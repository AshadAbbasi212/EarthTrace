"""Stage 2: Global Prior & Biome Candidate Generation."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
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

        # 3. Fuse evidence for each candidate point
        scored_points: List[Dict[str, Any]] = []

        for p in raw_predictions:
            lat = p["lat"]
            lon = p["lon"]
            prob = max(1e-12, p["prob"])
            base_log_prior = math.log(prob)

            country = get_country_candidate(lat, lon)
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

            combined_score = base_log_prior + climate_lr + hint_lr + driving_lr + meta_lr

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

        search_bboxes: List[Dict[str, Any]] = []

        for c in clusters:
            cand_name = f"Cell {c['cluster_id']}: {c['country'] or 'Open Region'} ({c['center_lat']:.2f}, {c['center_lon']:.2f})"
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

            search_bboxes.append({
                "cluster_id": c["cluster_id"],
                "candidate_name": cand_name,
                "country": c["country"],
                "bbox": bbox,
                "center": [c["center_lat"], c["center_lon"]],
                "score": c["best_score"],
                "probability": c.get("cluster_prob", 0.0),
            })

        # Check if high-confidence geocoded sign candidates exist from Stage 1
        geocoded_bboxes = []
        raw_cands = board.data.get("candidates", {})
        cand_list = list(raw_cands.values()) if isinstance(raw_cands, dict) else list(raw_cands)
        for cand in cand_list:
            if isinstance(cand, dict) and cand.get("level") in ("point", "city") and cand.get("lat") is not None and "sign" in cand.get("name", "").lower():
                p_lat = cand["lat"]
                p_lon = cand["lon"]
                g_bbox = cand.get("bbox") or [p_lat - 0.05, p_lon - 0.05, p_lat + 0.05, p_lon + 0.05]
                geocoded_bboxes.append({
                    "cluster_id": "geocoded_sign",
                    "candidate_name": cand["name"],
                    "country": cand.get("metadata", {}).get("country"),
                    "bbox": g_bbox,
                    "center": [p_lat, p_lon],
                    "score": 10.0,
                    "probability": 0.95,
                })

        board.data["search_bboxes"] = geocoded_bboxes + search_bboxes
        board.data["stages_run"].append("stage2_prior")
        board.save()

        # 6. Save prior artifact
        summary = {
            "total_raw_predictions": len(raw_predictions),
            "clusters_count": len(clusters),
            "top_clusters": search_bboxes[:5],
            "top_points": scored_points[:10],
            "aridity_cue": aridity_cue,
            "veg_cue": veg_cue,
            "snow_cue": snow_cue,
        }

        prior_results_path = job_dir / "prior_results.json"
        prior_results_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        logger.info("Stage 2 Prior completed: %d clusters generated, top cluster: %s",
                    len(clusters), clusters[0]["cluster_id"] if clusters else "None")

        return summary, board
