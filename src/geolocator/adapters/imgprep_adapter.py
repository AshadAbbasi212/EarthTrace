"""Adapter wrapping vendored imgprep.py for crops, zoom, and image preparations."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image

VENDOR_SCRIPTS = Path(__file__).resolve().parent.parent.parent.parent / "vendor" / "geo-sleuth" / "skills" / "geo-sleuth" / "scripts"
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

import imgprep


def generate_edge_crops(image_path: str | Path, out_dir: str | Path) -> Dict[str, Path]:
    """Generate zoomed crops for the 4 edges and 4 corners."""
    src = Path(image_path)
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)

    im = Image.open(src).convert("RGB")
    W, H = im.size
    
    crops = {
        "top": (0, 0, W, int(H * 0.35)),
        "bottom": (0, int(H * 0.50), W, H),
        "left": (0, 0, int(W * 0.35), H),
        "right": (int(W * 0.65), 0, W, H),
        "top_left": (0, 0, int(W * 0.45), int(H * 0.45)),
        "top_right": (int(W * 0.55), 0, W, int(H * 0.45)),
        "bottom_left": (0, int(H * 0.50), int(W * 0.50), H),
        "bottom_right": (int(W * 0.50), int(H * 0.50), W, H),
    }

    result = {}
    for name, box in crops.items():
        cropped = im.crop(box)
        target = dest / f"edge_{name}.jpg"
        cropped.save(target, quality=90)
        result[name] = target

    return result


def create_resized_copy(image_path: str | Path, out_path: str | Path, max_dim: int = 1024) -> Path:
    """Create a resized working copy constrained by maximum dimension."""
    im = Image.open(image_path).convert("RGB")
    im.thumbnail((max_dim, max_dim), Image.LANCZOS)
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    im.save(target, quality=92)
    return target
