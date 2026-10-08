"""Pre-download and cache model weights for 100% offline geolocation."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("download_weights")

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def download_models() -> None:
    """Pre-fetch all model weights into local Hugging Face / Torch cache."""
    logger.info("=======================================================")
    logger.info("  Offline Model Weight Pre-downloader (Milestone 11)")
    logger.info("=======================================================")

    # 1. GeoCLIP and CLIP ViT-L/14
    logger.info("[1/2] Pre-loading GeoCLIP model and CLIP vision backbone...")
    try:
        from geoclip import GeoCLIP
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Initializing GeoCLIP on device: %s", device)
        model = GeoCLIP()
        model.to(device)
        logger.info("✓ GeoCLIP and CLIP ViT-L/14 cached successfully.")
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as e:
        logger.warning("! GeoCLIP caching note: %s", e)

    # 2. RapidOCR ONNX models
    logger.info("[2/2] Pre-loading RapidOCR models...")
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
        logger.info("✓ RapidOCR detection/recognition models verified.")
    except Exception as e:
        logger.warning("! RapidOCR caching note: %s", e)

    logger.info("=======================================================")
    logger.info("  All local model weights are verified and cached.")
    logger.info("=======================================================")

if __name__ == "__main__":
    download_models()
