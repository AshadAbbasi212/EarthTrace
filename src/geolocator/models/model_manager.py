"""ModelManager: Sequential on-demand model loading with strict 8GB/4GB VRAM safety."""
from __future__ import annotations

import asyncio
import gc
import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, Optional, Tuple

import torch

from geolocator.config import AppConfig, get_config

logger = logging.getLogger("geolocator.models.manager")


class ModelManager:
    """Manages GPU/CPU model lifecycles ensuring only one neural network resides in VRAM at a time."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()
        self.current_model_name: Optional[str] = None
        self.current_model: Optional[Any] = None
        self._model_loaders: Dict[str, Callable[[], Any]] = {}
        self._cpu_cache: Dict[str, Any] = {}

    def register_loader(self, name: str, loader: Callable[[], Any]) -> None:
        """Register a lazy loader function for a named model."""
        self._model_loaders[name] = loader

    @staticmethod
    def get_vram_info() -> Dict[str, float]:
        """Return VRAM statistics in megabytes (MB)."""
        if not torch.cuda.is_available():
            return {"allocated_mb": 0.0, "reserved_mb": 0.0, "total_mb": 0.0, "free_mb": 0.0}

        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info()
            allocated = torch.cuda.memory_allocated() / (1024 * 1024)
            reserved = torch.cuda.memory_reserved() / (1024 * 1024)
            return {
                "allocated_mb": round(allocated, 2),
                "reserved_mb": round(reserved, 2),
                "total_mb": round(total_bytes / (1024 * 1024), 2),
                "free_mb": round(free_bytes / (1024 * 1024), 2),
            }
        except Exception as e:
            logger.warning("Failed to query VRAM info: %s", e)
            return {"allocated_mb": 0.0, "reserved_mb": 0.0, "total_mb": 0.0, "free_mb": 0.0}

    def unload(self) -> None:
        """Forcefully unload current model from GPU and purge VRAM."""
        with self._lock:
            if self.current_model is not None:
                vram_before = self.get_vram_info()
                model_name = self.current_model_name
                logger.info("Unloading model '%s' (VRAM before: %s MB allocated)", model_name, vram_before["allocated_mb"])
                
                # Move to cpu and cache in CPU RAM to eliminate disk reload overhead
                try:
                    if hasattr(self.current_model, "to"):
                        self.current_model.to("cpu")
                    self._cpu_cache[model_name] = self.current_model
                except Exception as e:
                    logger.debug("Failed to cache model %s on cpu: %s", model_name, e)

                self.current_model = None
                self.current_model_name = None

                # Thorough garbage collection and cache flushing
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()

                vram_after = self.get_vram_info()
                logger.info("Unloaded '%s' (VRAM after: %s MB allocated, %s MB free)", model_name, vram_after["allocated_mb"], vram_after["free_mb"])

    def load(self, name: str) -> Any:
        """Load requested model onto device, unloading any active model if different."""
        with self._lock:
            if self.current_model_name == name and self.current_model is not None:
                return self.current_model

            if self.current_model is not None:
                self.unload()

            vram_before = self.get_vram_info()
            logger.info("Loading model '%s' (VRAM before: %s MB allocated, %s MB free)...", name, vram_before["allocated_mb"], vram_before["free_mb"])
            
            t0 = time.time()
            try:
                if name in self._cpu_cache:
                    model = self._cpu_cache[name]
                    target_device = "cuda" if torch.cuda.is_available() else "cpu"
                    try:
                        if hasattr(model, "to"):
                            model.to(target_device)
                        if hasattr(model, "device"):
                            model.device = target_device
                    except Exception as dev_err:
                        logger.warning("CUDA error moving '%s' to %s (%s). Retrying on CPU.", name, target_device, dev_err)
                        if hasattr(model, "to"):
                            model.to("cpu")
                        if hasattr(model, "device"):
                            model.device = "cpu"
                elif name in self._model_loaders:
                    try:
                        model = self._model_loaders[name]()
                    except Exception as load_err:
                        if ("cuda" in str(load_err).lower() or isinstance(load_err, torch.cuda.OutOfMemoryError)) and torch.cuda.is_available():
                            logger.warning("CUDA error loading '%s' (%s). Retrying loader on CPU fallback...", name, load_err)
                            orig_avail = torch.cuda.is_available
                            try:
                                torch.cuda.is_available = lambda: False
                                model = self._model_loaders[name]()
                            finally:
                                torch.cuda.is_available = orig_avail
                        else:
                            raise
                else:
                    raise ValueError(f"No loader registered for model '{name}'. Registered: {list(self._model_loaders.keys())}")

                self.current_model = model
                self.current_model_name = name
                elapsed = time.time() - t0
                
                vram_after = self.get_vram_info()
                logger.info("Loaded model '%s' in %.2fs (VRAM: %s MB allocated, %s MB free)", 
                            name, elapsed, vram_after["allocated_mb"], vram_after["free_mb"])
                return model
            except torch.cuda.OutOfMemoryError as oom:
                logger.error("CUDA OOM while loading '%s': %s", name, oom)
                self.unload()
                raise
            except Exception as exc:
                logger.error("Error loading model '%s': %s", name, exc)
                self.unload()
                raise

    @contextmanager
    def acquire(self, name: str, keep_loaded: bool = False) -> Generator[Any, None, None]:
        """Synchronous context manager to use a model with automatic cleanup."""
        model = self.load(name)
        try:
            yield model
        finally:
            if not keep_loaded:
                self.unload()

    async def acquire_async(self, name: str, keep_loaded: bool = False):
        """Asynchronous context manager acquiring the GPU lock."""
        class AsyncModelContext:
            def __init__(self, manager: ModelManager, model_name: str, keep: bool):
                self.manager = manager
                self.model_name = model_name
                self.keep = keep
                self.model = None

            async def __aenter__(self):
                await self.manager._async_lock.acquire()
                # Run sync loading in thread pool to not block async loop
                loop = asyncio.get_running_loop()
                self.model = await loop.run_in_executor(None, self.manager.load, self.model_name)
                return self.model

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                try:
                    if not self.keep:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, self.manager.unload)
                finally:
                    self.manager._async_lock.release()

        return AsyncModelContext(self, name, keep_loaded)


_manager_instance: Optional[ModelManager] = None


def get_model_manager(config: Optional[AppConfig] = None) -> ModelManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ModelManager(config)
    return _manager_instance
