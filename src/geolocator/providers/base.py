"""Base provider interface with robust disk caching, offline mode, and polite retries."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("geolocator.providers.base")

DEFAULT_USER_AGENT = "GlobalPhotoGeolocator/1.0 (Open-Source Research; contact: local-deploy)"


class BaseProvider:
    """Base class for all keyless data providers."""

    def __init__(
        self,
        name: str,
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 30.0,
    ):
        self.name = name
        self.cache_dir = Path(cache_dir) / name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode or (os.getenv("OFFLINE_MODE", "").lower() in ("true", "1", "yes"))
        self.user_agent = user_agent
        self.timeout = timeout

    def _hash_key(self, key_data: Any) -> str:
        """Create a deterministic SHA-256 hash string for caching."""
        if isinstance(key_data, dict):
            serialized = json.dumps(key_data, sort_keys=True)
        elif isinstance(key_data, str):
            serialized = key_data
        else:
            serialized = str(key_data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]

    def get_cache_path(self, key: str, ext: str = ".json") -> Path:
        """Return the filesystem path for a cache key."""
        filename = f"{key}{ext}" if not key.endswith(ext) else key
        return self.cache_dir / filename

    def is_cached(self, key: str, ext: str = ".json") -> bool:
        """Check if an item exists in the disk cache."""
        path = self.get_cache_path(key, ext)
        return path.exists() and path.stat().st_size > 0

    def read_cached_bytes(self, key: str, ext: str = ".bin") -> Optional[bytes]:
        """Read cached raw bytes if present."""
        path = self.get_cache_path(key, ext)
        if path.exists():
            try:
                return path.read_bytes()
            except OSError as e:
                logger.warning("[%s] Failed to read cache file %s: %s", self.name, path, e)
        return None

    def write_cached_bytes(self, key: str, data: bytes, ext: str = ".bin") -> Path:
        """Write raw bytes to disk cache."""
        path = self.get_cache_path(key, ext)
        try:
            path.write_bytes(data)
        except OSError as e:
            logger.warning("[%s] Failed to write cache file %s: %s", self.name, path, e)
        return path

    def read_cached_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Read cached JSON if present."""
        raw = self.read_cached_bytes(key, ext=".json")
        if raw is not None:
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning("[%s] Malformed cached JSON for key %s: %s", self.name, key, e)
        return None

    def write_cached_json(self, key: str, data: Any) -> Path:
        """Write JSON data to disk cache."""
        serialized = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return self.write_cached_bytes(key, serialized, ext=".json")

    def fetch_bytes(
        self,
        url: str,
        cache_key: Optional[str] = None,
        ext: str = ".bin",
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        backoff_sec: float = 1.5,
    ) -> bytes:
        """Fetch bytes from remote URL with caching and retries, respecting offline mode."""
        key = cache_key or self._hash_key(url)

        # Check cache first
        cached = self.read_cached_bytes(key, ext=ext)
        if cached is not None:
            return cached

        if self.offline_mode:
            raise FileNotFoundError(f"[{self.name}] Running in offline mode and item not cached: {url}")

        req_headers = {"User-Agent": self.user_agent}
        if headers:
            req_headers.update(headers)

        last_error = None
        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = resp.read()
                    self.write_cached_bytes(key, data, ext=ext)
                    return data
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
                last_error = e
                logger.warning("[%s] Attempt %d/%d failed for %s: %s", self.name, attempt, retries, url, e)
                if attempt < retries:
                    time.sleep(backoff_sec * attempt)

        raise RuntimeError(f"[{self.name}] All {retries} fetch attempts failed for {url}: {last_error}")

    def fetch_json(
        self,
        url: str,
        cache_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        backoff_sec: float = 1.5,
    ) -> Any:
        """Fetch JSON payload with caching and retries."""
        key = cache_key or self._hash_key(url)
        cached = self.read_cached_json(key)
        if cached is not None:
            return cached

        raw = self.fetch_bytes(url, cache_key=key, ext=".json", headers=headers, retries=retries, backoff_sec=backoff_sec)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"[{self.name}] Response from {url} is not valid JSON: {e}")
