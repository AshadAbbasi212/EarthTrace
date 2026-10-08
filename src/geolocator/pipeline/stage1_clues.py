"""Stage 1: Clue Extraction - Visual perception, local OCR, tabular lookups, and hint parsing."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from geolocator.adapters import (
    get_ocr,
    lookup_plate,
    lookup_driving_side,
    lookup_calling_code,
    lookup_territory,
    detect_script,
    detect_tld,
    detect_calling_code,
    extract_candidate_place_phrases,
)
from geolocator.providers.nominatim import NominatimProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.hint_parser import HintParser
from geolocator.pipeline.schema import ClueExtractionResult, TextSignItem, RegionGuessItem

logger = logging.getLogger("geolocator.pipeline.stage1")


class Stage1Clues:
    """Orchestrates Stage 1 clue extraction from images, OCR, lookup tables, and user hints."""

    def __init__(self, nominatim: Optional[NominatimProvider] = None):
        self.ocr = get_ocr()
        self.hint_parser = HintParser()
        self.nominatim = nominatim or NominatimProvider()

    def process(
        self,
        job_dir: str | Path,
        board: CandidateBoard,
        user_hint_text: Optional[str] = None,
        vlm_override: Optional[ClueExtractionResult] = None,
    ) -> Tuple[ClueExtractionResult, CandidateBoard]:
        """Execute Stage 1 clue extraction and update the candidate board."""
        job_path = Path(job_dir)
        working_image_path = job_path / "working_1024.jpg"
        if not working_image_path.exists():
            working_image_path = Path(board.photo_path)

        # 1. OCR Extraction (Full Image + Edge Crops)
        ocr_snippets: List[Dict[str, Any]] = []
        try:
            ocr_snippets.extend(self.ocr.read_text(working_image_path, min_conf=0.4))
            
            # Also check edge crops if available
            edges_dir = job_path / "edges"
            if edges_dir.exists():
                for crop_path in edges_dir.glob("*.jpg"):
                    crop_snippets = self.ocr.read_text(crop_path, min_conf=0.5)
                    for snip in crop_snippets:
                        snip["file_ref"] = str(crop_path.relative_to(job_path))
                        ocr_snippets.append(snip)
        except Exception as e:
            logger.warning("[stage1] OCR pass encountered error: %s", e)

        # Record unique OCR text onto the board
        seen_texts = set()
        for snip in ocr_snippets:
            t = snip["text"]
            if t not in seen_texts and len(t) >= 2:
                seen_texts.add(t)
                clue_id = board.add_clue(
                    text=f"OCR text: '{t}'",
                    kind="text_sign",
                    status="read",
                    source="ocr",
                    confidence=snip.get("confidence", 0.8),
                    file_ref=snip.get("file_ref", "working_1024.jpg"),
                )

                # 1a. Plate lookup check (first 2 chars)
                if len(t) >= 2:
                    plate_hit = lookup_plate(t[:2])
                    if plate_hit:
                        board.add_clue(
                            text=f"License plate '{t[:2]}' matches {plate_hit.get('province')}, {plate_hit.get('city')}",
                            kind="plate",
                            status="read",
                            source="clues_table",
                            confidence=0.95,
                        )
                        cand_name = plate_hit.get("city") or plate_hit.get("province")
                        if cand_name:
                            board.add_candidate(cand_name, level="city", prior=5.0)

                # 1b. Non-Latin writing script detection (Cyrillic, Greek, Arabic, Hangul, Kana, etc.)
                script_hit = detect_script(t)
                if script_hit:
                    s_name = script_hit["script"]
                    cands = script_hit["candidate_countries"]
                    board.add_clue(
                        text=f"Non-Latin script '{s_name}' detected in sign: '{t}'",
                        kind="script",
                        status="read",
                        source="ocr_meta",
                        confidence=0.90,
                    )
                    for c_country in cands[:3]:
                        board.add_candidate(c_country, level="country", prior=4.5)

                # 1c. Country-code Top Level Domain detection (.de, .fr, .co.uk, .com.br, etc.)
                tld_hit = detect_tld(t)
                if tld_hit:
                    tld_country = tld_hit["country"]
                    tld_token = tld_hit["matched_token"]
                    board.add_clue(
                        text=f"Web domain '{tld_token}' points to {tld_country}",
                        kind="tld",
                        status="read",
                        source="ocr_meta",
                        confidence=0.98,
                    )
                    board.add_candidate(tld_country, level="country", prior=8.0)

                # 1d. International dialing code detection (+XX, 00XX)
                calling_hit = detect_calling_code(t)
                if calling_hit:
                    code_country = calling_hit["country"]
                    if code_country:
                        board.add_clue(
                            text=f"Phone dialing prefix +{calling_hit['code']} indicates {code_country}",
                            kind="calling_code",
                            status="read",
                            source="ocr_meta",
                            confidence=0.92,
                        )
                        board.add_candidate(code_country, level="country", prior=7.0)

        # 1e. Autonomous Place-Name & Landmark Geocoding via Nominatim
        # Collect candidate place phrases across all detected text
        all_place_phrases = []
        for snip in ocr_snippets:
            all_place_phrases.extend(extract_candidate_place_phrases(snip["text"]))
        unique_phrases = list(dict.fromkeys(all_place_phrases))[:3]  # Polite limit of 3 lookups

        for phrase in unique_phrases:
            try:
                nom_results = self.nominatim.search(phrase, limit=1)
                if nom_results:
                    hit = nom_results[0]
                    p_lat = float(hit["lat"])
                    p_lon = float(hit["lon"])
                    display_name = hit.get("display_name", phrase)
                    raw_bbox = hit.get("boundingbox", [p_lat - 0.05, p_lat + 0.05, p_lon - 0.05, p_lon + 0.05])
                    bbox = [float(raw_bbox[0]), float(raw_bbox[2]), float(raw_bbox[1]), float(raw_bbox[3])]

                    p_clue_id = board.add_clue(
                        text=f"Sign text '{phrase}' geocoded to {display_name}",
                        kind="place_sign",
                        status="observed",
                        source="nominatim_geocoding",
                        confidence=0.92,
                    )
                    cand_name = f"Geocoded Sign '{phrase}': {display_name[:40]}"
                    board.add_candidate(
                        name=cand_name,
                        level="point",
                        prior=9.0,
                        bbox=bbox,
                        lat=p_lat,
                        lon=p_lon,
                    )
                    board.add_evidence(
                        clue_id=p_clue_id,
                        candidate_weights={cand_name: 50.0},
                        rationale="Autonomous sign text geocoding via OpenStreetMap Nominatim",
                    )
                    logger.info("[stage1] Successfully geocoded sign '%s' -> (%f, %f) %s", phrase, p_lat, p_lon, display_name)
            except Exception as e:
                logger.debug("[stage1] Geocoding lookup skipped for '%s': %s", phrase, e)

        # 2. Parse User Hints
        if user_hint_text and user_hint_text.strip():
            parsed_hints = self.hint_parser.parse(user_hint_text)
            board.data["user_hints"] = parsed_hints
            
            for country in parsed_hints.get("countries", []):
                clue_id = board.add_clue(
                    text=f"User stated location is in {country}",
                    kind="user_hint_country",
                    status="inferred",
                    source="user_hint",
                    confidence=0.85,
                )
                board.add_candidate(country, level="country", prior=4.0)

            for continent in parsed_hints.get("continents", []):
                board.add_clue(
                    text=f"User stated continent is {continent}",
                    kind="user_hint_continent",
                    status="inferred",
                    source="user_hint",
                    confidence=0.8,
                )

            if parsed_hints.get("season"):
                board.add_clue(
                    text=f"User hinted season: {parsed_hints['season']}",
                    kind="user_hint_season",
                    status="inferred",
                    source="user_hint",
                    confidence=0.75,
                )

        # 3. Visual Clue Extraction (VLM / Schema Validation)
        if vlm_override:
            clues_result = vlm_override
        else:
            clues_result = self._extract_visual_clues_heuristic(working_image_path, ocr_snippets)

        # Merge extracted cues onto board
        board.data["visual_cues"] = clues_result.model_dump()
        board.add_clue(
            text=f"Scene classified as: {clues_result.scene_type}",
            kind="scene_type",
            status="observed",
            source="vlm",
            confidence=0.8,
        )

        if clues_result.climate_cues.aridity != "unknown":
            board.add_clue(
                text=f"Aridity observed: {clues_result.climate_cues.aridity}",
                kind="aridity",
                status="observed",
                source="vlm",
                confidence=0.75,
            )

        if clues_result.climate_cues.snow:
            board.add_clue(
                text="Snow / ice observed in frame",
                kind="snow_ice",
                status="observed",
                source="vlm",
                confidence=0.85,
            )

        for guess in clues_result.region_guesses:
            cand_name = guess.place
            clue_id = board.add_clue(
                text=f"Visual guess: {cand_name} ({guess.reason})",
                kind="vlm_region_guess",
                status="inferred",
                source="vlm",
                confidence=guess.confidence,
            )
            board.add_candidate(cand_name, level="country", prior=1.0 + 3.0 * guess.confidence)

        # Save clues.json
        (job_path / "clues.json").write_text(
            json.dumps(clues_result.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        board.mark_stage_run("stage1_clues")
        board.save(job_path / "board.json")

        return clues_result, board

    def _extract_visual_clues_heuristic(
        self,
        image_path: Path,
        ocr_snippets: List[Dict[str, Any]],
    ) -> ClueExtractionResult:
        """Robust algorithmic visual cue extraction and schema validation fallback."""
        im = Image.open(image_path).convert("RGB")
        W, H = im.size
        
        # Color distribution analysis
        import numpy as np
        arr = np.asarray(im, dtype=np.float32)
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

        green_ratio = float(np.mean((g > r * 1.05) & (g > b * 1.05)))
        blue_sky_ratio = float(np.mean((b > r * 1.15) & (b > g * 1.05)))
        sand_ratio = float(np.mean((r > 160) & (g > 140) & (b < 130) & (r > g) & (g > b)))
        snow_ratio = float(np.mean((r > 220) & (g > 220) & (b > 220)))

        scene_type = "other"
        aridity = "unknown"
        snow = snow_ratio > 0.15
        veg_density = "unknown"
        relief = "flat"

        if sand_ratio > 0.25:
            scene_type = "desert"
            aridity = "arid"
            veg_density = "sparse"
        elif snow:
            scene_type = "snow_ice"
            veg_density = "none"
        elif green_ratio > 0.25:
            scene_type = "forest" if green_ratio > 0.45 else "farmland"
            aridity = "humid"
            veg_density = "dense" if green_ratio > 0.45 else "moderate"
        elif len(ocr_snippets) >= 3:
            scene_type = "urban"
            veg_density = "sparse"
        else:
            scene_type = "rural_road"

        text_items = [
            TextSignItem(text=s["text"], script="latin")
            for s in ocr_snippets[:10]
        ]

        result = ClueExtractionResult(
            scene_type=scene_type,
            terrain={"relief": relief, "landforms": [], "rock_soil_color": "yellow_brown" if sand_ratio > 0.2 else "unknown", "horizon_visible": blue_sky_ratio > 0.1},
            vegetation={"type": "unknown", "density": veg_density, "notable_species": []},
            climate_cues={"season_guess": "unknown", "snow": snow, "aridity": aridity},
            built_environment={"road_markings": "unknown", "driving_side": "unknown", "utility_poles": "unknown", "architecture": "unknown", "vehicles": "unknown"},
            text_and_signs=text_items,
            sun_shadow={"shadows_visible": False, "time_of_day_guess": "unknown"},
            water={"type": "none", "notes": ""},
            region_guesses=[],
            distinctive_features=[],
            overall_confidence=0.6,
        )
        return result
