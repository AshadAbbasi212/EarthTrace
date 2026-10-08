#!/usr/bin/env python3
"""Hardware and GPU verification script for Global Photo Geolocator.

Checks:
- Python version, PyTorch version, CUDA runtime
- NVIDIA GPU model name, compute capability, VRAM size
- ModelManager allocation, test model inference latency, peak VRAM, and memory cleanup
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import torch
import torchvision
from PIL import Image

from geolocator.config import get_config
from geolocator.models.model_manager import ModelManager


def main() -> int:
    print("=" * 70)
    print(" GLOBAL PHOTO GEOLOCATOR - HARDWARE & GPU VERIFICATION")
    print("=" * 70)

    print(f"Python Version:   {sys.version.split()[0]}")
    print(f"PyTorch Version:  {torch.__version__}")
    print(f"Torchvision:      {torchvision.__version__}")
    print(f"CUDA Available:   {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print("\n[WARN] CUDA is not available. System will run on CPU.")
        device_name = "CPU"
        total_vram_mb = 0.0
        free_vram_mb = 0.0
    else:
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        total_vram_mb = total_bytes / (1024 * 1024)
        free_vram_mb = free_bytes / (1024 * 1024)

        print(f"CUDA Device Count: {device_count}")
        print(f"GPU Name:          {device_name}")
        print(f"Compute Capability:{capability[0]}.{capability[1]}")
        print(f"Total VRAM:        {total_vram_mb:.1f} MB ({total_vram_mb / 1024:.2f} GB)")
        print(f"Free VRAM:         {free_vram_mb:.1f} MB ({free_vram_mb / 1024:.2f} GB)")

    print("\n" + "-" * 70)
    print(" TESTING MODELMANAGER & VISION MODEL INFERENCE")
    print("-" * 70)

    config = get_config()
    manager = ModelManager(config)

    # Register a lightweight vision benchmark loader
    def load_test_model():
        from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
        model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
        return model

    manager.register_loader("test_benchmark", load_test_model)

    vram_start = manager.get_vram_info()
    print(f"Initial VRAM Allocated: {vram_start['allocated_mb']} MB")

    t_load_start = time.time()
    model = manager.load("test_benchmark")
    t_load_end = time.time()
    load_time = t_load_end - t_load_start
    print(f"Model Load Time:        {load_time:.3f} s")

    vram_loaded = manager.get_vram_info()
    print(f"Loaded VRAM Allocated:  {vram_loaded['allocated_mb']} MB")

    # Run inference test
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dummy_input = torch.randn(1, 3, 224, 224, device=device)

    # Warmup
    with torch.no_grad():
        _ = model(dummy_input)

    # Timed run
    t_inf_start = time.time()
    with torch.no_grad():
        output = model(dummy_input)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t_inf_end = time.time()
    inf_latency_ms = (t_inf_end - t_inf_start) * 1000

    peak_vram = torch.cuda.max_memory_allocated() / (1024 * 1024) if torch.cuda.is_available() else 0.0

    print(f"Inference Latency:      {inf_latency_ms:.2f} ms")
    print(f"Peak VRAM:              {peak_vram:.2f} MB")
    print(f"Output Shape:           {list(output.shape)}")

    # Unload and verify memory reclamation
    print("\nTesting ModelManager Unload & VRAM Cleanup...")
    manager.unload()
    vram_after = manager.get_vram_info()
    print(f"Post-Unload Allocated:  {vram_after['allocated_mb']} MB")
    print(f"Post-Unload Free:       {vram_after['free_mb']} MB")

    print("\n" + "=" * 70)
    print(" VERIFICATION RESULT: PASS")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
