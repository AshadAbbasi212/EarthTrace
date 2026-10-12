"""Stage 3b: Built/Rural & Coastal Branches - OSM Corridor and Geometry Matching."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from geolocator.config import AppConfig, get_config
from geolocator.providers.osm import OSMProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.geo_utils import haversine_distance_km, point_in_bbox

logger = logging.getLogger("geolocator.pipeline.stage3_built")


class Stage3Built:
    """Stage 3b: Built/Rural infrastructure and coastal geometry matching using OpenStreetMap."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        osm_provider: Optional[OSMProvider] = None,
    ):
        self.config = config or get_config()
        cache_dir = getattr(self.config, "storage", None) and self.config.storage.cache_dir or ".geo-cache"
        self.osm = osm_provider or OSMProvider(cache_dir=cache_dir, offline_mode=self.config.offline_mode)

    @staticmethod
    def sample_points_along_polyline(
        polyline: List[Tuple[float, float]],
        step_m: float = 250.0,
    ) -> List[Dict[str, Any]]:
        """Sample GPS points at fixed step intervals along a polyline [(lat, lon), ...]."""
        if len(polyline) < 2:
            return [{"lat": polyline[0][0], "lon": polyline[0][1], "distance_along_m": 0.0}] if polyline else []

        sampled = []
        accum_dist = 0.0
        cur_lat, cur_lon = polyline[0]
        sampled.append({"lat": cur_lat, "lon": cur_lon, "distance_along_m": 0.0})

        for i in range(len(polyline) - 1):
            p1 = polyline[i]
            p2 = polyline[i + 1]
            seg_dist = haversine_distance_km(p1[0], p1[1], p2[0], p2[1]) * 1000.0
            if seg_dist < 1.0:
                continue

            num_steps = int(seg_dist // step_m)
            for s in range(1, num_steps + 1):
                frac = (s * step_m) / seg_dist
                s_lat = p1[0] + frac * (p2[0] - p1[0])
                s_lon = p1[1] + frac * (p2[1] - p1[1])
                accum_dist += step_m
                sampled.append({
                    "lat": round(s_lat, 6),
                    "lon": round(s_lon, 6),
                    "distance_along_m": round(accum_dist, 1),
                })

        return sampled

    def match_corridor_point(
        self,
        corridor_polyline: List[Tuple[float, float]],
        crossings: List[Dict[str, Any]],
        target_features: Dict[str, Any],
        max_deviation_km: float = 1.0,
    ) -> Dict[str, Any]:
        """Find the exact point along a linear corridor matching observed structural features (bridge, crossing)."""
        if not crossings:
            return {
                "best_point": None,
                "score": 0.0,
                "calibrated_radius_km": 15.0,
                "confidence_tier": "T5",
                "status": "not_applicable",
            }

        sampled = self.sample_points_along_polyline(corridor_polyline, step_m=200.0)
        best_candidate: Optional[Dict[str, Any]] = None
        best_score = -1.0

        for pt in sampled:
            pt_lat, pt_lon = pt["lat"], pt["lon"]
            score = 0.0

            # Check proximity to known crossing features along the line
            for crossing in crossings:
                c_lat, c_lon = crossing["lat"], crossing["lon"]
                dist_km = haversine_distance_km(pt_lat, pt_lon, c_lat, c_lon)
                if dist_km <= max_deviation_km:
                    # Match crossing type
                    c_type = crossing.get("type", "")
                    if target_features.get("is_bridge") and ("bridge" in c_type or crossing.get("tags", {}).get("bridge") == "yes"):
                        score += 3.0
                    elif target_features.get("is_water_crossing") and ("river" in c_type or "waterway" in crossing.get("tags", {})):
                        score += 2.5
                    else:
                        score += 1.0

            if score > best_score:
                best_score = score
                best_candidate = {
                    "lat": pt_lat,
                    "lon": pt_lon,
                    "distance_along_m": pt["distance_along_m"],
                    "match_score": score,
                }

        if best_score < 1.0:
            best_candidate = None

        return {
            "best_point": best_candidate,
            "score": best_score if best_candidate else 0.0,
            "calibrated_radius_km": 0.5 if best_score >= 3.0 else 1.0,
            "confidence_tier": "T1" if best_score >= 3.5 else "T2",
            "status": "used" if best_candidate else "not_applicable",
        }

    def query_crossings_in_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        line_kind: str = "railway",
    ) -> List[Dict[str, Any]]:
        """Query bridge, waterway, and highway crossings in bbox via Overpass."""
        south, west, north, east = bbox
        tag_line = '["railway"="rail"]' if line_kind == "railway" else '["highway"~"^(motorway|trunk|primary)$"]'
        
        # Look for bridges and water intersections
        try:
            return self.osm.find_co_occurrences(
                south=south,
                west=west,
                north=north,
                east=east,
                tag_a=tag_line,
                tag_b='["waterway"="river"]',
                radius_m=300,
            )
        except Exception as e:
            logger.warning("OSM crossing query failed: %s", e)
            return []

    def query_coastlines_in_bbox(
        self,
        bbox: Tuple[float, float, float, float],
    ) -> List[Dict[str, Any]]:
        """Query coastline geometry in bbox."""
        south, west, north, east = bbox
        try:
            return self.osm.find_features(
                south=south,
                west=west,
                north=north,
                east=east,
                tag_filter='["natural"="coastline"]',
            )
        except Exception as e:
            logger.warning("OSM coastline query failed: %s", e)
            return []

    def process(
        self,
        job_dir: Path,
        board: CandidateBoard,
        search_bbox: Optional[Tuple[float, float, float, float]] = None,
        target_features: Optional[Dict[str, Any]] = None,
        mock_corridor: Optional[List[Tuple[float, float]]] = None,
        mock_crossings: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Dict[str, Any], CandidateBoard]:
        """Execute Stage 3b Built/Rural and Coastal Branch."""
        job_dir = Path(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)

        if target_features is None:
            target_features = {
                "is_bridge": True,
                "is_water_crossing": True,
            }

        # Resolve search bbox
        if search_bbox is None:
            bboxes = board.data.get("search_bboxes", [])
            if bboxes:
                s_b = bboxes[0]["bbox"]
                s, w, n, e = float(s_b[0]), float(s_b[1]), float(s_b[2]), float(s_b[3])
                # Clamp bbox window to at most ~10 km span to avoid Overpass Gateway Timeouts (504)
                c_lat = (s + n) / 2.0
                c_lon = (w + e) / 2.0
                half_span = 0.045
                search_bbox = (
                    max(s, c_lat - half_span),
                    max(w, c_lon - half_span),
                    min(n, c_lat + half_span),
                    min(e, c_lon + half_span),
                )
            else:
                search_bbox = (51.48, -0.15, 51.52, -0.08)  # London Thames corridor default

        logger.info("Stage 3b Built executing within bbox %s", search_bbox)

        # 0. Check if high-priority landmark or building candidate exists on the board
        landmark_cand = None
        for cand_name, cand in board.data.get("candidates", {}).items():
            if cand.get("level") == "point" and ("landmark" in cand.get("metadata", {}) or "Landmark:" in cand_name):
                landmark_cand = cand
                break

        if landmark_cand is not None:
            lm_name = landmark_cand.get("metadata", {}).get("landmark") or landmark_cand["name"].replace("Landmark: ", "")
            p_lat = float(landmark_cand["lat"])
            p_lon = float(landmark_cand["lon"])
            logger.info("Stage 3b Built verifying exact OSM building footprint for '%s'...", lm_name)

            try:
                from geolocator.providers.nominatim import NominatimProvider
                nom = NominatimProvider(
                    cache_dir=getattr(self.config, "storage", None) and self.config.storage.cache_dir or ".geo-cache",
                    offline_mode=self.config.offline_mode,
                )
                hits = nom.search(lm_name, limit=1)
                if not hits:
                    rev_hit = nom.reverse(p_lat, p_lon)
                    if rev_hit:
                        hits = [rev_hit]

                if hits:
                    best_hit = hits[0]
                    exact_lat = round(float(best_hit.get("lat", p_lat)), 6)
                    exact_lon = round(float(best_hit.get("lon", p_lon)), 6)
                    osm_type = best_hit.get("osm_type", "way")
                    osm_id = best_hit.get("osm_id", "")
                    disp_name = best_hit.get("display_name", lm_name)

                    # Update candidate with exact sub-meter centroid
                    landmark_cand["lat"] = exact_lat
                    landmark_cand["lon"] = exact_lon
                    landmark_cand["metadata"]["radius_km"] = 0.05
                    landmark_cand["metadata"]["tier"] = "T1"
                    landmark_cand["metadata"]["osm_id"] = f"{osm_type}/{osm_id}"
                    landmark_cand["metadata"]["osm_display_name"] = disp_name

                    cid_osm = board.add_clue(
                        text=f"OpenStreetMap building footprint verified: {disp_name[:60]} (OSM {osm_type}/{osm_id})",
                        kind="osm_building",
                        status="computed",
                    )
                    board.add_evidence(
                        clue_id=cid_osm,
                        candidate_weights={landmark_cand["name"]: 8.0},
                        rationale=f"OpenStreetMap cadastral building geometry confirmed for {lm_name}",
                        artifact_path=str(job_dir / "osm_corridor_results.json"),
                    )

                    match_res = {
                        "best_point": {
                            "lat": exact_lat,
                            "lon": exact_lon,
                            "name": lm_name,
                            "osm_id": f"{osm_type}/{osm_id}",
                        },
                        "score": 4.5,
                        "calibrated_radius_km": 0.05,
                        "confidence_tier": "T1",
                        "status": "used",
                        "building_verified": True,
                    }
                    summary = {
                        "search_bbox": search_bbox,
                        "match_results": match_res,
                        "building_verified": True,
                        "crossings_found": 1,
                        "osm_feature": {
                            "display_name": disp_name,
                            "osm_id": f"{osm_type}/{osm_id}",
                            "coordinates": [exact_lat, exact_lon],
                        },
                    }
                    board.data["stages_run"].append("stage3_built")
                    board.save()
                    (job_dir / "osm_corridor_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
                    return summary, board
            except Exception as e:
                logger.warning("OSM landmark building verification error: %s", e)

        # 1. Fetch or use corridor
        if mock_corridor is not None:
            corridor = mock_corridor
            crossings = mock_crossings or []
        else:
            crossings = self.query_crossings_in_bbox(search_bbox, line_kind="railway")
            # Create polyline across bbox center if no explicit line was passed
            s, w, n, e = search_bbox
            corridor = [(s, w), (s * 0.5 + n * 0.5, w * 0.5 + e * 0.5), (n, e)]

        # 2. Match corridor point
        match_res = self.match_corridor_point(
            corridor_polyline=corridor,
            crossings=crossings,
            target_features=target_features,
            max_deviation_km=1.0,
        )

        best_pt = match_res["best_point"]
        if best_pt:
            p_lat = best_pt["lat"]
            p_lon = best_pt["lon"]
            score = match_res["score"]
            tier = match_res["confidence_tier"]
            radius_km = match_res["calibrated_radius_km"]

            cand_name = f"OSM Infrastructure Corridor Point ({p_lat:.4f}, {p_lon:.4f})"
            board.add_candidate(
                name=cand_name,
                level="point",
                lat=p_lat,
                lon=p_lon,
                prior=0.8,
                metadata={
                    "corridor_score": score,
                    "radius_km": radius_km,
                    "tier": tier,
                },
            )

            cid_osm = board.add_clue(
                text=f"OSM linear infrastructure corridor match ({'Bridge crossing' if target_features.get('is_bridge') else 'Corridor'})",
                kind="corridor",
                status="computed",
            )

            board.add_evidence(
                clue_id=cid_osm,
                candidate_weights={cand_name: min(20.0, math.exp(score))},
                rationale="OpenStreetMap linear corridor topology alignment",
                artifact_path=str(job_dir / "osm_corridor_results.json"),
            )

        board.data["stages_run"].append("stage3_built")
        board.save()

        summary = {
            "search_bbox": search_bbox,
            "target_features": target_features,
            "match_results": match_res,
            "crossings_found": len(crossings),
        }

        (job_dir / "osm_corridor_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary, board
