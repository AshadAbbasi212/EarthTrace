"""Local keyless OCR adapter using RapidOCR (ONNX runtime)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List
from PIL import Image
import numpy as np

logger = logging.getLogger("geolocator.adapters.ocr")


class LocalOCR:
    """Performs offline, keyless optical character recognition on image patches."""

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()
        return self._engine

    def read_text(self, image_input: str | Path | Image.Image, min_conf: float = 0.4) -> List[Dict[str, Any]]:
        """Run OCR and return list of detected text snippets with bounding boxes."""
        try:
            if isinstance(image_input, (str, Path)):
                im = Image.open(image_input).convert("RGB")
            else:
                im = image_input.convert("RGB")

            engine = self._get_engine()
            # RapidOCR takes BGR numpy array
            img_bgr = np.array(im)[:, :, ::-1]
            results, _ = engine(img_bgr)

            parsed = []
            if results:
                for box, text, conf in results:
                    confidence = float(conf)
                    if confidence >= min_conf and text.strip():
                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        parsed.append({
                            "text": str(text).strip(),
                            "confidence": round(confidence, 3),
                            "box": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
                        })
            return parsed
        except Exception as e:
            logger.warning("[ocr] OCR failed: %s", e)
            return []


# Module singleton
_ocr_instance = None


def get_ocr() -> LocalOCR:
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = LocalOCR()
    return _ocr_instance
