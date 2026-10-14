"""Stage 2: Global Prior & Biome Candidate Generation."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import numpy as np
from PIL import Image

from geolocator.config import AppConfig, get_config
from geolocator.models.model_manager import ModelManager, get_model_manager
from geolocator.providers.climate import ClimateProvider
from geolocator.providers.landcover import LandCoverProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.geo_utils import (
    haversine_distance_km,
    point_in_bbox,
    is_in_region,
    get_country_candidate,
    get_country_anchors,
    get_subnational_division,
    cluster_points,
    COUNTRY_BBOXES,
)
from geolocator.adapters.clues_adapter import (
    lookup_driving_side,
    detect_script,
    detect_tld,
    detect_calling_code,
)

logger = logging.getLogger("geolocator.pipeline.stage2_prior")

# Comprehensive global country set for vision-language zero-shot country likelihood estimation
# Fully covering all 15 prioritized South Asia & Middle East nations plus worldwide baselines
GLOBAL_GEOLOC_COUNTRIES: List[str] = [
    # South & Central Asia
    "Pakistan", "India", "Bangladesh", "Nepal", "Sri Lanka", "Afghanistan",
    "Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan",
    # Middle East & North Africa (All 15 target countries fully covered)
    "Iran", "Iraq", "Turkey", "Saudi Arabia", "United Arab Emirates", "Israel",
    "Qatar", "Kuwait", "Oman", "Yemen", "Bahrain", "Syria",
    "Jordan", "Egypt", "Morocco", "Algeria", "Tunisia",
    # Europe
    "United Kingdom", "Ireland", "France", "Germany", "Italy", "Spain", "Portugal",
    "Netherlands", "Belgium", "Switzerland", "Austria", "Greece", "Poland",
    "Czech Republic", "Hungary", "Romania", "Sweden", "Norway", "Finland", "Denmark",
    "Ukraine", "Russia",
    # East & Southeast Asia
    "Japan", "South Korea", "China", "Taiwan", "Thailand", "Vietnam",
    "Indonesia", "Malaysia", "Philippines",
    # Americas
    "United States", "Canada", "Mexico", "Brazil", "Argentina", "Chile",
    "Colombia", "Peru",
    # Sub-Saharan Africa
    "South Africa", "Kenya", "Nigeria",
    # Oceania
    "Australia", "New Zealand",
]


class Stage2Prior:
    """Stage 2: Computes global image prior (GeoCLIP), filters with Köppen climate and clues."""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        model_manager: Optional[ModelManager] = None,
        climate_provider: Optional[ClimateProvider] = None,
        landcover_provider: Optional[LandCoverProvider] = None,
    ):
        self.config = config or get_config()
        self.model_manager = model_manager or get_model_manager(self.config)
        cache_dir = getattr(self.config, "storage", None) and self.config.storage.cache_dir or ".geo-cache"
        self.climate = climate_provider or ClimateProvider(cache_dir=cache_dir, offline_mode=self.config.offline_mode)
        self.landcover = landcover_provider or LandCoverProvider(cache_dir=cache_dir, offline_mode=self.config.offline_mode)

    def _ensure_geoclip_registered(self) -> None:
        """Register GeoCLIP lazy loader with ModelManager if not already registered."""
        if "geoclip" not in self.model_manager._model_loaders:
            def _loader():
                from geoclip import GeoCLIP
                dev_setting = getattr(getattr(self.config, "hardware", None), "device", "cuda")
                device = "cuda" if (torch.cuda.is_available() and dev_setting == "cuda") else "cpu"
                logger.info("Initializing GeoCLIP on device '%s'...", device)
                try:
                    return GeoCLIP().to(device)
                except Exception as e:
                    logger.warning("GeoCLIP failed to load on %s (%s), falling back to cpu", device, e)
                    return GeoCLIP().to("cpu")

            self.model_manager.register_loader("geoclip", _loader)

    def _ensure_reranker_registered(self) -> None:
        """Register StreetCLIP / CLIP ViT-Large lazy loader with ModelManager."""
        if "geo_reranker" not in self.model_manager._model_loaders:
            def _loader():
                from transformers import CLIPProcessor, CLIPModel
                from pathlib import Path
                
                # Check if StreetCLIP is locally ready
                streetclip_dir = Path(r"C:\Users\David\.cache\huggingface\hub\models--geolocal--StreetCLIP\snapshots\e3561ba2ad9bf14c9efd6b0092607b8497efbfea")
                if (streetclip_dir / "model.safetensors").exists() and (streetclip_dir / "model.safetensors").stat().st_size > 1700000000:
                    model_id = str(streetclip_dir)
                    logger.info("[stage2] Initializing fine-tuned StreetCLIP for zero-shot geographic reranking: %s...", model_id)
                else:
                    model_id = "openai/clip-vit-large-patch14"
                    logger.info("[stage2] Initializing CLIP ViT-Large for zero-shot geographic reranking: %s...", model_id)

                dev_setting = getattr(getattr(self.config, "hardware", None), "device", "cuda")
                device = "cuda" if (torch.cuda.is_available() and dev_setting == "cuda") else "cpu"
                processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
                model = CLIPModel.from_pretrained(model_id, local_files_only=True).to(device)
                model.eval()

                class RerankerWrapper:
                    def __init__(self, p, m):
                        self.processor = p
                        self.model = m
                    def to(self, d):
                        self.model.to(d)
                        return self
                    def __iter__(self):
                        return iter((self.processor, self.model))

                return RerankerWrapper(processor, model)

            self.model_manager.register_loader("geo_reranker", _loader)

    def score_candidate_countries_zero_shot(
        self,
        image_path: Path | str,
        candidate_countries: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Compute vision-language geographic likelihood for candidate countries using StreetCLIP / CLIP ViT-Large."""
        img_p = Path(image_path)
        if not img_p.exists():
            return {}

        if candidate_countries is None or len(candidate_countries) == 0:
            candidate_countries = GLOBAL_GEOLOC_COUNTRIES

        clean_countries = [c.strip() for c in candidate_countries if c and len(c.strip()) >= 2]
        unique_countries = list(dict.fromkeys(clean_countries))
        if len(unique_countries) < 2:
            return {c: 1.0 for c in unique_countries}

        try:
            self._ensure_reranker_registered()
            with self.model_manager.acquire("geo_reranker") as (processor, model):
                device = next(model.parameters()).device
                with Image.open(str(image_path)) as img:
                    im = img.convert("RGB")
                    if max(im.size) > 672:
                        im.thumbnail((672, 672), Image.LANCZOS)
                    
                    w, h = im.size
                    templates = [
                        "a photo taken in {c}",
                        "a street or road photo in {c}",
                        "a scenic landscape or countryside in {c}",
                        "architecture and buildings in {c}",
                    ]
                    all_prompts = [tmpl.format(c=c) for tmpl in templates for c in unique_countries]

                    if w >= 224 and h >= 224:
                        crop_full = im
                        crop_horizon = im.crop((0, int(h * 0.05), w, int(h * 0.70)))
                        crop_ground = im.crop((0, int(h * 0.40), w, h))
                        crops = [crop_full, crop_horizon, crop_ground]
                        weights = [0.50, 0.25, 0.25]
                    else:
                        crops = [im]
                        weights = [1.0]

                    inputs = processor(text=all_prompts, images=crops, return_tensors="pt", padding=True).to(device)
                    with torch.no_grad():
                        outputs = model(**inputs)
                        probs_mat = outputs.logits_per_image.view(len(crops), len(templates), len(unique_countries)).mean(dim=1).softmax(dim=-1).cpu().numpy()
                        # Weighted sum across crops
                        combined_probs = np.zeros(len(unique_countries), dtype=np.float32)
                        for cr_idx, w_cr in enumerate(weights):
                            combined_probs += w_cr * probs_mat[cr_idx]
                        combined_probs = combined_probs / np.sum(combined_probs)

                    scored = {c: float(p) for c, p in zip(unique_countries, combined_probs)}
                    sorted_scored = dict(sorted(scored.items(), key=lambda kv: kv[1], reverse=True))
                    logger.info("[stage2] Zero-shot multi-crop geographic ranking (ensemble): %s", 
                                {k: f"{v*100:.1f}%" for k, v in list(sorted_scored.items())[:5]})
                    return sorted_scored
        except Exception as e:
            logger.warning("[stage2] Geographic zero-shot reranking error: %s", e)
            return {}

    def predict_image_locations(
        self,
        image_path: Path,
        top_k: int = 50,
        mock_predictions: Optional[List[Dict[str, float]]] = None,
        multi_crop: bool = True,
        in_country_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, float]]:
        """Run GeoCLIP inference with batched multi-crop spatial pooling and HCNGR refinement."""
        if mock_predictions is not None:
            return mock_predictions

        self._ensure_geoclip_registered()
        predictions: List[Dict[str, float]] = []

        try:
            with self.model_manager.acquire("geoclip") as model:
                with Image.open(str(image_path)) as img:
                    im = img.convert("RGB")
                    w, h = im.size

                    if multi_crop and w >= 224 and h >= 224:
                        # Multi-crop ensemble: full, center, horizon, and ground
                        crop_full = im
                        crop_center = im.crop((int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)))
                        crop_horizon = im.crop((0, int(h * 0.05), w, int(h * 0.70)))
                        crop_ground = im.crop((0, int(h * 0.40), w, h))
                        crops = [crop_full, crop_center, crop_horizon, crop_ground]
                    else:
                        crops = [im]

                    # Ensure model device
                    m_dev = next(model.parameters()).device
                    tensors = [model.image_encoder.preprocess_image(c) for c in crops]
                    batch = torch.cat(tensors, dim=0).to(m_dev)
                    gps_gal = model.gps_gallery.to(m_dev)

                    unique_cands: List[Dict[str, Any]] = []
                    if in_country_candidates:
                        seen_c = set()
                        for c in in_country_candidates:
                            ck = (round(c["lat"], 3), round(c["lon"], 3))
                            if ck not in seen_c:
                                seen_c.add(ck)
                                unique_cands.append(c)

                    if unique_cands:
                        cand_arr = np.array([[float(c["lat"]), float(c["lon"])] for c in unique_cands], dtype=np.float32)
                        t_cands = torch.tensor(cand_arr, dtype=torch.float32, device=m_dev)
                        all_locations = torch.cat([gps_gal, t_cands], dim=0)
                    else:
                        all_locations = gps_gal

                    with torch.no_grad():
                        logits = model.forward(batch, all_locations)
                        probs = logits.softmax(dim=-1).mean(dim=0)

                        # Top gallery points
                        gal_probs = probs[:len(gps_gal)]
                        top_pred = torch.topk(gal_probs, min(top_k, len(gps_gal)))
                        coords_np = gps_gal.index_select(0, top_pred.indices).cpu().numpy()
                        probs_np = top_pred.values.cpu().numpy()

                        # Hierarchical Continuous Neural Location Refinement (HCNGR) on gallery points
                        for top_i in range(min(5, len(coords_np))):
                            try:
                                c_lat, c_lon = float(coords_np[top_i][0]), float(coords_np[top_i][1])
                                lats1 = np.linspace(c_lat - 0.6, c_lat + 0.6, 19)
                                lons1 = np.linspace(c_lon - 0.6, c_lon + 0.6, 19)
                                grid_lats1, grid_lons1 = np.meshgrid(lats1, lons1)
                                grid1 = np.stack([grid_lats1.ravel(), grid_lons1.ravel()], axis=1)
                                t_grid1 = torch.tensor(grid1, dtype=torch.float32, device=m_dev)
                                logits1 = model.forward(batch[0:1], t_grid1)
                                best_i1 = torch.argmax(logits1[0]).item()
                                b_lat1, b_lon1 = float(grid1[best_i1][0]), float(grid1[best_i1][1])

                                lats2 = np.linspace(b_lat1 - 0.12, b_lat1 + 0.12, 19)
                                lons2 = np.linspace(b_lon1 - 0.12, b_lon1 + 0.12, 19)
                                grid_lats2, grid_lons2 = np.meshgrid(lats2, lons2)
                                grid2 = np.stack([grid_lats2.ravel(), grid_lons2.ravel()], axis=1)
                                t_grid2 = torch.tensor(grid2, dtype=torch.float32, device=m_dev)
                                logits2 = model.forward(batch[0:1], t_grid2)
                                best_i2 = torch.argmax(logits2[0]).item()
                                coords_np[top_i][0] = float(grid2[best_i2][0])
                                coords_np[top_i][1] = float(grid2[best_i2][1])
                            except Exception as e_hcngr:
                                logger.debug("[stage2_hcngr] Refinement skipped for point %d: %s", top_i, e_hcngr)

                        for i in range(len(coords_np)):
                            predictions.append({
                                "lat": float(coords_np[i][0]),
                                "lon": float(coords_np[i][1]),
                                "prob": float(probs_np[i]),
                            })

                        # In-country continuous neural location scoring & hierarchical refinement
                        if unique_cands:
                            cand_probs = probs[len(gps_gal):].cpu().numpy()
                            sorted_cand_indices = np.argsort(cand_probs)[::-1]
                            top_cand_indices = list(sorted_cand_indices[:min(60, len(unique_cands))])
                            # Ensure all curated regional anchors are included alongside grid points
                            cand_index_set = set(top_cand_indices)
                            for c_i, c_obj in enumerate(unique_cands):
                                if "Grid" not in (c_obj.get("name") or "") and c_i not in cand_index_set:
                                    top_cand_indices.append(c_i)
                                    cand_index_set.add(c_i)

                            for rank_i, c_idx in enumerate(top_cand_indices):
                                orig_cand = unique_cands[c_idx]
                                c_lat, c_lon = float(orig_cand["lat"]), float(orig_cand["lon"])
                                ref_lat, ref_lon = c_lat, c_lon

                                if rank_i < 5:
                                    try:
                                        # Level 1: coarse grid +/- 0.5 degrees (15x15 = 225 points)
                                        lats1 = np.linspace(c_lat - 0.5, c_lat + 0.5, 15)
                                        lons1 = np.linspace(c_lon - 0.5, c_lon + 0.5, 15)
                                        glat1, glon1 = np.meshgrid(lats1, lons1)
                                        grid1 = np.stack([glat1.ravel(), glon1.ravel()], axis=1)
                                        t_grid1 = torch.tensor(grid1, dtype=torch.float32, device=m_dev)
                                        lg1 = model.forward(batch[0:1], t_grid1)
                                        b_idx1 = torch.argmax(lg1[0]).item()
                                        b_lat1, b_lon1 = float(grid1[b_idx1][0]), float(grid1[b_idx1][1])

                                        # Level 2: fine grid +/- 0.1 degrees (15x15 = 225 points)
                                        lats2 = np.linspace(b_lat1 - 0.1, b_lat1 + 0.1, 15)
                                        lons2 = np.linspace(b_lon1 - 0.1, b_lon1 + 0.1, 15)
                                        glat2, glon2 = np.meshgrid(lats2, lons2)
                                        grid2 = np.stack([glat2.ravel(), glon2.ravel()], axis=1)
                                        t_grid2 = torch.tensor(grid2, dtype=torch.float32, device=m_dev)
                                        lg2 = model.forward(batch[0:1], t_grid2)
                                        b_idx2 = torch.argmax(lg2[0]).item()
                                        ref_lat, ref_lon = float(grid2[b_idx2][0]), float(grid2[b_idx2][1])
                                    except Exception as e_cr:
                                        logger.debug("[stage2] In-country refinement skipped: %s", e_cr)

                                predictions.append({
                                    "lat": ref_lat,
                                    "lon": ref_lon,
                                    "prob": float(cand_probs[c_idx]),
                                    "anchor_name": orig_cand.get("name") or orig_cand.get("anchor_name"),
                                    "country": orig_cand.get("country"),
                                })
        except Exception as e:
            logger.warning("[stage2] GeoCLIP inference failed or timed out: %s. Continuing with clue priors.", e)

        return predictions

    def process(
        self,
        job_dir: Path,
        board: CandidateBoard,
        working_image_path: Optional[Path] = None,
        top_k: int = 50,
        mock_predictions: Optional[List[Dict[str, float]]] = None,
    ) -> Tuple[Dict[str, Any], CandidateBoard]:
        """Execute Stage 2: compute global prior, fuse with climate/biome/clues, output candidate cells."""
        job_dir = Path(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)

        # Determine input image
        if working_image_path is None:
            working_image_path = job_dir / "working_1024.jpg"
            if not working_image_path.exists():
                working_image_path = job_dir / "working_512.jpg"
            if not working_image_path.exists():
                working_image_path = board.photo_path
        logger.info("Stage 2 Prior: evaluating clues and geographic prior on %s", working_image_path)

        # 1. Extract perception cues and user hints from board & disk
        observed_clues = board.data.get("clues", {})
        aridity_cue = 0.0
        veg_cue = 0.5
        snow_cue = False
        driving_cue: Optional[str] = None
        hint_countries: List[str] = []
        subnational_hints: List[str] = []
        script_countries: List[str] = []
        tld_country: Optional[str] = None
        phone_country: Optional[str] = None

        user_hints_dict = board.data.get("user_hints", {})
        for sub_item in user_hints_dict.get("subnational", []):
            if sub_item.get("division") and sub_item["division"] not in subnational_hints:
                subnational_hints.append(sub_item["division"])
        radius_km_hint: Optional[float] = user_hints_dict.get("radius_km")
        center_coords_hint: Optional[Tuple[float, float]] = user_hints_dict.get("center_coords")

        for cid, cinfo in observed_clues.items():
            kind = cinfo.get("kind")
            text = cinfo.get("text", "")
            if kind == "user_hint_subnational":
                m = re.search(r"province/state:\s*([^\(]+)", text)
                if m:
                    sub_name = m.group(1).strip()
                    if sub_name not in subnational_hints:
                        subnational_hints.append(sub_name)
            elif kind == "user_hint_radius":
                m = re.search(r"radius constraint:\s*(\d+)", text)
                if m and not radius_km_hint:
                    radius_km_hint = float(m.group(1))
            elif kind == "user_hint_center":
                m = re.search(r"center coordinates:\s*(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", text)
                if m and not center_coords_hint:
                    center_coords_hint = (float(m.group(1)), float(m.group(2)))
            if kind == "colorimetry":
                if "arid" in text.lower() or "desert" in text.lower():
                    aridity_cue = 0.8
                    veg_cue = 0.1
                elif "vegetation" in text.lower():
                    veg_cue = 0.7
                    aridity_cue = 0.1
            elif kind == "driving_side":
                if "left" in text.lower():
                    driving_cue = "left"
                elif "right" in text.lower():
                    driving_cue = "right"
            elif kind == "hint_country":
                hint_countries.append(text)
            elif kind == "script":
                hit = detect_script(text)
                if hit:
                    script_countries.extend(hit["candidate_countries"])
            elif kind == "tld":
                hit = detect_tld(text)
                if hit:
                    tld_country = hit["country"]
            elif kind == "calling_code":
                hit = detect_calling_code(text)
                if hit:
                    phone_country = hit["country"]

        # Check intake colorimetry from disk if available
        clues_file = job_dir / "clues.json"
        if clues_file.exists():
            try:
                cdata = json.loads(clues_file.read_text(encoding="utf-8"))
                vp = cdata.get("visual_perception", {})
                aridity_cue = max(aridity_cue, float(vp.get("aridity", 0.0)))
                veg_cue = float(vp.get("vegetation_index", veg_cue))
                snow_cue = bool(vp.get("snow_present", False))
            except Exception:
                pass

        # 2. Vision-Language Geographic Zero-Shot Reranking (StreetCLIP / CLIP ViT-Large)
        # Formulate full candidate country universe: global baseline + hint/script/tld countries
        candidate_countries_set = set(GLOBAL_GEOLOC_COUNTRIES)
        for hc in hint_countries:
            candidate_countries_set.add(hc)
        for sc in script_countries:
            candidate_countries_set.add(sc)
        if tld_country:
            candidate_countries_set.add(tld_country)
        if phone_country:
            candidate_countries_set.add(phone_country)

        country_zero_shot_probs: Dict[str, float] = {}
        if working_image_path and Path(working_image_path).exists() and mock_predictions is None:
            try:
                country_zero_shot_probs = self.score_candidate_countries_zero_shot(
                    image_path=working_image_path,
                    candidate_countries=list(candidate_countries_set),
                )
            except Exception as e:
                logger.warning("[stage2] Country zero-shot scoring failed: %s", e)

        # 3. Determine scene terrain context to bias anchors towards matching biomes
        desired_terrain: Optional[str] = None
        if snow_cue or "conifer" in str(observed_clues).lower():
            desired_terrain = "mountain"
        elif aridity_cue >= 0.5:
            desired_terrain = "desert"

        if clues_file.exists():
            try:
                cdata = json.loads(clues_file.read_text(encoding="utf-8"))
                terr_dict = cdata.get("terrain", {})
                if terr_dict.get("relief") in ("mountainous", "hilly") or terr_dict.get("snow_present"):
                    desired_terrain = "mountain"
                env_m = cdata.get("environmental_meta", {})
                if env_m.get("dominant_flora") == "conifer_forest":
                    desired_terrain = "mountain"
                elif env_m.get("soil_type") == "desert_sand":
                    desired_terrain = "desert"
            except Exception:
                pass

        # 4. Formulate In-Country Candidate Mesh for Continuous Neural Evaluation
        in_country_candidates: List[Dict[str, Any]] = []
        if country_zero_shot_probs and mock_predictions is None:
            top_country, top_prob = next(iter(country_zero_shot_probs.items()))
            if top_prob >= 0.04:
                top_anchors = get_country_anchors(top_country, max_anchors=24, terrain=desired_terrain)
                for a in top_anchors:
                    in_country_candidates.append({
                        "lat": a["lat"],
                        "lon": a["lon"],
                        "name": a["name"],
                        "country": top_country,
                    })

                # If confident top country with bounding box, inject dense spatial grid
                c_key_lower = top_country.lower()
                if top_prob >= 0.15 and c_key_lower in COUNTRY_BBOXES:
                    c_bbox = COUNTRY_BBOXES[c_key_lower]
                    lat_span = c_bbox[2] - c_bbox[0]
                    lon_span = c_bbox[3] - c_bbox[1]
                    grid_n = 15 if max(lat_span, lon_span) > 20.0 else 11
                    lats_g = np.linspace(c_bbox[0], c_bbox[2], grid_n)
                    lons_g = np.linspace(c_bbox[1], c_bbox[3], grid_n)
                    for gla in lats_g:
                        for glo in lons_g:
                            in_country_candidates.append({
                                "lat": float(gla),
                                "lon": float(glo),
                                "name": f"{top_country} Grid ({gla:.2f}, {glo:.2f})",
                                "country": top_country,
                            })

            # Runners-up anchors
            for c_name, c_prob in list(country_zero_shot_probs.items())[1:5]:
                if c_prob >= 0.08:
                    ru_anchors = get_country_anchors(c_name, max_anchors=16, terrain=desired_terrain)
                    for a in ru_anchors:
                        in_country_candidates.append({
                            "lat": a["lat"],
                            "lon": a["lon"],
                            "name": a["name"],
                            "country": c_name,
                        })

            # Discrete cue countries
            cue_countries = list(dict.fromkeys(
                hint_countries + ([tld_country] if tld_country else []) + ([phone_country] if phone_country else []) + script_countries[:3]
            ))
            for cue_c in cue_countries:
                cue_anchors = get_country_anchors(cue_c, max_anchors=16, terrain=desired_terrain)
                for a in cue_anchors:
                    in_country_candidates.append({
                        "lat": a["lat"],
                        "lon": a["lon"],
                        "name": a["name"],
                        "country": cue_c,
                    })

        # 5. Run visual geolocator prior (GeoCLIP with continuous in-country evaluation & HCNGR refinement)
        raw_predictions = self.predict_image_locations(
            image_path=working_image_path,
            top_k=top_k,
            mock_predictions=mock_predictions,
            in_country_candidates=in_country_candidates if in_country_candidates else None,
        )
        raw_predictions_count = len([p for p in raw_predictions if not p.get("anchor_name")])

        # 5b. Fallback Anchor Injection: ensure all key anchors are represented
        existing_coords = {(round(p["lat"], 3), round(p["lon"], 3)) for p in raw_predictions}
        if country_zero_shot_probs:
            top_country, top_prob = next(iter(country_zero_shot_probs.items()))
            if top_prob >= 0.04:
                anchors = get_country_anchors(top_country, max_anchors=16, terrain=desired_terrain)
                anchor_prob = 0.0008
                for a in anchors:
                    c_key = (round(a["lat"], 3), round(a["lon"], 3))
                    if c_key not in existing_coords:
                        existing_coords.add(c_key)
                        raw_predictions.append({
                            "lat": a["lat"],
                            "lon": a["lon"],
                            "prob": anchor_prob,
                            "anchor_name": a["name"],
                            "country": top_country,
                        })

            for c_name, c_prob in list(country_zero_shot_probs.items())[1:5]:
                if c_prob >= 0.08:
                    anchors = get_country_anchors(c_name, max_anchors=10, terrain=desired_terrain)
                    anchor_prob = 0.0006
                    for a in anchors:
                        c_key = (round(a["lat"], 3), round(a["lon"], 3))
                        if c_key not in existing_coords:
                            existing_coords.add(c_key)
                            raw_predictions.append({
                                "lat": a["lat"],
                                "lon": a["lon"],
                                "prob": anchor_prob,
                                "anchor_name": a["name"],
                                "country": c_name,
                            })

            cue_countries = list(dict.fromkeys(hint_countries + ([tld_country] if tld_country else []) + ([phone_country] if phone_country else []) + script_countries[:3]))
            for cue_c in cue_countries:
                cue_anchors = get_country_anchors(cue_c, max_anchors=12, terrain=desired_terrain)
                for a in cue_anchors:
                    c_key = (round(a["lat"], 3), round(a["lon"], 3))
                    if c_key not in existing_coords:
                        existing_coords.add(c_key)
                        a_name = a["name"].lower()
                        is_sub_match = any(sh.lower() in a_name for sh in subnational_hints)
                        raw_predictions.append({
                            "lat": a["lat"],
                            "lon": a["lon"],
                            "prob": 0.0015 if is_sub_match else 0.0008,
                            "anchor_name": a["name"],
                            "country": cue_c,
                        })

        # 6. Fuse evidence for each candidate point
        known_country_mass = sum(country_zero_shot_probs.values()) if country_zero_shot_probs else 0.0
        rem_mass = max(0.0001, 1.0 - known_country_mass)

        scored_points: List[Dict[str, Any]] = []

        for p in raw_predictions:
            lat = p["lat"]
            lon = p["lon"]
            prob = max(1e-12, float(p.get("prob", p.get("score", 1.0))))
            country = get_country_candidate(lat, lon)

            # Hierarchical visual prior: P(point | image) = P(country | image) * P(point | country)
            # Both P(country) and P(point) are globally normalized probabilities.
            if country_zero_shot_probs:
                if country and country in country_zero_shot_probs:
                    c_prob = country_zero_shot_probs[country]
                    joint_prior = c_prob * prob
                elif country:
                    c_prob = country_zero_shot_probs.get(country, 0.0005)
                    joint_prior = c_prob * prob
                else:
                    joint_prior = max(0.0005, rem_mass / 50.0) * prob
                base_log_prior = math.log(max(1e-12, joint_prior))
                reranker_lr = 0.0
            else:
                base_log_prior = math.log(prob)
                reranker_lr = 0.00

            climate_info = self.climate.get_climate_classification(lat, lon)
            koeppen = climate_info.get("code", "C")

            aridity_tag = "arid" if aridity_cue > 0.5 else ("humid" if veg_cue > 0.5 else None)
            veg_density = "none" if veg_cue < 0.2 else ("dense" if veg_cue > 0.6 else None)
            comp_score = self.climate.score_compatibility(
                lat, lon,
                aridity_cue=aridity_tag,
                snow_present=snow_cue,
                vegetation_density=veg_density,
            )
            climate_lr = math.log(max(0.01, comp_score))

            # Positive boost for desert match, severe penalty for polar/taiga/boreal in arid photo
            if aridity_cue > 0.6:
                if climate_info.get("group") == "B":
                    climate_lr += 3.0
                elif climate_info.get("group") in ("D", "E") or is_in_region(lat, lon, "scandinavia"):
                    climate_lr -= 14.0

            # Hint alignment
            hint_lr = 0.0
            if hint_countries:
                if country and any(hc.lower() in country.lower() for hc in hint_countries):
                    hint_lr = 3.5
                else:
                    hint_lr = -2.5

            # Subnational Division (ADMIN1) alignment (Picarta & GeoSpy state conditioning)
            subnational_lr = 0.0
            if subnational_hints:
                cand_subdiv = get_subnational_division(lat, lon)
                if cand_subdiv:
                    cand_div_str = str(cand_subdiv).lower()
                    matched_sub = any(
                        sh.lower() in cand_div_str or cand_div_str in sh.lower()
                        for sh in subnational_hints
                    )
                    if matched_sub:
                        subnational_lr += 4.5
                    elif country and any(hc.lower() in country.lower() for hc in hint_countries):
                        subnational_lr -= 3.0
                else:
                    if country and any(hc.lower() in country.lower() for hc in hint_countries):
                        subnational_lr -= 1.5

            # Distance radius constraint (Picarta radius parameter)
            radius_lr = 0.0
            if center_coords_hint and radius_km_hint:
                dist_to_center = haversine_distance_km(lat, lon, center_coords_hint[0], center_coords_hint[1])
                if dist_to_center <= radius_km_hint:
                    radius_lr += 3.5
                else:
                    radius_lr -= 12.0

            # Driving side alignment
            driving_lr = 0.0
            if driving_cue and country:
                country_side = lookup_driving_side(country)
                if country_side and country_side != driving_cue:
                    driving_lr = -4.5

            # Geoguessr meta log-likelihood adjustment
            meta_lr = 0.0
            if script_countries and country:
                if any(sc.lower() in country.lower() for sc in script_countries):
                    meta_lr += 2.5
                elif country_zero_shot_probs.get(country, 0.0) < 0.15:
                    meta_lr -= 1.5

            if tld_country and country:
                if tld_country.lower() in country.lower():
                    meta_lr += 6.0
                else:
                    meta_lr -= 4.0

            if phone_country and country:
                if phone_country.lower() in country.lower():
                    meta_lr += 5.0
                else:
                    meta_lr -= 3.0

            # 4b. Solar Hemispheric Likelihood Adjustment
            solar_meta = board.data.get("solar_meta", {})
            solar_lr = 0.0
            if solar_meta and solar_meta.get("confidence", 0.0) >= 0.65:
                sh = solar_meta.get("hemisphere")
                if sh == "northern":
                    if lat < -12.0:
                        solar_lr = -12.0
                    elif lat >= 15.0:
                        solar_lr = 1.0
                elif sh == "southern":
                    if lat > 12.0:
                        solar_lr = -12.0
                    elif lat <= -15.0:
                        solar_lr = 1.0

            # 4c. Environmental Meta (Soil, Flora, Plates, Road infrastructure)
            env_meta = board.data.get("environmental_meta", {})
            env_lr = 0.0
            if env_meta:
                soil = env_meta.get("soil_type")
                flora = env_meta.get("dominant_flora")
                plate = env_meta.get("plate_style")
                curb = env_meta.get("curb_style")

                if soil == "red_laterite":
                    if country in ("India", "Brazil", "Australia", "Pakistan"):
                        env_lr += 2.0
                    elif lat > 45.0:
                        env_lr -= 4.0
                elif soil == "desert_sand":
                    if country in ("Saudi Arabia", "United Arab Emirates", "Egypt", "Oman", "Qatar", "Kuwait", "Morocco", "Algeria", "Tunisia", "Jordan", "Australia", "United States"):
                        env_lr += 2.5
                    elif climate_info.get("group") in ("D", "E", "C") and not (country in ("Morocco", "Jordan", "Australia", "United States") and climate_info.get("group") == "C"):
                        env_lr -= 3.0

                if flora == "date_palm":
                    if country in ("United Arab Emirates", "Saudi Arabia", "Egypt", "Oman", "Iraq", "Pakistan", "Morocco", "Algeria", "Tunisia"):
                        env_lr += 2.0
                    elif lat > 42.0:
                        env_lr -= 4.0
                elif flora == "olive_groves":
                    if country in ("Greece", "Italy", "Spain", "Turkey", "Israel", "Syria", "Morocco", "Tunisia", "Jordan", "Portugal"):
                        env_lr += 2.5
                    elif lat > 46.0 or lat < 20.0:
                        env_lr -= 3.0

                if curb == "black_yellow" and country in ("Pakistan", "India", "United Kingdom", "Kenya"):
                    env_lr += 2.0
                if plate == "yellow_rear" and country in ("United Kingdom", "Israel", "Netherlands", "Cyprus", "Kenya"):
                    env_lr += 3.5
                elif plate == "eu_blue_band" and country in ("Germany", "France", "Italy", "Spain", "Turkey", "Poland", "Czech Republic", "Czechia", "Romania", "Hungary", "Bulgaria", "Finland", "Sweden", "Ireland", "Portugal"):
                    env_lr += 3.0
                elif plate == "commercial_yellow" and country in ("India", "Pakistan"):
                    env_lr += 3.0

            # 4d. Co-Pilot / User Hints Constraints (Exclusions & Terrain filters)
            uh = board.data.get("user_hints", {})
            excluded_countries = board.data.get("co_pilot", {}).get("excluded_countries") or uh.get("excluded_countries", [])
            terrain_filter = board.data.get("co_pilot", {}).get("terrain_filter") or uh.get("terrain_filter")

            copilot_lr = 0.0
            if country and excluded_countries:
                if any(ec.lower() in country.lower() for ec in excluded_countries):
                    copilot_lr = -999.0

            if terrain_filter:
                tf = str(terrain_filter).lower()
                if tf == "mountain" and (climate_info.get("group") == "E" or abs(lat) > 30.0):
                    copilot_lr += 2.5
                elif tf == "desert" and climate_info.get("group") == "B":
                    copilot_lr += 3.0
                elif tf == "coast" and country:
                    copilot_lr += 1.5

            combined_score = (
                base_log_prior + climate_lr + hint_lr + driving_lr + meta_lr
                + reranker_lr + solar_lr + env_lr + copilot_lr + subnational_lr + radius_lr
            )

            scored_points.append({
                "lat": lat,
                "lon": lon,
                "prob": prob,
                "base_log_prior": base_log_prior,
                "country": country,
                "koeppen": koeppen,
                "climate_lr": climate_lr,
                "hint_lr": hint_lr,
                "subnational_lr": subnational_lr,
                "radius_lr": radius_lr,
                "driving_lr": driving_lr,
                "meta_lr": meta_lr,
                "solar_lr": solar_lr,
                "env_lr": env_lr,
                "copilot_lr": copilot_lr,
                "reranker_lr": reranker_lr,
                "country_zero_shot_prob": country_zero_shot_probs.get(country, 0.0) if country else 0.0,
                "anchor_name": p.get("anchor_name"),
                "score": combined_score,
            })

        # 4. Cluster scored points into candidate spatial cells / search bounding boxes
        clusters = cluster_points(scored_points, radius_km=75.0, max_clusters=15)

        # Compute normalized softmax probabilities across clusters
        if clusters:
            max_s = max(c["best_score"] for c in clusters)
            exp_scores = [math.exp(min(50.0, c["best_score"] - max_s)) for c in clusters]
            sum_exp = sum(exp_scores)
            for i, c in enumerate(clusters):
                c["cluster_prob"] = exp_scores[i] / sum_exp if sum_exp > 0 else (1.0 / len(clusters))

        # 5. Update Candidate Board
        cid_geoclip = board.add_clue(
            text=f"GeoCLIP global visual prior evaluated ({len(raw_predictions)} raw predictions)",
            kind="prior",
            status="observed",
        )

        cid_climate = board.add_clue(
            text=f"Köppen climate & biome raster filtering (aridity cue={aridity_cue:.2f}, veg cue={veg_cue:.2f})",
            kind="climate",
            status="observed",
        )

        cid_reranker = None
        if country_zero_shot_probs:
            top_ranked = list(country_zero_shot_probs.items())[:3]
            top_str = ", ".join(f"{c}: {p*100:.1f}%" for c, p in top_ranked)
            cid_reranker = board.add_clue(
                text=f"Zero-shot geographic vision-language reranking ({top_str})",
                kind="reranker",
                status="observed",
                confidence=0.92,
            )

        search_bboxes: List[Dict[str, Any]] = []

        for c in clusters:
            anchor_lbl = ""
            for pt in c.get("points", []):
                if pt.get("anchor_name"):
                    anchor_lbl = f" - {pt['anchor_name']}"
                    break
            subdiv = get_subnational_division(c["center_lat"], c["center_lon"])
            subdiv_lbl = f", {subdiv}" if subdiv else ""
            cand_name = f"Cell {c['cluster_id']}: {c['country'] or 'Open Region'}{subdiv_lbl}{anchor_lbl} ({c['center_lat']:.2f}, {c['center_lon']:.2f})"
            bbox = [round(c["min_lat"], 4), round(c["min_lon"], 4), round(c["max_lat"], 4), round(c["max_lon"], 4)]
            board.add_candidate(
                name=cand_name,
                level="cell",
                prior=c["cluster_prob"],
                bbox=bbox,
                lat=c["center_lat"],
                lon=c["center_lon"],
                metadata={
                    "country": c.get("country"),
                    "subnational_division": subdiv,
                },
            )

            # Add evidence linking clues to candidate
            board.add_evidence(
                clue_id=cid_geoclip,
                candidate_weights={cand_name: math.exp(min(1.5, c["best_score"] / 10.0))},
                rationale="Visual embedding similarity from GeoCLIP",
            )
            if cid_reranker and country_zero_shot_probs:
                top_country, top_prob = next(iter(country_zero_shot_probs.items()))
                c_country = c.get("country")
                c_zs_prob = country_zero_shot_probs.get(c_country, 0.0) if c_country else 0.0
                if c_zs_prob >= 0.10:
                    weight = min(3.0, 1.0 + 3.0 * (c_zs_prob / max(0.1, top_prob)))
                elif c_zs_prob < 0.03 and top_prob >= 0.20:
                    weight = 0.33
                else:
                    weight = max(0.5, 1.0 + (c_zs_prob - 0.1))
                board.add_evidence(
                    clue_id=cid_reranker,
                    candidate_weights={cand_name: weight},
                    rationale=f"Zero-shot vision-language country likelihood ({c_country}: {c_zs_prob*100:.1f}%)",
                )

            search_bboxes.append({
                "cluster_id": c["cluster_id"],
                "candidate_name": cand_name,
                "country": c["country"],
                "subnational_division": subdiv,
                "bbox": bbox,
                "center": [c["center_lat"], c["center_lon"]],
                "score": c["best_score"],
                "probability": c.get("cluster_prob", 0.0),
            })

        # 5b. Geographically Validate Point / Sign Candidates Against Visual Prior Clusters
        # Reject false homonyms (e.g. a street in France when visual prior is in Pakistan)
        corroborated_point_bboxes = []
        raw_cands = board.data.get("candidates", {})
        cand_list = list(raw_cands.values()) if isinstance(raw_cands, dict) else list(raw_cands)
        for cand in cand_list:
            if isinstance(cand, dict) and cand.get("lat") is not None and cand.get("lon") is not None:
                if cand.get("level") == "point" or "sign" in cand.get("name", "").lower():
                    p_lat = float(cand["lat"])
                    p_lon = float(cand["lon"])
                    
                    # Compute minimum distance to any top visual prior cluster
                    min_dist_km = 99999.0
                    if clusters:
                        for c in clusters[:5]:
                            d = haversine_distance_km(p_lat, p_lon, c["center_lat"], c["center_lon"])
                            if d < min_dist_km:
                                min_dist_km = d
                    else:
                        min_dist_km = 0.0

                    # Check user hints for country match
                    c_cand_country = cand.get("metadata", {}).get("country") or get_country_candidate(p_lat, p_lon)
                    hint_match = False
                    if hint_countries:
                        if c_cand_country and any(hc.lower() in c_cand_country.lower() for hc in hint_countries):
                            hint_match = True

                    top_cluster_country = clusters[0]["country"] if clusters else None
                    top_cluster_prob = clusters[0].get("cluster_prob", 0.0) if clusters else 0.0

                    country_conflict = False
                    if top_cluster_country and c_cand_country and top_cluster_prob >= 0.50:
                        if top_cluster_country.lower() != c_cand_country.lower():
                            country_conflict = True

                    # Accept point candidates within 150 km of visual prior clusters without cross-country contradiction,
                    # or explicitly matching ground truth user hint, or high-confidence T1 architectural monuments.
                    # Unhinted generic T2/T3 natural features (e.g. dunes, basins) must be corroborated within 150 km.
                    is_landmark_source = cand.get("metadata", {}).get("source") in ("landmark_matcher", "landmark_hint")
                    is_t1_landmark = is_landmark_source and cand.get("metadata", {}).get("tier") == "T1"
                    is_landmark_hint = cand.get("metadata", {}).get("source") == "landmark_hint"

                    if ((min_dist_km <= 150.0 and not country_conflict) or hint_match or is_landmark_hint or is_t1_landmark):
                        g_bbox = cand.get("bbox") or [p_lat - 0.05, p_lon - 0.05, p_lat + 0.05, p_lon + 0.05]
                        cand_subdiv = get_subnational_division(p_lat, p_lon)
                        corroborated_point_bboxes.append({
                            "cluster_id": "verified_point",
                            "candidate_name": cand["name"],
                            "country": c_cand_country,
                            "subnational_division": cand_subdiv,
                            "bbox": g_bbox,
                            "center": [p_lat, p_lon],
                            "score": 10.0,
                            "probability": 0.90,
                        })
                        logger.info("[stage2_prior] Point candidate '%s' corroborated by visual prior (dist=%.1f km, subdiv=%s)", cand["name"], min_dist_km, cand_subdiv)
                    else:
                        logger.warning(
                            "[stage2_prior] Pruned contradictory point candidate '%s' at (%.2f, %.2f) (%.1f km away from visual prior, country=%s, conflict=%s)",
                            cand["name"], p_lat, p_lon, min_dist_km, c_cand_country, country_conflict
                        )
                        # Penalize candidate on board so it does not win
                        cand["prior"] = 0.0001
                        cand["score"] = -20.0

        board.data["search_bboxes"] = corroborated_point_bboxes + search_bboxes
        board.data["stages_run"].append("stage2_prior")
        board.save(job_dir / "board.json")

        # 6. Save prior artifact
        summary = {
            "total_raw_predictions": raw_predictions_count,
            "total_candidate_points": len(raw_predictions),
            "clusters_count": len(clusters),
            "top_clusters": search_bboxes[:5],
            "top_points": scored_points[:10],
            "aridity_cue": aridity_cue,
            "veg_cue": veg_cue,
            "snow_cue": snow_cue,
            "zero_shot_country_probs": dict(list(country_zero_shot_probs.items())[:5]),
        }

        prior_results_path = job_dir / "prior_results.json"
        prior_results_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        logger.info("Stage 2 Prior completed: %d clusters generated, top cluster: %s",
                    len(clusters), clusters[0]["cluster_id"] if clusters else "None")

        return summary, board
