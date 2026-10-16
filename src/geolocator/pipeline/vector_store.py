"""Landmark Vector Store: Precomputed CLIP Embeddings Search Engine.

Enables sub-millisecond similarity matching across hundreds of cities and thousands
of landmark prompts without GPU TDR watchdog timeouts. Supports semantic category
compatibility filtering, negative background prompt rejection, and country consistency gating.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
from PIL import Image

logger = logging.getLogger("geolocator.pipeline.vector_store")

NATURAL_SCENES = {"mountain", "wilderness", "desert", "coastal", "rural"}
BUILDING_CATEGORIES = {
    "university_campus",
    "educational_campus",
    "hospital_complex",
    "civic_building",
    "civic_market",
    "shopping_mall",
    "commercial_towers",
    "commercial_market",
    "commercial_district",
    "luxury_hotel",
    "hotel",
    "sports_club",
    "government",
    "embassy",
    "embassy_zone",
}


class LandmarkVectorStore:
    """Ultra-fast offline vector store for landmarks across all target cities."""

    _instance: Optional["LandmarkVectorStore"] = None

    def __init__(self, data_dir: Optional[Path | str] = None):
        self.data_dir = Path(data_dir or "data/landmarks")
        self.embeddings_path = self.data_dir / "landmarks_embeddings.pt"
        self.index_path = self.data_dir / "landmarks_index.json"
        self.embeddings: Optional[torch.Tensor] = None
        self.metadata: List[Dict[str, Any]] = []
        self.num_landmarks_prompts: int = 0
        self.num_negatives: int = 0
        self._is_loaded = False
        self._load()

    @classmethod
    def get_instance(cls, data_dir: Optional[Path | str] = None) -> "LandmarkVectorStore":
        if cls._instance is None:
            cls._instance = LandmarkVectorStore(data_dir)
        return cls._instance

    def _load(self):
        """Load precomputed embeddings tensor and metadata index."""
        if not self.embeddings_path.exists() or not self.index_path.exists():
            logger.warning("[vector_store] Precomputed embeddings not found at %s. Store uninitialized.", self.embeddings_path)
            return

        try:
            self.embeddings = torch.load(self.embeddings_path, map_location="cpu", weights_only=True)
            index_data = json.loads(self.index_path.read_text(encoding="utf-8"))
            self.metadata = index_data.get("metadata", [])
            self.num_landmarks_prompts = index_data.get("num_landmarks_prompts", len(self.metadata))
            self.num_negatives = index_data.get("num_negatives", 0)
            self._is_loaded = True
            logger.info(
                "[vector_store] Loaded %d prompt embeddings (tensor shape %s) with %d landmarks and %d negative prompts.",
                len(self.metadata), self.embeddings.shape, self.num_landmarks_prompts, self.num_negatives
            )
        except Exception as e:
            logger.error("[vector_store] Failed to load embeddings: %s", e)
            self._is_loaded = False

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and self.embeddings is not None and len(self.metadata) > 0

    def search(
        self,
        image_embedding: torch.Tensor,
        candidate_countries: Optional[List[str]] = None,
        scene_type: Optional[str] = None,
        has_buildings: Optional[bool] = None,
        logit_scale: float = 100.0,
        min_confidence: float = 0.35,
    ) -> Optional[Dict[str, Any]]:
        """Run vector similarity match against landmark database.

        Args:
            image_embedding: (1, D) normalized float32 tensor of query image.
            candidate_countries: Optional country hints or priors.
            scene_type: Scene type from clue extraction (e.g. 'mountain', 'urban').
            has_buildings: Boolean indicating whether prominent buildings were detected.
            logit_scale: CLIP logit scale factor (typically ~100).
            min_confidence: Minimum total probability threshold.

        Returns:
            Dict containing canonical landmark metadata, or None if rejected.
        """
        if not self.is_ready:
            logger.warning("[vector_store] Search requested but vector store is not ready.")
            return None

        # Normalize image embedding and move to same device as embeddings
        im_emb = image_embedding.detach().cpu()
        if im_emb.dim() == 1:
            im_emb = im_emb.unsqueeze(0)
        im_emb = torch.nn.functional.normalize(im_emb, dim=1)

        # 1. Cosine similarity & softmax logits across all prompts
        similarities = (im_emb @ self.embeddings.t())[0]  # Shape: (N,)
        logits = logit_scale * similarities
        probs = logits.softmax(dim=-1).numpy()

        # 2. Extract negative background probabilities
        landmark_probs = probs[:self.num_landmarks_prompts]
        neg_probs = probs[self.num_landmarks_prompts:]
        max_neg_prob = float(np.max(neg_probs)) if len(neg_probs) > 0 else 0.0

        # 3. Aggregate probabilities across prompt variants by canonical landmark
        canonical_map: Dict[str, Dict[str, Any]] = {}
        for i in range(self.num_landmarks_prompts):
            meta = self.metadata[i]
            c_name = meta["name"]
            if c_name not in canonical_map:
                canonical_map[c_name] = {
                    "name": c_name,
                    "city": meta.get("city", ""),
                    "country": meta.get("country", ""),
                    "category": meta.get("category", "landmark"),
                    "latitude": meta["latitude"],
                    "longitude": meta["longitude"],
                    "radius_km": meta.get("radius_km", 0.05),
                    "total_prob": 0.0,
                    "max_prob": 0.0,
                    "best_prompt": meta.get("prompt", ""),
                }
            p = float(landmark_probs[i])
            canonical_map[c_name]["total_prob"] += p
            if p > canonical_map[c_name]["max_prob"]:
                canonical_map[c_name]["max_prob"] = p
                canonical_map[c_name]["best_prompt"] = meta.get("prompt", "")

        # 4. Semantic Category Compatibility Filtering:
        # If scene is natural wilderness (e.g. mountain, desert) and no buildings detected,
        # strictly reject architectural/campus categories (like university campus, hotel, civic buildings).
        valid_candidates = []
        for c_name, data in canonical_map.items():
            if scene_type in NATURAL_SCENES and has_buildings is False:
                if data["category"] in BUILDING_CATEGORIES:
                    logger.debug(
                        "[vector_store] Excluding '%s' (%s) due to natural scene_type=%s and has_buildings=False",
                        c_name, data["category"], scene_type
                    )
                    continue
            valid_candidates.append(data)

        if not valid_candidates:
            return None

        valid_candidates.sort(key=lambda x: x["total_prob"], reverse=True)
        top_cand = valid_candidates[0]
        top_prob = top_cand["total_prob"]

        # Reject if top candidate is weaker than highest negative background prompt
        if top_prob < max_neg_prob:
            logger.info(
                "[vector_store] Negative background exceeded top landmark '%s' (top_prob=%.4f < max_neg=%.4f)",
                top_cand["name"], top_prob, max_neg_prob
            )
            return None

        neg_margin = top_prob - max_neg_prob
        second_prob = valid_candidates[1]["total_prob"] if len(valid_candidates) > 1 else 0.0
        lm_margin = top_prob - second_prob

        logger.info(
            "[vector_store] Candidate match: '%s' in %s, %s (conf=%.4f, lm_margin=%.4f, neg_margin=%.4f, max_neg=%.4f)",
            top_cand["name"], top_cand["city"], top_cand["country"], top_prob, lm_margin, neg_margin, max_neg_prob
        )

        # 5. Significance thresholds calibrated for 900+ multi-class zero-shot distribution
        # Base random chance across 903 prompts is ~0.0011 (0.11%).
        # A top probability of >= 0.18 is > 150x random chance.
        is_significant = (
            (top_prob >= 0.35 and neg_margin >= 0.10)
            or (top_prob >= 0.20 and lm_margin >= 0.05 and neg_margin >= 0.10)
            or (top_prob >= 0.15 and lm_margin >= 0.04 and neg_margin >= 0.10 and max_neg_prob < 0.01)
        )
        if not is_significant:
            logger.info(
                "[vector_store] Match '%s' rejected (failed significance: prob=%.4f, lm_margin=%.4f, neg_margin=%.4f, max_neg=%.4f)",
                top_cand["name"], top_prob, lm_margin, neg_margin, max_neg_prob
            )
            return None

        # 6. Country consistency verification
        lm_country = top_cand.get("country", "")
        if not lm_country:
            from geolocator.pipeline.geo_utils import get_country_candidate
            lm_country = get_country_candidate(top_cand["latitude"], top_cand["longitude"]) or ""

        if candidate_countries:
            norm_cand_countries = [c.strip().lower() for c in candidate_countries if c.strip()]
            lm_text = f"{top_cand['best_prompt']} {top_cand['name']} {top_cand.get('city', '')} {lm_country}".lower()
            country_matched = any(c in lm_text for c in norm_cand_countries)
            if not country_matched and top_prob < 0.90:
                logger.info(
                    "[vector_store] Match '%s' rejected due to country mismatch with candidate countries %s (conf=%.4f < 0.90)",
                    top_cand["name"], candidate_countries, top_prob
                )
                return None

        category = top_cand["category"]
        canonical_name = top_cand["name"]
        city = top_cand.get("city", "")
        lat = top_cand["latitude"]
        lon = top_cand["longitude"]

        # Calibrated error radius based on category
        if category in ("monument", "national_monument", "fortress", "unesco_world_heritage", "world_landmark", "landmark_building", "cathedral", "grand_mosque", "national_mosque", "historical_mosque", "palace", "historical_palace", "museum", "university_campus", "hospital_complex", "civic_building", "civic_market", "luxury_hotel", "hotel", "sports_club", "hospitality", "natural_landmark", "urban_landmark", "aircraft_monument", "military_monument", "shrine", "historical_shrine", "historical_temple", "temple", "historical_church", "shopping_mall", "commercial_towers"):
            calibrated_radius_km = float(top_cand.get("radius_km") or (0.05 if top_prob >= 0.50 else 0.10))
            tier = "T1"
        elif category in ("urban_metropolis", "scenic_corridor", "coastal_cliffs", "coastal_stacks", "coastal_cape", "bridge", "commercial_market", "commercial_district", "residential_district", "interchange", "highway", "transit_corridor"):
            calibrated_radius_km = float(top_cand.get("radius_km") or 1.0)
            tier = "T2" if top_prob >= 0.50 else "T3"
        elif category in ("mountain_peak", "mountain_ridge", "mountain_viewpoint", "mountain_pass", "alpine_meadow", "alpine_valley", "himalayan_valley", "rift_valley", "desert_dunes", "desert_basin", "arid_desert", "desert_valley", "alpine_lake", "lake", "waterfall", "glacier", "volcanic_island", "atoll_island", "island", "polar_research_station", "reservoir", "canyon"):
            calibrated_radius_km = float(top_cand.get("radius_km") or 10.0)
            tier = "T2"
        else:
            calibrated_radius_km = float(top_cand.get("radius_km") or 15.0)
            tier = "T3"

        return {
            "name": canonical_name,
            "city": city,
            "country": lm_country,
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "confidence": top_prob,
            "margin": lm_margin,
            "tier": tier,
            "radius_km": calibrated_radius_km,
            "rationale": f"High-confidence visual perception match against landmark database for {canonical_name} ({city}, {lm_country})",
        }
