"""Stage 3a: Natural Terrain Branch - DEM Skyline and Horizon Profile Matching."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from geolocator.config import AppConfig, get_config
from geolocator.providers.dem import DEMProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.skyline_extractor import SkylineExtractor
from geolocator.pipeline.geo_utils import haversine_distance_km

logger = logging.getLogger("geolocator.pipeline.stage3_terrain")


class Stage3Terrain:
    """Stage 3a: Fits photographic horizon profiles against synthetic DEM skylines."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        dem_provider: Optional[DEMProvider] = None,
        skyline_extractor: Optional[SkylineExtractor] = None,
    ):
        self.config = config or get_config()
        cache_dir = getattr(self.config, "storage", None) and self.config.storage.cache_dir or ".geo-cache"
        self.dem = dem_provider or DEMProvider(cache_dir=cache_dir, offline_mode=self.config.offline_mode)
        self.extractor = skyline_extractor or SkylineExtractor(target_width=120)

    @staticmethod
    def _compute_profile_correlation(photo_profile: np.ndarray, dem_profile: np.ndarray) -> float:
        """Compute Normalized Cross-Correlation (NCC) between photo skyline and DEM skyline."""
        if len(photo_profile) != len(dem_profile):
            # Resample DEM profile to match photo profile dimension
            xp = np.linspace(0, 1, len(dem_profile))
            x_new = np.linspace(0, 1, len(photo_profile))
            dem_resampled = np.interp(x_new, xp, dem_profile)
        else:
            dem_resampled = dem_profile

        # Normalize DEM profile
        std_dem = float(np.std(dem_resampled))
        if std_dem < 1e-4:
            return 0.0
        norm_dem = (dem_resampled - np.mean(dem_resampled)) / std_dem

        # Photo profile is assumed to be mean 0, std 1
        std_photo = float(np.std(photo_profile))
        if std_photo < 1e-4:
            return 0.0
        norm_photo = (photo_profile - np.mean(photo_profile)) / std_photo

        ncc = float(np.mean(norm_photo * norm_dem))
        return float(np.clip(ncc, -1.0, 1.0))

    def search_viewpoint(
        self,
        photo_profile: np.ndarray,
        center_lat: float,
        center_lon: float,
        radius_km: float = 15.0,
        coarse_step_km: float = 3.0,
        fine_step_km: float = 0.5,
        heading_hint: Optional[float] = None,
        hfov: float = 60.0,
        range_m: float = 35000.0,
    ) -> Dict[str, Any]:
        """Search viewpoint inside search radius that maximizes skyline profile correlation."""
        lat_rad = math.radians(center_lat)
        deg_lat_km = 111.32
        deg_lon_km = 111.32 * math.cos(lat_rad)

        # 1. Coarse search grid
        r_deg_lat = radius_km / deg_lat_km
        r_deg_lon = radius_km / max(1.0, deg_lon_km)

        coarse_step_lat = coarse_step_km / deg_lat_km
        coarse_step_lon = coarse_step_km / max(1.0, deg_lon_km)

        lats = np.arange(center_lat - r_deg_lat, center_lat + r_deg_lat + 1e-5, coarse_step_lat)
        lons = np.arange(center_lon - r_deg_lon, center_lon + r_deg_lon + 1e-5, coarse_step_lon)

        # Heading sweep
        if heading_hint is not None:
            headings = [heading_hint - 20.0, heading_hint, heading_hint + 20.0]
        else:
            headings = np.arange(0.0, 360.0, 30.0).tolist()

        best_score = -2.0
        best_candidate: Optional[Dict[str, Any]] = None
        candidates_scored: List[Dict[str, Any]] = []

        logger.info("Coarse grid search: %d x %d positions, %d headings", len(lats), len(lons), len(headings))

        for c_lat in lats:
            for c_lon in lons:
                dist = haversine_distance_km(center_lat, center_lon, c_lat, c_lon)
                if dist > radius_km:
                    continue

                for h in headings:
                    profile_res = self.dem.compute_skyline_profile(
                        lat=c_lat,
                        lon=c_lon,
                        heading=float(h),
                        hfov=hfov,
                        range_m=range_m,
                        samples=len(photo_profile),
                    )
                    dem_angles = np.array(profile_res["skyline_angles"], dtype=np.float32)
                    score = self._compute_profile_correlation(photo_profile, dem_angles)

                    entry = {
                        "lat": float(c_lat),
                        "lon": float(c_lon),
                        "heading": float(h),
                        "score": score,
                        "distance_from_center_km": dist,
                    }
                    candidates_scored.append(entry)

                    if score > best_score:
                        best_score = score
                        best_candidate = entry

        # 2. Fine search around best coarse candidate
        if best_candidate and best_candidate["score"] > -0.5:
            ref_lat = best_candidate["lat"]
            ref_lon = best_candidate["lon"]
            ref_heading = best_candidate["heading"]

            fine_step_lat = fine_step_km / deg_lat_km
            fine_step_lon = fine_step_km / max(1.0, deg_lon_km)

            fine_lats = np.arange(ref_lat - coarse_step_lat, ref_lat + coarse_step_lat + 1e-5, fine_step_lat)
            fine_lons = np.arange(ref_lon - coarse_step_lon, ref_lon + coarse_step_lon + 1e-5, fine_step_lon)
            fine_headings = np.arange(ref_heading - 15.0, ref_heading + 15.0 + 1e-5, 5.0)

            for f_lat in fine_lats:
                for f_lon in fine_lons:
                    for f_h in fine_headings:
                        profile_res = self.dem.compute_skyline_profile(
                            lat=float(f_lat),
                            lon=float(f_lon),
                            heading=float(f_h),
                            hfov=hfov,
                            range_m=range_m,
                            samples=len(photo_profile),
                        )
                        dem_angles = np.array(profile_res["skyline_angles"], dtype=np.float32)
                        score = self._compute_profile_correlation(photo_profile, dem_angles)

                        if score > best_score:
                            best_score = score
                            best_candidate = {
                                "lat": float(f_lat),
                                "lon": float(f_lon),
                                "heading": float(f_h % 360.0),
                                "score": score,
                                "distance_from_center_km": haversine_distance_km(center_lat, center_lon, f_lat, f_lon),
                            }

        # Calibrated error radius based on skyline correlation score
        if best_score > 0.85:
            calibrated_radius_km = 1.5
            tier = "T2"
        elif best_score > 0.65:
            calibrated_radius_km = 4.5
            tier = "T2"
        elif best_score > 0.45:
            calibrated_radius_km = 15.0
            tier = "T3"
        else:
            calibrated_radius_km = 45.0
            tier = "T4"

        return {
            "best_viewpoint": best_candidate,
            "best_score": round(best_score, 4),
            "calibrated_radius_km": calibrated_radius_km,
            "confidence_tier": tier,
            "total_candidates_evaluated": len(candidates_scored),
        }

    def process(
        self,
        job_dir: Path,
        board: CandidateBoard,
        working_image_path: Optional[Path] = None,
        search_center: Optional[Tuple[float, float]] = None,
        photo_skyline_override: Optional[List[float]] = None,
        radius_km: float = 15.0,
    ) -> Tuple[Dict[str, Any], CandidateBoard]:
        """Execute Stage 3a Natural Terrain Branch and write artifacts/candidates to board."""
        job_dir = Path(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)

        # 1. Extract photo skyline
        overlay_path = job_dir / "skyline_overlay.png"
        if photo_skyline_override is not None:
            photo_profile = np.array(photo_skyline_override, dtype=np.float32)
            skyline_info = {
                "samples": len(photo_skyline_override),
                "normalized_profile": photo_skyline_override,
                "overlay_saved": False,
            }
        else:
            if working_image_path is None:
                working_image_path = job_dir / "working_1024.jpg"
                if not working_image_path.exists():
                    working_image_path = board.photo_path
            skyline_info = self.extractor.extract_from_image(working_image_path, save_overlay_path=overlay_path)
            photo_profile = np.array(skyline_info["normalized_profile"], dtype=np.float32)

        # Save skyline JSON artifact
        skyline_json_path = job_dir / "skyline_extracted.json"
        skyline_json_path.write_text(json.dumps(skyline_info, indent=2), encoding="utf-8")

        # 2. Determine search center from Stage 2 bounding box if not provided
        if search_center is None:
            bboxes = board.data.get("search_bboxes", [])
            if bboxes:
                top_bbox = bboxes[0]
                search_center = (float(top_bbox["center"][0]), float(top_bbox["center"][1]))
            else:
                # Default fallback from board top candidate
                ranked = board.rank()
                if ranked and ranked[0].get("lat") is not None:
                    search_center = (float(ranked[0]["lat"]), float(ranked[0]["lon"]))
                else:
                    search_center = (35.4983, 138.7688)  # Mount Fuji scenic default

        c_lat, c_lon = search_center
        logger.info("Executing terrain skyline search around (%.4f, %.4f), radius=%.1f km", c_lat, c_lon, radius_km)

        # 3. Fit viewpoint
        fit_results = self.search_viewpoint(
            photo_profile=photo_profile,
            center_lat=c_lat,
            center_lon=c_lon,
            radius_km=radius_km,
        )

        best_vp = fit_results["best_viewpoint"]
        if best_vp:
            v_lat = best_vp["lat"]
            v_lon = best_vp["lon"]
            v_heading = best_vp["heading"]
            score = fit_results["best_score"]

            cand_name = f"Terrain Ridgeline Viewpoint ({v_lat:.4f}, {v_lon:.4f})"
            board.add_candidate(
                name=cand_name,
                level="point",
                lat=v_lat,
                lon=v_lon,
                prior=max(0.01, min(1.0, (score + 1.0) / 2.0)),
                metadata={
                    "heading": v_heading,
                    "fit_score": score,
                    "radius_km": fit_results["calibrated_radius_km"],
                    "tier": fit_results["confidence_tier"],
                },
            )

            cid_skyline = board.add_clue(
                text=f"Terrain skyline cross-correlation fit at heading {v_heading:.1f}° (NCC={score:.3f})",
                kind="terrain",
                status="computed",
            )

            # Likelihood ratio weight
            weight = math.exp(min(3.5, max(-3.5, score * 3.5)))
            board.add_evidence(
                clue_id=cid_skyline,
                candidate_weights={cand_name: weight},
                rationale=f"Photographic skyline matched against AWS Terrarium DEM (NCC={score:.3f})",
                artifact_path=str(job_dir / "terrain_results.json"),
            )

        board.data["stages_run"].append("stage3_terrain")
        board.save()

        summary = {
            "search_center": [c_lat, c_lon],
            "radius_km": radius_km,
            "skyline_samples": len(photo_profile),
            "skyline_overlay_path": str(overlay_path) if overlay_path.exists() else None,
            "fit_results": fit_results,
        }

        (job_dir / "terrain_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary, board
