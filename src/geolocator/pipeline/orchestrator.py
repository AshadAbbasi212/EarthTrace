"""Master Pipeline Orchestrator: Chains Stages 0 through 5 with candidate board tracking."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from geolocator.config import AppConfig, get_config
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.stage0_intake import Stage0Intake
from geolocator.pipeline.stage1_clues import Stage1Clues
from geolocator.pipeline.stage2_prior import Stage2Prior
from geolocator.pipeline.stage3_terrain import Stage3Terrain
from geolocator.pipeline.stage3_built import Stage3Built
from geolocator.pipeline.stage4_verification import Stage4Verification
from geolocator.report.generator import ReportGenerator

logger = logging.getLogger("geolocator.pipeline.orchestrator")


class PipelineOrchestrator:
    """Orchestrates end-to-end geolocation pipeline execution from photo intake to final decision report."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.stage0 = Stage0Intake()
        self.stage1 = Stage1Clues()
        self.stage2 = Stage2Prior(self.config)
        self.stage3_terrain = Stage3Terrain(self.config)
        self.stage3_built = Stage3Built(self.config)
        self.stage4 = Stage4Verification(self.config)
        self.stage5 = ReportGenerator()

    def run(
        self,
        photo_path: str | Path,
        job_dir: Optional[str | Path] = None,
        user_hint_text: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Dict[str, Any]:
        """Execute complete geolocation workflow."""
        photo_path = Path(photo_path)
        if not photo_path.exists():
            raise FileNotFoundError(f"Input photo '{photo_path}' does not exist")

        jobs_root = Path(getattr(self.config, "storage", None) and self.config.storage.jobs_dir or "jobs")
        if job_dir is None:
            import uuid
            job_dir = jobs_root / f"job_{uuid.uuid4().hex[:12]}"
        job_dir = Path(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)

        def report_progress(step_name: str, pct: int):
            logger.info("Pipeline progress [%d%%]: %s", pct, step_name)
            if progress_callback:
                try:
                    progress_callback(step_name, pct)
                except Exception:
                    pass

        # ----------------------------------------------------
        # Stage 0: Intake
        # ----------------------------------------------------
        report_progress("Stage 0: Image Intake & EXIF Analysis", 10)
        intake_summary, board = self.stage0.process(photo_path, job_dir)

        # Check for EXIF GPS fast-path
        if intake_summary.get("exif_gps") is not None:
            logger.info("EXIF GPS detected, executing fast-path verification...")
            report_progress("EXIF GPS fast-path: Verifying location", 80)
            self.stage4.process(job_dir, board)
            report_progress("Stage 5: Compiling Final Report", 100)
            return self.stage5.process(job_dir, board)

        # ----------------------------------------------------
        # Stage 1: Clue Extraction & Visual Perception
        # ----------------------------------------------------
        report_progress("Stage 1: Extracting Visual Clues & OCR", 25)
        clues_res, board = self.stage1.process(job_dir, board, user_hint_text=user_hint_text)

        # ----------------------------------------------------
        # Stage 2: Global Prior & Biome Candidate Bounding Boxes
        # ----------------------------------------------------
        report_progress("Stage 2: Evaluating Global Prior & Biomes", 45)
        prior_summary, board = self.stage2.process(job_dir, board)

        # ----------------------------------------------------
        # Stage 3: Candidate Generation (Routed by Scene Type)
        # ----------------------------------------------------
        report_progress("Stage 3: Candidate Generation & Matching", 65)
        scene_type = getattr(clues_res, "scene_type", "other")
        
        # Terrain branch runs if mountain, desert, hill, natural terrain or horizon is detected
        if any(t in scene_type for t in ("mountain", "desert", "valley", "lake_river", "rural_road")) or board.data.get("search_bboxes"):
            self.stage3_terrain.process(job_dir, board)

        # Built & infrastructure branch runs for roads, bridges, urban, or rural
        if any(b in scene_type for b in ("urban", "rural_road", "farmland", "bridge", "coast", "other")):
            self.stage3_built.process(job_dir, board)

        # ----------------------------------------------------
        # Stage 4: Verification & Camera Pose Resection
        # ----------------------------------------------------
        report_progress("Stage 4: Satellite & Street Verification", 85)
        self.stage4.process(job_dir, board)

        # ----------------------------------------------------
        # Stage 5: Final Decision Engine & Report Generation
        # ----------------------------------------------------
        report_progress("Stage 5: Final Decision & Multi-Format Report", 100)
        report_data = self.stage5.process(job_dir, board)

        return report_data
