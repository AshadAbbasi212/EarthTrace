"""Stage 1: Clue Extraction - Visual perception, local OCR, tabular lookups, and hint parsing."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
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
    country_to_iso,
)
from geolocator.providers.nominatim import NominatimProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.hint_parser import HintParser
from geolocator.pipeline.schema import ClueExtractionResult, TextSignItem, RegionGuessItem
from geolocator.pipeline.landmarks import LandmarkMatcher
from geolocator.pipeline.stage2_prior import GLOBAL_GEOLOC_COUNTRIES

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

        # 1. Parse User Hints FIRST (ground-truth user cues take immediate precedence)
        user_hint_countries: List[str] = []
        if user_hint_text and user_hint_text.strip():
            parsed_hints = self.hint_parser.parse(user_hint_text)
            board.data["user_hints"] = parsed_hints
            
            for country in parsed_hints.get("countries", []):
                user_hint_countries.append(country)
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

            for sub in parsed_hints.get("subnational", []):
                div_name = sub.get("division")
                c_name = sub.get("country")
                board.add_clue(
                    text=f"User specified subnational province/state: {div_name} ({c_name})",
                    kind="user_hint_subnational",
                    status="inferred",
                    source="user_hint",
                    confidence=0.90,
                )
                board.add_candidate(f"{div_name}, {c_name}", level="region", prior=5.0)

            if parsed_hints.get("radius_km"):
                r_km = parsed_hints["radius_km"]
                board.add_clue(
                    text=f"User specified search radius constraint: {r_km:.0f} km",
                    kind="user_hint_radius",
                    status="inferred",
                    source="user_hint",
                    confidence=0.95,
                )

            if parsed_hints.get("center_coords"):
                c_lat, c_lon = parsed_hints["center_coords"]
                board.add_clue(
                    text=f"User specified approximate center coordinates: {c_lat:.4f}, {c_lon:.4f}",
                    kind="user_hint_center",
                    status="inferred",
                    source="user_hint",
                    confidence=0.95,
                )

            if parsed_hints.get("season"):
                board.add_clue(
                    text=f"User hinted season: {parsed_hints['season']}",
                    kind="user_hint_season",
                    status="inferred",
                    source="user_hint",
                    confidence=0.75,
                )

        # 2. Multi-Crop High-Resolution OCR Extraction
        ocr_snippets: List[Dict[str, Any]] = []
        try:
            # 2a. Global view (1024px, using contrast-enhanced copy if low-light detected)
            enhanced_path = job_path / "working_enhanced.jpg"
            ocr_target = enhanced_path if (board.data.get("is_low_light") and enhanced_path.exists()) else working_image_path
            ocr_snippets.extend(self.ocr.read_text(ocr_target, min_conf=0.25))
            
            # 2b. Edge and boundary crops (bottom half, bottom corners, center if available)
            edges_dir = job_path / "edges"
            if edges_dir.exists():
                crop_candidates = list(edges_dir.glob("edge_bottom*.jpg")) + list(edges_dir.glob("edge_center*.jpg"))
                for crop_path in crop_candidates[:3]:
                    crop_snippets = self.ocr.read_text(crop_path, min_conf=0.20)
                    for snip in crop_snippets:
                        snip["file_ref"] = str(crop_path.relative_to(job_path))
                        ocr_snippets.append(snip)

            # 2c. High-resolution center zoom from original image for distance highway signs
            original_path = job_path / "original.jpg"
            if not original_path.exists():
                for p in job_path.glob("original.*"):
                    original_path = p
                    break
            if original_path.exists():
                try:
                    with Image.open(original_path) as orig_im:
                        W, H = orig_im.size
                        if W > 1200 or H > 1200:
                            center_box = (int(W * 0.25), int(H * 0.25), int(W * 0.75), int(H * 0.75))
                            center_patch = orig_im.crop(center_box)
                            patch_snips = self.ocr.read_text(center_patch, min_conf=0.20)
                            for snip in patch_snips:
                                snip["file_ref"] = "original_center_zoom"
                                ocr_snippets.append(snip)
                except Exception as e:
                    logger.debug("[stage1] High-res center patch OCR skipped: %s", e)
        except Exception as e:
            logger.warning("[stage1] OCR pass encountered error: %s", e)

        # 3. Discrete Knowledge Lookups & Country Cues
        text_country_candidates: List[str] = []
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

                # 3a. License Plate Lookup
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

                # 3b. Script detection
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
                        if c_country not in text_country_candidates:
                            text_country_candidates.append(c_country)
                        board.add_candidate(c_country, level="country", prior=4.5)

                # 3c. TLD detection
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
                    if tld_country not in text_country_candidates:
                        text_country_candidates.append(tld_country)
                    board.add_candidate(tld_country, level="country", prior=8.0)

                # 3d. International Calling Code detection
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
                        if code_country not in text_country_candidates:
                            text_country_candidates.append(code_country)
                        board.add_candidate(code_country, level="country", prior=7.0)

        # 4. Visual Clue Extraction (VLM / Heuristic Perception)
        early_country_context = list(dict.fromkeys(user_hint_countries + text_country_candidates))
        if vlm_override:
            clues_result = vlm_override
            visual_country_candidates = []
        else:
            clues_result, visual_country_candidates = self._extract_visual_clues_heuristic(
                working_image_path,
                ocr_snippets,
                board=board,
                candidate_countries=early_country_context,
            )

        # 5. Compile Prioritized Candidate Countries & ISO-2 codes
        all_candidate_countries = list(dict.fromkeys(user_hint_countries + text_country_candidates + visual_country_candidates))
        candidate_country_iso_codes: List[str] = []
        for c in all_candidate_countries:
            iso = country_to_iso(c)
            if iso and iso not in candidate_country_iso_codes:
                candidate_country_iso_codes.append(iso)

        logger.info(
            "[stage1] Candidate country context: %s (ISO codes: %s)",
            all_candidate_countries, candidate_country_iso_codes
        )

        # 6. Country-Gated Place-Name & Route Geocoding via Nominatim
        all_place_phrases = []
        for snip in ocr_snippets:
            all_place_phrases.extend(extract_candidate_place_phrases(snip["text"]))
        unique_phrases = list(dict.fromkeys(all_place_phrases))
        known_synonyms = set(GEO_PHONETIC_SYNONYMS.values())

        filtered_phrases = []
        for p in unique_phrases:
            pl = p.strip().lower()
            tokens = [t.lower() for t in re.findall(r"\b\w+\b", pl)]
            if (
                pl not in COMMON_STOP_WORDS 
                and len(pl) >= 2 
                and not (tokens and all(t in COMMON_STOP_WORDS for t in tokens))
            ):
                filtered_phrases.append(p)

        filtered_phrases.sort(key=lambda p: (0 if p in known_synonyms else 1, len(p) < 4))
        filtered_phrases = filtered_phrases[:6]

        primary_cc = candidate_country_iso_codes[0] if candidate_country_iso_codes else None
        country_codes_param = ",".join(candidate_country_iso_codes[:3]) if candidate_country_iso_codes else None

        for phrase in filtered_phrases:
            try:
                query_str = GEO_PHONETIC_SYNONYMS.get(phrase, phrase).strip()
                query_words = [t.lower() for t in re.findall(r"\b\w+\b", query_str)]
                if query_words and all(t in COMMON_STOP_WORDS for t in query_words):
                    logger.debug("[stage1] Skipping token '%s' (all constituent words in COMMON_STOP_WORDS)", query_str)
                    continue

                is_route_code = bool(re.search(r"\b(US|I|M|A|B|D|N|RN|BR|NH|SH|E|Q|O|Ruta|Route|Hwy|Highway)\s*[\-\.]?\s*(\d{1,4}[A-Z]?)\b", query_str, re.IGNORECASE))
                
                # Rule: Only query Nominatim if the token is a recognized route code, a known phonetic synonym,
                # a multi-word phrase with non-stopword tokens, or a capitalized proper noun of at least 5 letters.
                # Never query arbitrary 3-4 letter abbreviations/fragments (e.g. BEIT, NYOK, STOP).
                is_proper_place_query = (
                    is_route_code
                    or (query_str in GEO_PHONETIC_SYNONYMS.values())
                    or (len(query_str.split()) >= 2 and any(t not in COMMON_STOP_WORDS for t in query_words))
                    or (len(query_str) >= 5 and query_str[0].isupper() and query_str.lower() not in COMMON_STOP_WORDS)
                )

                if not is_proper_place_query:
                    logger.debug("[stage1] Skipping ambiguous/fragmentary token '%s'", query_str)
                    continue

                # Disallow global unconstrained searches on short tokens or route numbers
                if not country_codes_param and is_route_code:
                    logger.debug("[stage1] Skipping unconstrained route query '%s' without country gating", query_str)
                    continue

                nom_results = []
                # First try with primary candidate country for maximum geographic fidelity
                if primary_cc:
                    nom_results = self.nominatim.search(query_str, country_codes=primary_cc, limit=1)

                # Then fallback to all candidate countries if primary had no match
                if not nom_results and country_codes_param:
                    nom_results = self.nominatim.search(query_str, country_codes=country_codes_param, limit=1)

                # Fallback to global query ONLY for distinct multi-word proper nouns with substantial non-stopword tokens
                if not nom_results and not is_route_code and len(query_str.split()) >= 2 and any(t not in COMMON_STOP_WORDS for t in query_words):
                    nom_results = self.nominatim.search(query_str, limit=1)

                if nom_results:
                    hit = nom_results[0]
                    hit_address = hit.get("address", {})
                    hit_cc = hit_address.get("country_code", "").lower()

                    # Geographic consistency check: Reject if search returned an unexpected foreign country
                    if candidate_country_iso_codes and hit_cc and hit_cc not in candidate_country_iso_codes:
                        logger.info("[stage1] Geocoded hit '%s' in '%s' rejected (mismatch with %s)", query_str, hit_cc, candidate_country_iso_codes)
                        continue

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
        candidate_countries: Optional[List[str]] = None,
    ) -> Tuple[ClueExtractionResult, List[str]]:
        """Visual cue extraction using local CLIP zero-shot classification with algorithmic fallback."""
        im = Image.open(image_path).convert("RGB")
        W, H = im.size
        
        # Color distribution analysis
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
        visual_country_candidates: List[str] = []

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

            # Geoguessr Meta-Feature Classification (Vehicles, road infrastructure, regional architecture, soil, flora)
            meta_prompts = [
                ("rickshaw", "an auto rickshaw, three-wheeled vehicle, or motorized tuk tuk in traffic"),
                ("truck_art", "a brightly painted Bedford truck or commercial lorry with vibrant South Asian truck art patterns"),
                ("south_asian_arch", "flat roof red brick or concrete South Asian architecture"),
                ("gulf_arch", "a modern white residential villa, high boundary wall, and palm tree avenue in the Arabian Gulf or UAE"),
                ("desert_highway", "a long straight multi-lane asphalt highway through open desert with light sand or dunes"),
                ("iranian_plateau_arch", "traditional Iranian plateau mudbrick architecture, Persian dome tilework, or adobe"),
                ("nile_brick_masonry", "red clay unplastered brick apartment blocks with exposed concrete pillars and rebar in Egypt"),
                ("turkish_townscape", "red clay tile pitched roofs on hillside residential apartments and minarets in Turkey"),
                ("levantine_stone", "pale limestone clad buildings on hilly Mediterranean terrain with olive trees"),
                ("concrete_ladder_pole", "concrete ladder utility pole with rungs and electrical wires"),
                ("yellow_rear_plate", "a vehicle with a yellow rear license plate"),
                ("eu_blue_strip_plate", "a white vehicle license plate with a blue vertical stripe on the left edge"),
                ("commercial_yellow_plate", "a commercial vehicle with yellow number plate"),
                ("yellow_road_lines", "yellow center lane lines or double yellow lines on asphalt road"),
                ("black_yellow_curb", "concrete road curb painted with alternating black and yellow stripes"),
                ("red_white_curb", "concrete road curb painted with alternating red and white stripes"),
                ("wooden_utility_pole", "a wooden utility pole with crossarms along a roadside"),
                ("red_laterite_soil", "red clay soil, red dirt road, or laterite earth"),
                ("pale_limestone_rock", "pale limestone rock outcrop, chalky dry soil, or karst terrain"),
                ("desert_sand", "golden desert sand dunes, light desert gravel reg, or arid sand"),
                ("date_palm_groves", "date palm trees, desert oasis palms, or fan palms"),
                ("olive_groves", "an olive tree grove or Mediterranean cypress trees"),
                ("conifer_forest", "coniferous pine, spruce, or deodar cedar mountain forest"),
                ("tropical_banyan_neem", "tropical banyan tree, neem tree, or dense lush subtropical foliage"),
            ]
            meta_texts = [m[1] for m in meta_prompts]
            meta_inputs = clip_proc(text=meta_texts, images=im, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                meta_out = clip_model(**meta_inputs)
                meta_probs = meta_out.logits_per_image.softmax(dim=-1).cpu().numpy()[0]

            env_meta: Dict[str, Any] = {}

            for m_idx, (m_key, m_desc) in enumerate(meta_prompts):
                m_prob = float(meta_probs[m_idx])
                if m_key == "rickshaw" and m_prob >= 0.35:
                    if board:
                        board.add_clue(
                            text="Auto-rickshaw / three-wheeled vehicle observed in scene",
                            kind="vehicle_type",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_rk in ["Pakistan", "India", "Bangladesh", "Egypt"]:
                        if c_rk not in visual_country_candidates:
                            visual_country_candidates.append(c_rk)
                elif m_key == "truck_art" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Vibrant painted truck art vehicle observed in scene",
                            kind="vehicle_type",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_ta in ["Pakistan", "India"]:
                        if c_ta not in visual_country_candidates:
                            visual_country_candidates.append(c_ta)
                elif m_key == "south_asian_arch" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Flat concrete / red brick South Asian architecture observed",
                            kind="architecture",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_sa in ["Pakistan", "India", "Bangladesh"]:
                        if c_sa not in visual_country_candidates:
                            visual_country_candidates.append(c_sa)
                elif m_key == "gulf_arch" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Arabian Gulf residential villa compound architecture observed",
                            kind="architecture",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_gulf in ["United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait", "Bahrain", "Oman"]:
                        if c_gulf not in visual_country_candidates:
                            visual_country_candidates.append(c_gulf)
                elif m_key == "desert_highway" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Long-distance arid desert highway corridor observed",
                            kind="infrastructure",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_dh in ["Saudi Arabia", "United Arab Emirates", "Oman", "Qatar", "Kuwait", "Egypt"]:
                        if c_dh not in visual_country_candidates:
                            visual_country_candidates.append(c_dh)
                elif m_key == "iranian_plateau_arch" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Iranian plateau / Persian architectural elements observed",
                            kind="architecture",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    if "Iran" not in visual_country_candidates:
                        visual_country_candidates.append("Iran")
                elif m_key == "nile_brick_masonry" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Nile valley red-brick concrete pillar masonry observed",
                            kind="architecture",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    if "Egypt" not in visual_country_candidates:
                        visual_country_candidates.append("Egypt")
                elif m_key == "turkish_townscape" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Turkish / Mediterranean pitched red tile townscape observed",
                            kind="architecture",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    if "Turkey" not in visual_country_candidates:
                        visual_country_candidates.append("Turkey")
                elif m_key == "levantine_stone" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Levantine pale limestone masonry observed",
                            kind="architecture",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_lev in ["Israel", "Jordan", "Syria"]:
                        if c_lev not in visual_country_candidates:
                            visual_country_candidates.append(c_lev)
                elif m_key == "concrete_ladder_pole" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Concrete ladder utility pole observed",
                            kind="infrastructure",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    env_meta["pole_type"] = "concrete_ladder"
                elif m_key == "yellow_rear_plate" and m_prob >= 0.28:
                    if board:
                        board.add_clue(
                            text="Yellow rear vehicle license plate format detected",
                            kind="license_plate",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_yp in ["United Kingdom", "Israel", "Netherlands", "Cyprus"]:
                        if c_yp not in visual_country_candidates:
                            visual_country_candidates.append(c_yp)
                    env_meta["plate_style"] = "yellow_rear"
                elif m_key == "eu_blue_strip_plate" and m_prob >= 0.28:
                    if board:
                        board.add_clue(
                            text="European Union standard blue-band license plate format detected",
                            kind="license_plate",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_eu in ["Germany", "France", "Italy", "Spain", "Turkey"]:
                        if c_eu not in visual_country_candidates:
                            visual_country_candidates.append(c_eu)
                    env_meta["plate_style"] = "eu_blue_band"
                elif m_key == "commercial_yellow_plate" and m_prob >= 0.28:
                    if board:
                        board.add_clue(
                            text="South Asian commercial yellow license plate detected",
                            kind="license_plate",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_cyp in ["India", "Pakistan"]:
                        if c_cyp not in visual_country_candidates:
                            visual_country_candidates.append(c_cyp)
                    env_meta["plate_style"] = "commercial_yellow"
                elif m_key == "yellow_road_lines" and m_prob >= 0.28:
                    if board:
                        board.add_clue(
                            text="Yellow center line road markings observed",
                            kind="road_infrastructure",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    env_meta["road_marking"] = "yellow_center"
                elif m_key == "black_yellow_curb" and m_prob >= 0.28:
                    if board:
                        board.add_clue(
                            text="Black and yellow striped curb marking observed",
                            kind="road_infrastructure",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_by in ["Pakistan", "India", "United Kingdom"]:
                        if c_by not in visual_country_candidates:
                            visual_country_candidates.append(c_by)
                    env_meta["curb_style"] = "black_yellow"
                elif m_key == "red_laterite_soil" and m_prob >= 0.28:
                    if board:
                        board.add_clue(
                            text="Red laterite clay soil / terrain observed",
                            kind="soil_type",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_ls in ["India", "Brazil", "Australia"]:
                        if c_ls not in visual_country_candidates:
                            visual_country_candidates.append(c_ls)
                    env_meta["soil_type"] = "red_laterite"
                elif m_key == "desert_sand" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Arid desert sand / dunes terrain observed",
                            kind="soil_type",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_ds in ["Saudi Arabia", "United Arab Emirates", "Egypt", "Oman", "Qatar", "Kuwait"]:
                        if c_ds not in visual_country_candidates:
                            visual_country_candidates.append(c_ds)
                    env_meta["soil_type"] = "desert_sand"
                elif m_key == "date_palm_groves" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Date palm trees / desert oasis grove observed",
                            kind="flora",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_dp in ["United Arab Emirates", "Saudi Arabia", "Egypt", "Oman", "Iraq", "Pakistan"]:
                        if c_dp not in visual_country_candidates:
                            visual_country_candidates.append(c_dp)
                    env_meta["dominant_flora"] = "date_palm"
                elif m_key == "olive_groves" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Olive tree grove / Mediterranean vegetation observed",
                            kind="flora",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    for c_og in ["Greece", "Italy", "Spain", "Turkey", "Israel", "Syria"]:
                        if c_og not in visual_country_candidates:
                            visual_country_candidates.append(c_og)
                    env_meta["dominant_flora"] = "olive_groves"
                elif m_key == "conifer_forest" and m_prob >= 0.30:
                    if board:
                        board.add_clue(
                            text="Coniferous pine / alpine forest observed",
                            kind="flora",
                            status="observed",
                            source="clip_meta",
                            confidence=round(m_prob, 2),
                        )
                    env_meta["dominant_flora"] = "conifer_forest"

            if board:
                board.data["environmental_meta"] = env_meta

            # Solar Hemispheric Latitude Estimation
            try:
                from geolocator.pipeline.solar_utils import estimate_solar_hemisphere
                exif_meta = board.data.get("exif", {}) if board else {}
                solar_res = estimate_solar_hemisphere(im, exif_data=exif_meta)
                if board:
                    board.data["solar_meta"] = solar_res
                if solar_res.get("hemisphere") in ("northern", "southern") and solar_res.get("confidence", 0.0) >= 0.65:
                    h_name = solar_res["hemisphere"].title()
                    if board:
                        board.add_clue(
                            text=f"Solar / shadow geometry indicates {h_name} Hemisphere ({solar_res['reason']})",
                            kind="solar_hemisphere",
                            status="computed",
                            source="solar_math",
                            confidence=solar_res["confidence"],
                        )
            except Exception as e:
                logger.debug("[stage1_solar] Solar estimation bypass: %s", e)

            # Direct Contour Skyline Analysis
            try:
                from geolocator.pipeline.skyline_extractor import SkylineExtractor
                extractor = SkylineExtractor(target_width=120)
                overlay_path = image_path.parent / "skyline_overlay.png"
                sky_info = extractor.extract_from_image(im, save_overlay_path=overlay_path)
                std_elev = sky_info.get("std_elevation", 0.0)
                is_roofline = sky_info.get("is_manmade_roofline", False)
                is_urban_built = (
                    scene_type in ("urban", "building", "indoor")
                    or architecture in ("historic_monument", "institutional_brick", "urban_modern")
                )

                if is_roofline or is_urban_built:
                    logger.info(
                        "[stage1_skyline] Contour identified as building roofline / architectural silhouette (scene=%s, arch=%s, roofline=%s); preserving natural terrain relief as flat/urban.",
                        scene_type, architecture, is_roofline
                    )
                    # Building rooflines are built environment features, not natural mountain horizons
                    sky_info["is_non_flat"] = False
                elif sky_info.get("is_non_flat", False) or std_elev >= 0.02:
                    relief = "mountainous" if std_elev >= 0.055 else "hilly"
                    horizon_visible = True
                    logger.info("[stage1_skyline] Direct contour inspection confirmed non-flat natural terrain (std=%.4f, relief=%s)", std_elev, relief)
            except Exception as e:
                logger.debug("[stage1_skyline] Direct contour check error: %s", e)

            # Multi-template Zero-shot Country Perception Sweep
            country_templates = [
                "a street or road photo in {c}",
                "a scenic landscape or countryside in {c}",
                "architecture and buildings in {c}",
                "typical nature and flora in {c}",
            ]
            all_country_prompts = [tmpl.format(c=c) for tmpl in country_templates for c in GLOBAL_GEOLOC_COUNTRIES]
            c_inputs = clip_proc(text=all_country_prompts, images=im, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                c_out = clip_model(**c_inputs)
                c_logits_mat = c_out.logits_per_image.view(len(country_templates), len(GLOBAL_GEOLOC_COUNTRIES)).mean(dim=0)
                c_probs = c_logits_mat.softmax(dim=-1).cpu().numpy()

            top_c_indices = np.argsort(c_probs)[::-1]
            top_c1_idx = int(top_c_indices[0])
            top_c1_country = GLOBAL_GEOLOC_COUNTRIES[top_c1_idx]
            top_c1_prob = float(c_probs[top_c1_idx])
            logger.info(
                "[stage1_country] Top zero-shot countries (multi-template ensemble): %s (%.3f), %s (%.3f), %s (%.3f)",
                top_c1_country, top_c1_prob,
                GLOBAL_GEOLOC_COUNTRIES[int(top_c_indices[1])], float(c_probs[top_c_indices[1]]),
                GLOBAL_GEOLOC_COUNTRIES[int(top_c_indices[2])], float(c_probs[top_c_indices[2]]),
            )
            for idx in top_c_indices[:3]:
                c_name = GLOBAL_GEOLOC_COUNTRIES[int(idx)]
                if float(c_probs[idx]) >= 0.08 and c_name not in visual_country_candidates:
                    visual_country_candidates.append(c_name)

            if top_c1_prob >= 0.18 and not region_guesses:
                region_guesses.append(RegionGuessItem(place=top_c1_country, confidence=round(top_c1_prob, 3), reason="Vision-language country prior"))

            # Automatic Landmark Perception:
            # LandmarkMatcher uses 8 negative prompt rejectors and country consistency checks.
            # Run whenever scene is not flat empty terrain, or if user explicitly hinted landmarks.
            user_requested_landmark = bool(board and board.data.get("user_hints", {}).get("landmarks"))
            all_known_countries = list(dict.fromkeys((candidate_countries or []) + visual_country_candidates))
            should_run_landmark = (
                user_requested_landmark
                or scene_type in ("urban", "monument", "mountain", "desert", "coastal", "other")
            )
            if should_run_landmark:
                lm_matcher = LandmarkMatcher()
                lm_res = lm_matcher.match(im, clip_model, clip_proc, device=device, candidate_countries=all_known_countries)
                if lm_res and lm_res.get("confidence", 0.0) >= 0.50:
                    l_name = lm_res["name"]
                    l_lat = lm_res["latitude"]
                    l_lon = lm_res["longitude"]
                    l_conf = lm_res["confidence"]
                    reason_desc = "User-requested landmark perception" if user_requested_landmark else "Zero-shot visual landmark identification"
                    region_guesses.append(RegionGuessItem(place=l_name, confidence=l_conf, reason=reason_desc))
                    cand_name = f"Landmark: {l_name}"
                    if board:
                        board.add_candidate(
                            name=cand_name,
                            level="point",
                            lat=l_lat,
                            lon=l_lon,
                            prior=3.5,
                            metadata={
                                "landmark": l_name,
                                "tier": "T1" if l_conf >= 0.70 else "T2",
                                "radius_km": lm_res.get("radius_km", 2.0),
                                "source": "landmark_matcher",
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

        # Construct GeoSpy-style structured supporting vs uncertain clues and forensic interpretation
        supporting_clues: List[str] = []
        uncertain_clues: List[str] = []

        if scene_type != "other":
            supporting_clues.append(f"Visual environment matches {scene_type} biome ({relief} relief, {veg_density} vegetation)")
        if aridity == "arid":
            supporting_clues.append("High solar aridity and dry soil conditions observed")
        elif snow:
            supporting_clues.append("Snow / alpine frost cover observed")
        if text_items:
            supporting_clues.append(f"Signage / text markers detected: {', '.join(t.text for t in text_items[:3])}")
        for rg in region_guesses[:3]:
            supporting_clues.append(f"Candidate region: {rg.place} ({rg.reason})")
        for sc in visual_country_candidates[:2]:
            supporting_clues.append(f"Visual-language likelihood aligns with {sc}")

        # Confounding or uncertain clues
        if relief == "unknown":
            uncertain_clues.append("Terrain relief is partially obstructed or ambiguous")
        if not text_items:
            uncertain_clues.append("No legible road furniture, license plates, or signage in frame")
        if len(visual_country_candidates) > 2:
            uncertain_clues.append(f"Cross-regional visual homonyms between {', '.join(visual_country_candidates[:3])}")

        interp_parts = [
            f"Scene categorized as {scene_type} with {relief} relief and {aridity} climate characteristics.",
        ]
        if visual_country_candidates:
            interp_parts.append(f"Visual appearance aligns with {', '.join(visual_country_candidates[:3])}.")
        if text_items:
            interp_parts.append(f"Observed textual markers include: {', '.join(t.text for t in text_items[:3])}.")
        interpretation = " ".join(interp_parts)

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
            interpretation=interpretation,
            supporting_clues=supporting_clues,
            uncertain_clues=uncertain_clues,
        )
        return result, visual_country_candidates

