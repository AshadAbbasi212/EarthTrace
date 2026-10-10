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
    GEO_PHONETIC_SYNONYMS,
    COMMON_STOP_WORDS,
)
from geolocator.providers.nominatim import NominatimProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.hint_parser import HintParser
from geolocator.pipeline.schema import ClueExtractionResult, TextSignItem, RegionGuessItem
from geolocator.pipeline.landmarks import LandmarkMatcher

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

        # 1. OCR Extraction (Full 1024px Image)
        ocr_snippets: List[Dict[str, Any]] = []
        try:
            ocr_snippets.extend(self.ocr.read_text(working_image_path, min_conf=0.25))
            
            # If text is detected, also check bottom crops where signs and plates reside
            edges_dir = job_path / "edges"
            if edges_dir.exists() and ocr_snippets:
                for crop_path in list(edges_dir.glob("*bottom*.jpg"))[:2]:
                    crop_snippets = self.ocr.read_text(crop_path, min_conf=0.25)
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

        # 1e. Autonomous Place-Name & Route Geocoding via Nominatim
        # Collect candidate place phrases across all detected text
        all_place_phrases = []
        for snip in ocr_snippets:
            all_place_phrases.extend(extract_candidate_place_phrases(snip["text"]))
        unique_phrases = list(dict.fromkeys(all_place_phrases))
        known_synonyms = set(GEO_PHONETIC_SYNONYMS.values())

        # Filter out obvious false positives and stop words
        filtered_phrases = []
        for p in unique_phrases:
            pl = p.strip().lower()
            if pl not in COMMON_STOP_WORDS and len(pl) >= 3:
                filtered_phrases.append(p)

        # Prioritize recognized gazetteer place names and route codes
        filtered_phrases.sort(key=lambda p: (0 if p in known_synonyms else 1, len(p) < 4))
        filtered_phrases = filtered_phrases[:6]  # Polite limit of 6 lookups

        for phrase in filtered_phrases:
            try:
                # Query with known synonym expansion if available
                query_str = GEO_PHONETIC_SYNONYMS.get(phrase, phrase)
                nom_results = self.nominatim.search(query_str, limit=1)
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
                    is_specific = any(w in display_name.lower() for w in ("road", "expressway", "highway", "point", "hill", "peak", "street", "building", "shrine", "station"))
                    cand_prior = 4.0 if is_specific else 2.0
                    weight = 6.0 if is_specific else 3.0

                    cand_name = f"Geocoded Sign '{phrase}': {display_name[:40]}"
                    board.add_candidate(
                        name=cand_name,
                        level="point",
                        prior=cand_prior,
                        bbox=bbox,
                        lat=p_lat,
                        lon=p_lon,
                        metadata={
                            "sign_text": phrase,
                            "display_name": display_name,
                            "tier": "T1" if is_specific else "T2",
                            "radius_km": 1.0 if is_specific else 15.0,
                        },
                    )
                    board.add_evidence(
                        clue_id=p_clue_id,
                        candidate_weights={cand_name: weight},
                        rationale=f"Autonomous place-name geocoding via OpenStreetMap Nominatim for '{phrase}'",
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
            clues_result = self._extract_visual_clues_heuristic(working_image_path, ocr_snippets, board=board)

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

        # Unload OCR from GPU so subsequent vision models have full VRAM headroom
        try:
            self.ocr.unload()
        except Exception as e:
            logger.debug("[stage1] Error unloading OCR: %s", e)

        return clues_result, board

    def _extract_visual_clues_heuristic(
        self,
        image_path: Path,
        ocr_snippets: List[Dict[str, Any]],
        board: Optional[CandidateBoard] = None,
    ) -> ClueExtractionResult:
        """Visual cue extraction using local CLIP zero-shot classification with algorithmic fallback."""
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

        scene_type = "urban" if len(ocr_snippets) >= 2 else "other"
        aridity = "unknown"
        snow = snow_ratio > 0.15
        veg_density = "unknown"
        relief = "flat"
        horizon_visible = False
        architecture = "unknown"
        region_guesses: List[RegionGuessItem] = []

        # Attempt high-accuracy local CLIP zero-shot scene & landmark classification
        try:
            import torch
            from transformers import CLIPProcessor, CLIPModel

            if not hasattr(self, "_cached_clip_model") or self._cached_clip_model is None:
                self._cached_clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14", local_files_only=True)
                self._cached_clip_proc = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14", local_files_only=True)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            clip_model = self._cached_clip_model.to(device)
            clip_proc = self._cached_clip_proc

            categories = [
                ("urban", "an urban brick institutional building or university campus or hospital block", "flat", False, "institutional_brick"),
                ("urban", "a photo of a modern city building or urban street architecture", "flat", False, "urban_modern"),
                ("urban", "a famous historical monument, fort, or architectural landmark", "flat", False, "historic_monument"),
                ("mountain", "a natural mountain range with rugged ridgelines and peaks", "mountainous", True, "none"),
                ("desert", "a flat arid desert landscape with sand or dry ground", "flat", True, "none"),
                ("farmland", "a rural forest or green agricultural countryside", "hilly", False, "rural"),
                ("rural_road", "an asphalt highway, motorway, or paved road", "flat", False, "road_infrastructure"),
                ("coast", "a coastal beach or body of water", "flat", True, "coastal"),
            ]

            prompts = [c[1] for c in categories]
            inputs = clip_proc(text=prompts, images=im, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                out = clip_model(**inputs)
                probs = out.logits_per_image.softmax(dim=-1).cpu().numpy()[0]

            top_idx = int(np.argmax(probs))
            top_cat = categories[top_idx]
            top_prob = float(probs[top_idx])
            logger.info("[stage1_clip] Classified scene as '%s' (conf=%.3f, relief=%s, horizon=%s)", top_cat[1], top_prob, top_cat[2], top_cat[3])

            if top_prob > 0.25:
                scene_type = top_cat[0]
                relief = top_cat[2]
                horizon_visible = top_cat[3]
                architecture = top_cat[4]

            # Direct Contour Skyline Analysis: Check image directly for genuine mountain/hill relief
            try:
                from geolocator.pipeline.skyline_extractor import SkylineExtractor
                extractor = SkylineExtractor(target_width=120)
                overlay_path = image_path.parent / "skyline_overlay.png"
                sky_info = extractor.extract_from_image(im, save_overlay_path=overlay_path)
                std_elev = sky_info.get("std_elevation", 0.0)
                if sky_info.get("is_non_flat", False) or std_elev >= 0.02:
                    relief = "mountainous" if std_elev >= 0.055 else "hilly"
                    horizon_visible = True
                    logger.info("[stage1_skyline] Direct contour inspection confirmed non-flat terrain (std=%.4f, relief=%s)", std_elev, relief)
            except Exception as e:
                logger.debug("[stage1_skyline] Direct contour check error: %s", e)

            # Informational landmark perception (Only if explicitly hinted or high confidence; never force-snap)
            user_requested_landmark = bool(board and board.data.get("user_hints", {}).get("landmarks"))
            if user_requested_landmark:
                lm_matcher = LandmarkMatcher()
                lm_res = lm_matcher.match(im, clip_model, clip_proc, device=device)
                if lm_res and lm_res.get("confidence", 0.0) >= 0.65:
                    l_name = lm_res["name"]
                    l_lat = lm_res["latitude"]
                    l_lon = lm_res["longitude"]
                    l_conf = lm_res["confidence"]
                    region_guesses.append(RegionGuessItem(place=l_name, confidence=l_conf, reason="User-requested landmark perception"))
                    cand_name = f"Landmark: {l_name}"
                    board.add_candidate(
                        name=cand_name,
                        level="point",
                        lat=l_lat,
                        lon=l_lon,
                        prior=2.0,
                        metadata={
                            "landmark": l_name,
                            "tier": "T2",
                            "radius_km": lm_res.get("radius_km", 2.0),
                            "source": "landmark_hint",
                        }
                    )

            # Offload CLIP model to CPU and purge VRAM for subsequent stages
            if clip_model is not None:
                clip_model.to("cpu")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            logger.warning("[stage1] CLIP zero-shot perception fallback to heuristic: %s", e)
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
            elif len(ocr_snippets) >= 2:
                scene_type = "urban"
                veg_density = "sparse"
            else:
                scene_type = "urban"

        text_items = [
            TextSignItem(text=s["text"], script="latin")
            for s in ocr_snippets[:10]
        ]

        result = ClueExtractionResult(
            scene_type=scene_type,
            terrain={"relief": relief, "landforms": [], "rock_soil_color": "yellow_brown" if sand_ratio > 0.2 else "unknown", "horizon_visible": horizon_visible},
            vegetation={"type": "unknown", "density": veg_density, "notable_species": []},
            climate_cues={"season_guess": "unknown", "snow": snow, "aridity": aridity},
            built_environment={"road_markings": "unknown", "driving_side": "unknown", "utility_poles": "unknown", "architecture": architecture, "vehicles": "unknown"},
            text_and_signs=text_items,
            sun_shadow={"shadows_visible": False, "time_of_day_guess": "unknown"},
            water={"type": "none", "notes": ""},
            region_guesses=region_guesses,
            distinctive_features=[],
            overall_confidence=0.85 if region_guesses else 0.65,
        )
        return result
