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
GLOBAL_GEOLOC_COUNTRIES: List[str] = [
    # South & Central Asia
    "Pakistan", "India", "Bangladesh", "Nepal", "Sri Lanka", "Afghanistan",
    "Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan",
    # Middle East & North Africa
    "Iran", "Iraq", "Turkey", "Saudi Arabia", "United Arab Emirates", "Israel",
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
                    
                    prompts = [f"a photo taken in {c}" for c in unique_countries]
                    inputs = processor(text=prompts, images=im, return_tensors="pt", padding=True).to(device)
                    with torch.no_grad():
                        outputs = model(**inputs)
                        probs = outputs.logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                    
                    scored = {c: float(p) for c, p in zip(unique_countries, probs)}
                    sorted_scored = dict(sorted(scored.items(), key=lambda kv: kv[1], reverse=True))
                    logger.info("[stage2] Zero-shot geographic ranking: %s", 
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
    ) -> List[Dict[str, float]]:
        """Run GeoCLIP inference with batched multi-crop spatial pooling."""
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
                        # Multi-crop ensemble: full, center 80%, left 65%, right 65%
                        crop_full = im
                        crop_center = im.crop((int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)))
                        crop_left = im.crop((0, 0, int(w * 0.65), h))
                        crop_right = im.crop((int(w * 0.35), 0, w, h))
                        crops = [crop_full, crop_center, crop_left, crop_right]
                    else:
                        crops = [im]

                    # Ensure model device
                    m_dev = next(model.parameters()).device
                    tensors = [model.image_encoder.preprocess_image(c) for c in crops]
                    batch = torch.cat(tensors, dim=0).to(m_dev)
                    gps_gal = model.gps_gallery.to(m_dev)

                    with torch.no_grad():
                        logits = model.forward(batch, gps_gal)
                        probs = logits.softmax(dim=-1).mean(dim=0, keepdim=True)
                        top_pred = torch.topk(probs, min(top_k, gps_gal.shape[0]), dim=1)
                        coords_np = gps_gal.index_select(0, top_pred.indices[0]).cpu().numpy()
                        probs_np = top_pred.values[0].cpu().numpy()

                for i in range(len(coords_np)):
                    predictions.append({
                        "lat": float(coords_np[i][0]),
                        "lon": float(coords_np[i][1]),
                        "prob": float(probs_np[i]),
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

        logger.info("Stage 2 Prior: running image geolocator on %s", working_image_path)

        # 1. Run visual geolocator prior (GeoCLIP)
        raw_predictions = self.predict_image_locations(
            image_path=working_image_path,
            top_k=top_k,
            mock_predictions=mock_predictions,
        )
        raw_predictions_count = len(raw_predictions)

        # 2. Extract perception cues and user hints from board
        observed_clues = board.data.get("clues", {})
        aridity_cue = 0.0
        veg_cue = 0.5
        snow_cue = False
        driving_cue: Optional[str] = None
        hint_countries: List[str] = []
        script_countries: List[str] = []
        tld_country: Optional[str] = None
        phone_country: Optional[str] = None

        for cid, cinfo in observed_clues.items():
            kind = cinfo.get("kind")
            text = cinfo.get("text", "")
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

        # 3. Vision-Language Geographic Zero-Shot Reranking (StreetCLIP / CLIP ViT-Large)
        # Formulate full candidate country universe: global baseline + observed GeoCLIP/hint countries
        candidate_countries_set = set(GLOBAL_GEOLOC_COUNTRIES)
        for p in raw_predictions[:25]:
            c_name = get_country_candidate(p["lat"], p["lon"])
            if c_name:
                candidate_countries_set.add(c_name)
        for hc in hint_countries:
            candidate_countries_set.add(hc)
        for sc in script_countries:
            candidate_countries_set.add(sc)
        if tld_country:
            candidate_countries_set.add(tld_country)
        if phone_country:
            candidate_countries_set.add(phone_country)

        country_zero_shot_probs: Dict[str, float] = {}
        if working_image_path and Path(working_image_path).exists():
            try:
                country_zero_shot_probs = self.score_candidate_countries_zero_shot(
                    image_path=working_image_path,
                    candidate_countries=list(candidate_countries_set),
                )
            except Exception as e:
                logger.warning("[stage2] Country zero-shot scoring failed: %s", e)

        # 3b. High-Probability Country Anchor Injection
        # If the visual reranker strongly predicts a country that has sparse coverage in GeoCLIP's gallery,
        # inject regional urban/corridor anchors so the region can be actively evaluated across all evidence.
        if country_zero_shot_probs:
            top_country, top_prob = next(iter(country_zero_shot_probs.items()))
            rep_count = sum(1 for p in raw_predictions if (get_country_candidate(p["lat"], p["lon"]) or "").lower() == top_country.lower())
            if rep_count < 3 and top_prob >= 0.05:
                anchors = get_country_anchors(top_country, max_anchors=6)
                if anchors:
                    logger.info("[stage2] Injecting %d regional anchors for top zero-shot country '%s' (prob=%.2f%%)", len(anchors), top_country, top_prob * 100)
                    anchor_prob = max(0.015, top_prob / len(anchors))
                    for a in anchors:
                        raw_predictions.append({
                            "lat": a["lat"],
                            "lon": a["lon"],
                            "prob": anchor_prob,
                            "anchor_name": a["name"],
                            "country": top_country,
                        })

            for c_name, c_prob in list(country_zero_shot_probs.items())[1:3]:
                if c_prob >= 0.15:
                    c_rep = sum(1 for p in raw_predictions if (get_country_candidate(p["lat"], p["lon"]) or "").lower() == c_name.lower())
                    if c_rep < 2:
                        anchors = get_country_anchors(c_name, max_anchors=3)
                        anchor_prob = max(0.01, c_prob / max(1, len(anchors)))
                        for a in anchors:
                            raw_predictions.append({
                                "lat": a["lat"],
                                "lon": a["lon"],
                                "prob": anchor_prob,
                                "anchor_name": a["name"],
                                "country": c_name,
                            })

        # 4. Fuse evidence for each candidate point
        country_raw_mass: Dict[str, float] = {}
        for p in raw_predictions:
            c_name = get_country_candidate(p["lat"], p["lon"]) or "Other"
            country_raw_mass[c_name] = country_raw_mass.get(c_name, 0.0) + p.get("prob", 0.0)

        scored_points: List[Dict[str, Any]] = []

        for p in raw_predictions:
            lat = p["lat"]
            lon = p["lon"]
            prob = max(1e-12, p["prob"])
            country = get_country_candidate(lat, lon)

            # Hierarchical visual prior: P(point | image) = P(country | image) * P(point | country)
            # This cleanly debiases GeoCLIP's gallery density differences across nations.
            if country and country_zero_shot_probs:
                c_prob = country_zero_shot_probs.get(country, 0.0001)
                c_mass = max(1e-6, country_raw_mass.get(country, 1.0))
                p_cond = prob / c_mass
                joint_prior = c_prob * p_cond
                base_log_prior = math.log(max(1e-12, joint_prior))
                reranker_lr = 0.0
            else:
                base_log_prior = math.log(prob)
                reranker_lr = 0.0

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
                    meta_lr += 3.5
                else:
                    meta_lr -= 3.0

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

            combined_score = base_log_prior + climate_lr + hint_lr + driving_lr + meta_lr + reranker_lr

            scored_points.append({
                "lat": lat,
                "lon": lon,
                "prob": prob,
                "base_log_prior": base_log_prior,
                "country": country,
                "koeppen": koeppen,
                "climate_lr": climate_lr,
                "hint_lr": hint_lr,
                "driving_lr": driving_lr,
                "meta_lr": meta_lr,
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
            cand_name = f"Cell {c['cluster_id']}: {c['country'] or 'Open Region'}{anchor_lbl} ({c['center_lat']:.2f}, {c['center_lon']:.2f})"
            bbox = [round(c["min_lat"], 4), round(c["min_lon"], 4), round(c["max_lat"], 4), round(c["max_lon"], 4)]
            board.add_candidate(
                name=cand_name,
                level="cell",
                prior=c["cluster_prob"],
                bbox=bbox,
                lat=c["center_lat"],
                lon=c["center_lon"],
            )

            # Add evidence linking clues to candidate
            board.add_evidence(
                clue_id=cid_geoclip,
                candidate_weights={cand_name: math.exp(min(1.5, c["best_score"] / 10.0))},
                rationale="Visual embedding similarity from GeoCLIP",
            )
            if cid_reranker and c.get("country") in country_zero_shot_probs:
                c_zs_prob = country_zero_shot_probs[c["country"]]
                board.add_evidence(
                    clue_id=cid_reranker,
                    candidate_weights={cand_name: 1.0 + 3.0 * c_zs_prob},
                    rationale=f"Zero-shot vision-language country likelihood ({c_zs_prob*100:.1f}%)",
                )

            search_bboxes.append({
                "cluster_id": c["cluster_id"],
                "candidate_name": cand_name,
                "country": c["country"],
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
                    hint_match = False
                    if hint_countries:
                        c_cand_country = cand.get("metadata", {}).get("country") or get_country_candidate(p_lat, p_lon)
                        if c_cand_country and any(hc.lower() in c_cand_country.lower() for hc in hint_countries):
                            hint_match = True

                    # Only accept point candidates within 800 km of visual prior clusters or matching user hint
                    if min_dist_km <= 800.0 or hint_match:
                        g_bbox = cand.get("bbox") or [p_lat - 0.05, p_lon - 0.05, p_lat + 0.05, p_lon + 0.05]
                        corroborated_point_bboxes.append({
                            "cluster_id": "verified_point",
                            "candidate_name": cand["name"],
                            "country": cand.get("metadata", {}).get("country") or get_country_candidate(p_lat, p_lon),
                            "bbox": g_bbox,
                            "center": [p_lat, p_lon],
                            "score": 10.0,
                            "probability": 0.90,
                        })
                        logger.info("[stage2_prior] Point candidate '%s' corroborated by visual prior (dist=%.1f km)", cand["name"], min_dist_km)
                    else:
                        logger.warning(
                            "[stage2_prior] Pruned contradictory point candidate '%s' at (%.2f, %.2f) (%.1f km away from visual prior)",
                            cand["name"], p_lat, p_lon, min_dist_km
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
