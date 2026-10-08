"""Adapter wrapping vendored exif.py without modifying vendored code."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# Ensure vendor scripts are accessible
VENDOR_SCRIPTS = Path(__file__).resolve().parent.parent.parent.parent / "vendor" / "geo-sleuth" / "skills" / "geo-sleuth" / "scripts"
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

import exif


def extract_exif(image_path: str | Path) -> Dict[str, Any]:
    """Extract metadata including GPS, timestamp, camera model, and focal length."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    return exif.read(path)
