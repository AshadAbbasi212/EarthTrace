"""Master Pipeline Orchestrator: Chains Stages 0 through 5 with candidate board tracking."""
from __future__ import annotations

import json
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
from geolocator.providers.online_copilot import OnlineCoPilotProvider
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
        self.online_copilot = OnlineCoPilotProvider()

    def run(
        self,
        photo_path: str | Path,
        job_dir: Optional[str | Path] = None,
        user_hint_text: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        api_key: Optional[str] = None,
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
        if intake_summary.get("exif_gps") or intake_summary.get("gps_wgs84") or board.data.get("fast_path_gps"):
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

        # Optional Online Co-Pilot (e.g. free Gemini API key)
        working_img = job_dir / "working_1024.jpg"
        if not working_img.exists():
            working_img = photo_path
        if self.online_copilot.is_enabled(api_key):
            report_progress("Online Co-Pilot: Multimodal Cloud Vision Analysis", 35)
            try:
                self.online_copilot.process(
                    job_dir=job_dir,
                    board=board,
                    working_image_path=working_img,
                    user_hint=user_hint_text,
                    api_key=api_key,
                )
            except Exception as e:
                logger.warning("[orchestrator] Online co-pilot error: %s (continuing offline)", e)

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
        terrain_obj = getattr(clues_res, "terrain", None)
        relief = getattr(terrain_obj, "relief", "flat") if terrain_obj else "flat"
        horizon_vis = getattr(terrain_obj, "horizon_visible", False) if terrain_obj else False
        hint_lower = (user_hint_text or "").lower()

        # 3a. Terrain skyline branch: only runs when genuine mountain/hill relief is present
        has_mountain_hint = any(k in hint_lower for k in ("mountain", "ridge", "alps", "peak", "himalaya", "valley", "hiking", "pass", "summit", "cliff", "hill"))
        built_env = getattr(clues_res, "built_environment", None)
        architecture = getattr(built_env, "architecture", "unknown") if built_env else "unknown"
        is_urban_building = (
            scene_type in ("urban", "building", "indoor")
            or architecture in ("historic_monument", "institutional_brick", "urban_modern")
        )

        is_mountainous_relief = (
            (scene_type in ("mountain", "wilderness") or (relief in ("mountainous", "hilly") and not is_urban_building) or (horizon_vis and not is_urban_building))
            or has_mountain_hint
        )
        if is_mountainous_relief:
            self.stage3_terrain.process(job_dir, board)
        else:
            reason_msg = (
                "Scene classified as urban architecture / built structures; building rooflines excluded from DEM terrain correlation."
                if is_urban_building
                else f"Scene classified as flat or urban terrain (scene='{scene_type}', relief='{relief}') without prominent ridgeline; skyline search bypassed."
            )
            logger.info("[orchestrator] %s", reason_msg)
            board.data["stages_run"].append("stage3_terrain")
            board.data["terrain_evaluation"] = {
                "status": "not_applicable",
                "reason": reason_msg,
            }
            summary = {
                "status": "not_applicable",
                "reason": reason_msg,
                "fit_results": {"best_score": 0.0, "best_viewpoint": None},
            }
            (job_dir / "terrain_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            board.save()

        # 3b. Built & infrastructure branch runs for urban, buildings, landmarks, roads, bridges
        has_built_cues = (
            any(b in scene_type for b in ("urban", "building", "landmark", "rural_road", "farmland", "bridge", "coast", "other"))
            or any(k in hint_lower for k in ("bridge", "railway", "train", "crossing", "road", "building", "street", "city", "station"))
            or any(cand.get("level") == "point" for cand in board.data.get("candidates", {}).values())
        )
        if has_built_cues:
            self.stage3_built.process(job_dir, board)
        else:
            board.data["stages_run"].append("stage3_built")
            summary = {
                "status": "not_applicable",
                "reason": "Natural terrain without built structures or linear infrastructure; corridor search bypassed.",
                "match_results": {"status": "not_applicable"},
            }
            (job_dir / "osm_corridor_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            board.save()

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
