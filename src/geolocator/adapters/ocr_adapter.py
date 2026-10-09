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
        self._easy_engine = None

    def _get_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()
        return self._engine

    def _get_easy_engine(self):
        if self._easy_engine is None:
            try:
                import torch
                import easyocr
                use_gpu = bool(torch.cuda.is_available())
                logger.info("[ocr] Initializing EasyOCR multilingual reader (GPU: %s)...", use_gpu)
                self._easy_engine = easyocr.Reader(['ar', 'en'], gpu=use_gpu, download_enabled=False)
            except Exception as e:
                logger.warning("[ocr] EasyOCR initialization: %s", e)
                self._easy_engine = False
        return self._easy_engine if self._easy_engine else None

    def unload(self) -> None:
        """Unload EasyOCR from GPU and free memory for subsequent pipeline stages."""
        if self._easy_engine is not None and self._easy_engine is not False:
            try:
                logger.info("[ocr] Unloading EasyOCR engine from memory/GPU...")
                del self._easy_engine
            except Exception:
                pass
            self._easy_engine = None
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def read_text(self, image_input: str | Path | Image.Image, min_conf: float = 0.3) -> List[Dict[str, Any]]:
        """Run OCR and return list of detected text snippets with bounding boxes."""
        try:
            if isinstance(image_input, (str, Path)):
                im = Image.open(image_input).convert("RGB")
            else:
                im = image_input.convert("RGB")

            parsed = []
            seen_texts = set()

            # 1. RapidOCR pass (fast Latin and Chinese)
            try:
                engine = self._get_engine()
                img_bgr = np.array(im)[:, :, ::-1]
                results, _ = engine(img_bgr)
                if results:
                    for box, text, conf in results:
                        confidence = float(conf)
                        clean = str(text).strip()
                        if confidence >= min_conf and clean and clean not in seen_texts:
                            seen_texts.add(clean)
                            xs = [p[0] for p in box]
                            ys = [p[1] for p in box]
                            parsed.append({
                                "text": clean,
                                "confidence": round(confidence, 3),
                                "box": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
                                "engine": "rapidocr",
                            })
            except Exception as e:
                logger.debug("[ocr] RapidOCR pass error: %s", e)

            # 2. EasyOCR Multilingual / Arabic / Urdu pass
            easy_engine = self._get_easy_engine()
            if easy_engine is not None:
                try:
                    easy_im = im.copy()
                    if max(easy_im.size) > 1024:
                        easy_im.thumbnail((1024, 1024), Image.LANCZOS)
                    img_np = np.array(easy_im)
                    easy_res = easy_engine.readtext(img_np, canvas_size=1024, mag_ratio=1.0)
                    for bbox, text, conf in easy_res:
                        clean = str(text).strip()
                        confidence = float(conf)
                        # Retain detected multilingual words
                        if clean and len(clean) >= 2 and confidence >= 0.03:
                            if clean not in seen_texts:
                                seen_texts.add(clean)
                                xs = [p[0] for p in bbox]
                                ys = [p[1] for p in bbox]
                                parsed.append({
                                    "text": clean,
                                    "confidence": round(max(confidence, 0.75 if any(ord(c) > 127 for c in clean) else confidence), 3),
                                    "box": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
                                    "engine": "easyocr",
                                })
                except Exception as e:
                    logger.debug("[ocr] EasyOCR pass error: %s", e)

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
