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
        if std_dem < 0.15:  # Flat elevation angle profile across FOV
            return 0.0
        norm_dem = (dem_resampled - np.mean(dem_resampled)) / std_dem

        # Normalize photo profile and DEM angles to same dimension
        if len(photo_profile) != len(dem_resampled):
            norm_photo_raw = np.interp(
                np.linspace(0, 1, len(dem_resampled)),
                np.linspace(0, 1, len(photo_profile)),
                photo_profile
            )
        else:
            norm_photo_raw = photo_profile

        std_photo = float(np.std(norm_photo_raw))
        if std_photo < 0.015:  # Flat photo horizon
            return 0.0
        norm_photo = (norm_photo_raw - np.mean(norm_photo_raw)) / std_photo

        ncc = float(np.mean(norm_photo * norm_dem))
        return float(np.clip(ncc, -1.0, 1.0))

    def search_viewpoint(
        self,
        photo_profile: np.ndarray,
        center_lat: float,
        center_lon: float,
        radius_km: float = 12.0,
        coarse_step_km: float = 10.0,
        fine_step_km: float = 2.0,
        heading_hint: Optional[float] = None,
        hfov: float = 60.0,
        range_m: float = 25000.0,
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

        # Fast 8 cardinal headings (every 45 degrees) or focused heading sweep
        if heading_hint is not None:
            headings = [heading_hint - 25.0, heading_hint, heading_hint + 25.0]
        else:
            headings = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]

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
                        samples=36,
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
                            samples=min(60, len(photo_profile)),
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

        # 1. Extract photo skyline and ALWAYS save visual overlay
        overlay_path = job_dir / "skyline_overlay.png"
        if photo_skyline_override is not None:
            photo_profile = np.array(photo_skyline_override, dtype=np.float32)
            skyline_info = {
                "samples": len(photo_skyline_override),
                "normalized_profile": photo_skyline_override,
                "raw_elevations": photo_skyline_override,
                "std_elevation": float(np.std(photo_skyline_override)),
                "is_non_flat": float(np.std(photo_skyline_override)) >= 0.02,
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

        # Check if the extracted horizon has actual undulating mountain/hill relief
        std_elev = skyline_info.get("std_elevation", float(np.std(photo_profile)))
        is_non_flat = skyline_info.get("is_non_flat", std_elev >= 0.02)

        # Check if the extracted horizon is a man-made building roofline or scene is urban architecture
        is_roofline = skyline_info.get("is_manmade_roofline", False)
        clues_data = board.data.get("clues_data", {})
        scene_type = clues_data.get("scene_type", "")
        arch = clues_data.get("built_environment", {}).get("architecture", "")
        user_hint = (board.data.get("user_hints", {}).get("raw_hint") or "").lower()
        has_mountain_hint = any(k in user_hint for k in ("mountain", "ridge", "alps", "peak", "himalaya", "valley", "hiking", "pass", "summit", "cliff", "hill"))

        if (is_roofline or scene_type in ("urban", "building", "indoor") or arch in ("historic_monument", "institutional_brick", "urban_modern")) and not has_mountain_hint:
            reason_msg = (
                skyline_info.get("roofline_reason")
                or "Horizon contour identified as man-made architecture / building roofline; DEM natural terrain matching bypassed."
            )
            logger.info("[stage3_terrain] %s", reason_msg)
            board.data["stages_run"].append("stage3_terrain")
            board.data["terrain_evaluation"] = {
                "status": "not_applicable",
                "reason": reason_msg,
            }
            board.save()
            summary = {
                "status": "not_applicable",
                "reason": reason_msg,
                "skyline_overlay_path": None,
                "fit_results": {"best_score": 0.0, "best_viewpoint": None},
            }
            (job_dir / "terrain_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            return summary, board

        if not is_non_flat and std_elev < 0.015:
            logger.info("[stage3_terrain] Extracted skyline is flat (std=%.4f). Bypassing DEM search.", std_elev)
            board.data["stages_run"].append("stage3_terrain")
            board.data["terrain_evaluation"] = {
                "status": "not_applicable",
                "reason": f"Extracted horizon profile is flat (relief variation std={std_elev:.3f}); natural mountain terrain skyline bypassed.",
            }
            board.save()
            summary = {
                "status": "not_applicable",
                "reason": f"Extracted horizon profile is flat (relief variation std={std_elev:.3f}); natural mountain terrain skyline bypassed.",
                "skyline_overlay_path": None,
                "fit_results": {"best_score": 0.0, "best_viewpoint": None},
            }
            (job_dir / "terrain_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            return summary, board

        # 2. Determine candidate search centers from Stage 2 bounding boxes or board rank
        candidate_centers: List[Tuple[float, float]] = []
        if search_center is not None:
            candidate_centers.append(search_center)
        else:
            bboxes = board.data.get("search_bboxes", [])
            for b in bboxes[:3]:
                if "center" in b:
                    candidate_centers.append((float(b["center"][0]), float(b["center"][1])))
            if not candidate_centers:
                ranked = board.rank()
                for cand in ranked[:3]:
                    if cand.get("lat") is not None and cand.get("lon") is not None:
                        candidate_centers.append((float(cand["lat"]), float(cand["lon"])))
            if not candidate_centers:
                candidate_centers.append((35.4983, 138.7688))

        # 3. Fit viewpoint across candidate centers, keeping the strongest physical correlation
        best_overall_fit = None
        best_overall_score = -2.0
        chosen_center = candidate_centers[0]

        for c_idx, (c_lat, c_lon) in enumerate(candidate_centers):
            logger.info("Executing terrain skyline search around (%.4f, %.4f), radius=%.1f km (center %d/%d)", c_lat, c_lon, radius_km, c_idx + 1, len(candidate_centers))
            fit_res = self.search_viewpoint(
                photo_profile=photo_profile,
                center_lat=c_lat,
                center_lon=c_lon,
                radius_km=radius_km,
            )
            score_i = fit_res.get("best_score", -2.0)
            if score_i > best_overall_score:
                best_overall_score = score_i
                best_overall_fit = fit_res
                chosen_center = (c_lat, c_lon)

            # If an exceptionally strong viewpoint correlation is confirmed, stop early
            if best_overall_score >= 0.65:
                break

        fit_results = best_overall_fit if best_overall_fit is not None else {
            "best_viewpoint": None,
            "best_score": -1.0,
            "calibrated_radius_km": 45.0,
            "confidence_tier": "T4",
            "total_candidates_evaluated": 0,
        }
        c_lat, c_lon = chosen_center

        best_vp = fit_results.get("best_viewpoint")
        score = fit_results.get("best_score", -1.0)

        # Calibrated DEM viewpoint promotion threshold:
        # Require strong physical correlation (NCC >= 0.72) to promote a point viewpoint candidate.
        # Moderate correlations (0.45 - 0.71) are recorded as supporting evidence without overriding locations.
        if best_vp and score >= 0.72:
            v_lat = best_vp["lat"]
            v_lon = best_vp["lon"]
            v_heading = best_vp["heading"]

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
        elif best_vp and score >= 0.45:
            # Supporting clue only; do not fabricate a point candidate that hijacks predictions
            board.add_clue(
                text=f"Terrain ridgeline curvature consistent with regional DEM (NCC={score:.3f}, unverified viewpoint)",
                kind="terrain",
                status="computed",
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
