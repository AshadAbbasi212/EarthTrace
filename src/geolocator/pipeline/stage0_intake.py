"""Stage 0: Intake - Image validation, hashing, EXIF parsing, and preparation of working copies."""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

from geolocator.adapters import extract_exif, generate_edge_crops, create_resized_copy
from geolocator.pipeline.board import CandidateBoard

logger = logging.getLogger("geolocator.pipeline.stage0")

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


class Stage0Intake:
    """Handles intake validation, format conversion, hashing, EXIF extraction, and working copies."""

    def __init__(self, max_size_mb: float = 25.0):
        self.max_size_mb = max_size_mb

    def process(
        self,
        input_image_path: str | Path,
        job_dir: str | Path,
        board: Optional[CandidateBoard] = None,
    ) -> Tuple[Dict[str, Any], CandidateBoard]:
        """Validate photo, extract metadata, prepare crops, and initialize board."""
        src_path = Path(input_image_path)
        job_path = Path(job_dir)
        job_path.mkdir(parents=True, exist_ok=True)

        if not src_path.exists():
            raise FileNotFoundError(f"Input image not found: {src_path}")

        # Size check
        size_mb = src_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise ValueError(f"Image size {size_mb:.1f}MB exceeds limit of {self.max_size_mb}MB")

        # Decode validation
        try:
            im = Image.open(src_path)
            im.verify()
            # Reopen after verify
            im = Image.open(src_path).convert("RGB")
            orig_size = list(im.size)
        except Exception as e:
            raise ValueError(f"File is not a valid decodable image: {e}")

        # Compute SHA-256
        sha256 = hashlib.sha256(src_path.read_bytes()).hexdigest()

        # Copy original into job dir (keep original untouched)
        job_original = job_path / f"original{src_path.suffix.lower()}"
        if src_path != job_original:
            shutil.copy2(src_path, job_original)

        # Working copies (1024px, 512px)
        copy_1024 = create_resized_copy(job_original, job_path / "working_1024.jpg", max_dim=1024)
        copy_512 = create_resized_copy(job_original, job_path / "working_512.jpg", max_dim=512)

        # Edge crops (4 edges + 4 corners)
        edge_crops = generate_edge_crops(job_original, job_path / "edges")

        # Extract EXIF metadata
        try:
            exif_data = extract_exif(job_original)
        except Exception as e:
            logger.warning("[stage0] EXIF extraction error: %s", e)
            exif_data = {"file": str(job_original), "size": orig_size}

        # Initialize or update candidate board
        active_board = board or CandidateBoard(photo_path=job_original, board_path=job_path / "board.json")
        active_board.data["image_hash"] = sha256
        active_board.data["image_size"] = orig_size
        active_board.data["exif"] = exif_data

        # Check for GPS fast path
        gps = exif_data.get("gps_wgs84")
        if gps and len(gps) == 2:
            lat, lon = gps
            logger.info("[stage0] Found EXIF GPS coordinates: %s, %s (fast-path candidate)", lat, lon)
            active_board.data["fast_path_gps"] = [lat, lon]
            active_board.add_candidate(
                name="EXIF_GPS_Point",
                level="point",
                lat=lat,
                lon=lon,
                prior=10.0,
                metadata={"source": "exif_gps", "altitude": exif_data.get("altitude_m")},
            )
            active_board.add_clue(
                text=f"EXIF GPS tagged at {lat:.5f}, {lon:.5f}",
                kind="exif_gps",
                status="read",
                source="stage0_exif",
                confidence=0.9,
            )

        intake_summary = {
            "image_path": str(job_original),
            "sha256": sha256,
            "dimensions": orig_size,
            "size_mb": round(size_mb, 2),
            "has_exif": bool(exif_data.get("Make") or exif_data.get("DateTimeOriginal") or gps),
            "gps_wgs84": gps,
            "exif_gps": gps,
            "focal_35mm": exif_data.get("focal_35mm"),
            "fov": exif_data.get("fov_4x3_long_short"),
            "working_1024": str(copy_1024),
            "working_512": str(copy_512),
            "edge_crops_count": len(edge_crops),
        }

        # Save intake.json
        (job_path / "intake.json").write_text(json.dumps(intake_summary, indent=2), encoding="utf-8")
        active_board.mark_stage_run("stage0_intake")
        active_board.save(job_path / "board.json")

        return intake_summary, active_board
