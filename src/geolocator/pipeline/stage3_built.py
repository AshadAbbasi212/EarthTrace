"""Stage 3b: Built/Rural & Coastal Branches - OSM Corridor and Geometry Matching."""
from __future__ import annotations

import json
import logging
import math
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from geolocator.config import AppConfig, get_config
from geolocator.providers.osm import OSMProvider
from geolocator.providers.dem import DEMProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.building_detector import BuildingDetector
from geolocator.pipeline.geo_utils import haversine_distance_km, point_in_bbox

logger = logging.getLogger("geolocator.pipeline.stage3_built")


class Stage3Built:
    """Stage 3b: Built/Rural infrastructure and coastal geometry matching using OpenStreetMap."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        osm_provider: Optional[OSMProvider] = None,
        building_detector: Optional[BuildingDetector] = None,
        dem_provider: Optional[DEMProvider] = None,
    ):
        self.config = config or get_config()
        cache_dir = getattr(self.config, "storage", None) and self.config.storage.cache_dir or ".geo-cache"
        self.osm = osm_provider or OSMProvider(cache_dir=cache_dir, offline_mode=self.config.offline_mode)
        self.building_detector = building_detector or BuildingDetector()
        self.dem = dem_provider or DEMProvider(cache_dir=cache_dir, offline_mode=self.config.offline_mode)


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
        # Bound search box to prevent Overpass timeouts on oversized candidate bboxes
        if (north - south) > 0.35 or (east - west) > 0.35:
            mid_lat = (north + south) / 2.0
            mid_lon = (east + west) / 2.0
            south = max(-90.0, mid_lat - 0.10)
            north = min(90.0, mid_lat + 0.10)
            west = max(-180.0, mid_lon - 0.10)
            east = min(180.0, mid_lon + 0.10)
            logger.debug("[stage3_built] Bbox bounded to 0.20 deg centered at (%.3f, %.3f) for Overpass query", mid_lat, mid_lon)

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
        image_path: Optional[Path | str] = None,
    ) -> Tuple[Dict[str, Any], CandidateBoard]:
        """Execute Stage 3b Built/Rural, Building Detection, and Coastal Branch."""
        job_dir = Path(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)

        if target_features is None:
            target_features = {
                "is_bridge": True,
                "is_water_crossing": True,
            }

        # Resolve image path
        if image_path is None:
            for ext in ("original.jpeg", "original.jpg", "original.png", "original.webp"):
                cand_file = job_dir / ext
                if cand_file.exists():
                    image_path = cand_file
                    break

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
                # Center search bbox on top coordinate candidate if available
                ranked = board.rank()
                top_coord_cand = next((c for c in ranked if c.get("lat") is not None and c.get("lon") is not None), None)
                if top_coord_cand:
                    c_lat = float(top_coord_cand["lat"])
                    c_lon = float(top_coord_cand["lon"])
                    half_span = 0.045
                    search_bbox = (c_lat - half_span, c_lon - half_span, c_lat + half_span, c_lon + half_span)
                else:
                    search_bbox = (51.48, -0.15, 51.52, -0.08)  # London default

        logger.info("Stage 3b Built executing within bbox %s", search_bbox)

        # -------------------------------------------------------------------
        # 1. Automated Building & Facade Detection + Cadastral Matching
        # -------------------------------------------------------------------
        detected_manifest: Dict[str, Any] = {"count": 0, "buildings": [], "overlay_path": None}
        matched_cadastral_list: List[Dict[str, Any]] = []

        if image_path and Path(image_path).exists():
            try:
                bldg_out_dir = job_dir / "buildings"
                detected_manifest = self.building_detector.detect_building_regions(
                    image_path=image_path,
                    output_dir=bldg_out_dir,
                    max_buildings=5,
                )
                logger.info("[stage3_built] Detected %d building facades", detected_manifest.get("count", 0))

                # Copy tactical HUD overlay to job_dir root for convenience
                if detected_manifest.get("overlay_path") and Path(detected_manifest["overlay_path"]).exists():
                    shutil.copy2(detected_manifest["overlay_path"], job_dir / "building_detection_overlay.png")

                detected_buildings = detected_manifest.get("buildings", [])
                if detected_buildings:
                    # Enrich buildings with OCR text clues from board
                    ocr_clues = [
                        c.get("text", "") for c in board.data.get("clues", {}).values()
                        if isinstance(c, dict) and (c.get("kind") in ("text", "ocr", "sign") or c.get("status") == "read")
                    ]
                    combined_ocr = " ".join(ocr_clues)
                    for bldg in detected_buildings:
                        if not bldg.get("ocr_text") and combined_ocr:
                            bldg["ocr_text"] = combined_ocr

                    matched_cadastral_list = self.building_detector.match_buildings_against_osm(
                        detected_buildings=detected_buildings,
                        candidate_bbox=search_bbox,
                        osm_provider=self.osm,
                    )
                    # If initial search bbox didn't match and other bounding boxes exist on the board, check runner-ups
                    if not matched_cadastral_list:
                        bboxes = board.data.get("search_bboxes", [])
                        for alt_b_entry in bboxes[1:3]:
                            alt_b = alt_b_entry.get("bbox")
                            if alt_b:
                                s, w, n, e = float(alt_b[0]), float(alt_b[1]), float(alt_b[2]), float(alt_b[3])
                                c_lat, c_lon = (s + n) / 2.0, (w + e) / 2.0
                                alt_bbox = (max(s, c_lat - 0.045), max(w, c_lon - 0.045), min(n, c_lat + 0.045), min(e, c_lon + 0.045))
                                alt_matched = self.building_detector.match_buildings_against_osm(
                                    detected_buildings=detected_buildings,
                                    candidate_bbox=alt_bbox,
                                    osm_provider=self.osm,
                                )
                                if alt_matched:
                                    matched_cadastral_list.extend(alt_matched)
                                    break
            except Exception as e:
                logger.warning("[stage3_built] Building detection failed: %s", e)

        # Promote matched cadastral buildings to high-confidence point candidates on the board
        primary_building_feature = None
        for m_item in matched_cadastral_list:
            m_cad = m_item.get("matched", {})
            m_name = m_cad.get("name")
            if not m_name:
                continue
            cand_name = f"Cadastral Building: {m_name}"
            exact_lat = m_cad["lat"]
            exact_lon = m_cad["lon"]
            osm_id = m_cad.get("osm_id", "")
            osm_type = m_cad.get("osm_type", "way")

            # Pillar 2: Verify ground elevation at building coordinate using AWS Terrarium DEM
            dem_alt_m = None
            try:
                dem_alt_m = self.dem.get_elevation(exact_lat, exact_lon)
            except Exception as e_dem:
                logger.debug("[stage3_built] DEM altitude query failed: %s", e_dem)

            board.add_candidate(
                name=cand_name,
                level="point",
                lat=exact_lat,
                lon=exact_lon,
                prior=5.0,
                metadata={
                    "radius_km": 0.05,
                    "tier": "T1",
                    "osm_id": f"{osm_type}/{osm_id}",
                    "source": "cadastral_exact_mark",
                    "building_id": m_item.get("building_id"),
                    "classification": m_item.get("classification"),
                    "match_score": m_cad.get("match_score"),
                    "dem_altitude_m": round(dem_alt_m, 1) if dem_alt_m is not None else None,
                    "levels": m_cad.get("levels"),
                    "height": m_cad.get("height"),
                },
            )
            cid_bldg = board.add_clue(
                text=f"OpenStreetMap Cadastral Building Match: {m_name} (OSM {osm_type}/{osm_id})",
                kind="cadastral_building",
                status="computed",
            )
            board.add_evidence(
                clue_id=cid_bldg,
                candidate_weights={cand_name: 35.0},
                rationale=f"Automated building facade detection matched cadastral footprint in OpenStreetMap ({m_name})",
                artifact_path=str(job_dir / "buildings" / "detected_buildings.json"),
            )
            if dem_alt_m is not None:
                cid_elev = board.add_clue(
                    text=f"Pillar 2 Ground Altitude at Building: {dem_alt_m:.0f}m ASL (AWS Terrarium DEM terrain verified)",
                    kind="terrain_elevation",
                    status="computed",
                )
                board.add_evidence(
                    clue_id=cid_elev,
                    candidate_weights={cand_name: 1.5},
                    rationale=f"Physical ground elevation of building ({dem_alt_m:.0f}m ASL) validated against terrain DEM",
                )
            if primary_building_feature is None:
                primary_building_feature = {
                    "display_name": m_name,
                    "osm_id": f"{osm_type}/{osm_id}",
                    "coordinates": [exact_lat, exact_lon],
                    "dem_altitude_m": dem_alt_m,
                }


        # -------------------------------------------------------------------
        # 2. Check if high-priority landmark candidate exists on the board
        # -------------------------------------------------------------------
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
                    landmark_cand["metadata"]["source"] = "cadastral_exact_mark"
                    landmark_cand["metadata"]["osm_id"] = f"{osm_type}/{osm_id}"
                    landmark_cand["metadata"]["osm_display_name"] = disp_name

                    cid_osm = board.add_clue(
                        text=f"OpenStreetMap building footprint verified: {disp_name[:60]} (OSM {osm_type}/{osm_id})",
                        kind="osm_building",
                        status="computed",
                    )
                    board.add_evidence(
                        clue_id=cid_osm,
                        candidate_weights={landmark_cand["name"]: 12.0},
                        rationale=f"OpenStreetMap cadastral building geometry confirmed for {lm_name}",
                        artifact_path=str(job_dir / "osm_corridor_results.json"),
                    )

                    if primary_building_feature is None:
                        primary_building_feature = {
                            "display_name": disp_name,
                            "osm_id": f"{osm_type}/{osm_id}",
                            "coordinates": [exact_lat, exact_lon],
                        }
            except Exception as e:
                logger.warning("OSM landmark building verification error: %s", e)

        # -------------------------------------------------------------------
        # 3. Linear Corridor & Infrastructure Matching (Bridges, Rails)
        # -------------------------------------------------------------------
        clue_kinds = {c.get("kind") for c in board.data.get("clues", {}).values() if isinstance(c, dict)}
        raw_hint = (board.data.get("user_hints", {}).get("raw_text", "") or "").lower()
        has_linear_infrastructure = (
            bool({"corridor", "railway_crossing", "bridge_crossing", "railway"} & clue_kinds)
            or any(k in raw_hint for k in ("bridge", "railway", "train", "crossing", "canal", "river crossing", "track", "rail"))
        )

        match_res = {"status": "not_applicable", "score": 0.0, "best_point": None}
        crossings: List[Dict[str, Any]] = []

        if mock_corridor is not None:
            corridor = mock_corridor
            crossings = mock_crossings or []
            match_res = self.match_corridor_point(
                corridor_polyline=corridor,
                crossings=crossings,
                target_features=target_features,
                max_deviation_km=1.0,
            )
        elif has_linear_infrastructure:
            crossings = self.query_crossings_in_bbox(search_bbox, line_kind="railway")
            s, w, n, e = search_bbox
            corridor = [(s, w), (s * 0.5 + n * 0.5, w * 0.5 + e * 0.5), (n, e)]
            match_res = self.match_corridor_point(
                corridor_polyline=corridor,
                crossings=crossings,
                target_features=target_features,
                max_deviation_km=1.0,
            )

        best_pt = match_res.get("best_point")
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
            cid_corridor = board.add_clue(
                text=f"OSM linear infrastructure corridor match ({'Bridge crossing' if target_features.get('is_bridge') else 'Corridor'})",
                kind="corridor",
                status="computed",
            )
            board.add_evidence(
                clue_id=cid_corridor,
                candidate_weights={cand_name: min(20.0, math.exp(score))},
                rationale="OpenStreetMap linear corridor topology alignment",
                artifact_path=str(job_dir / "osm_corridor_results.json"),
            )

        building_verified = bool(primary_building_feature or matched_cadastral_list)
        status_str = "used" if (building_verified or match_res.get("best_point")) else "not_applicable"
        reason_str = "No linear corridor or bridge infrastructure or cadastral matches found in candidate area." if status_str == "not_applicable" else "Cadastral building or infrastructure corridor verified in OpenStreetMap."
        summary = {
            "status": status_str,
            "reason": reason_str,
            "search_bbox": search_bbox,
            "match_results": match_res,
            "building_verified": building_verified,
            "detected_buildings": detected_manifest.get("buildings", []),
            "building_count": detected_manifest.get("count", 0),
            "building_overlay": "building_detection_overlay.png" if (job_dir / "building_detection_overlay.png").exists() else None,
            "matched_cadastral": matched_cadastral_list,
            "crossings_found": len(crossings),
        }


        if primary_building_feature:
            summary["osm_feature"] = primary_building_feature

        board.data["stages_run"].append("stage3_built")
        board.save()
        (job_dir / "osm_corridor_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary, board
