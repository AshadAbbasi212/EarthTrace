"""Open global land cover provider supporting ESA WorldCover taxonomy."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.landcover")

# Standard ESA WorldCover 10m taxonomy
WORLDCOVER_CLASSES = {
    10: {"name": "Tree cover", "category": "forest", "density": "dense"},
    20: {"name": "Shrubland", "category": "shrub", "density": "moderate"},
    30: {"name": "Grassland", "category": "grass", "density": "moderate"},
    40: {"name": "Cropland", "category": "farmland", "density": "moderate"},
    50: {"name": "Built-up", "category": "urban", "density": "built"},
    60: {"name": "Bare / sparse vegetation", "category": "desert_bare", "density": "sparse"},
    70: {"name": "Snow and ice", "category": "snow_ice", "density": "none"},
    80: {"name": "Permanent water bodies", "category": "water", "density": "none"},
    90: {"name": "Herbaceous wetland", "category": "wetland", "density": "moderate"},
    95: {"name": "Mangroves", "category": "mangrove", "density": "dense"},
    100: {"name": "Moss and lichen", "category": "tundra", "density": "sparse"},
}


class LandCoverProvider(BaseProvider):
    """Provides keyless land cover categorization for scene filtering."""

    def __init__(
        self,
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
    ):
        super().__init__(name="landcover", cache_dir=cache_dir, offline_mode=offline_mode)

    def classify_point(self, lat: float, lon: float) -> Dict[str, Any]:
        """Estimate dominant land cover category at coordinates."""
        cache_key = f"lc_{lat:.4f}_{lon:.4f}"
        cached = self.read_cached_json(cache_key)
        if cached is not None:
            return cached

        # Global geographic heuristics for keyless baseline filtering
        abs_lat = abs(lat)
        if abs_lat > 75:
            class_id = 70  # Snow / Ice
        elif abs_lat > 65:
            class_id = 100  # Tundra / Moss
        elif 15 <= abs_lat <= 30 and ((-15 <= lon <= 55) or (-118 <= lon <= -105)):
            class_id = 60  # Sahara / Arabian / Sonoran desert
        elif abs_lat < 10 and (-75 <= lon <= -50 or 100 <= lon <= 140):
            class_id = 10  # Tropical rainforest
        else:
            class_id = 30  # Grassland / Temperate default

        info = WORLDCOVER_CLASSES.get(class_id, WORLDCOVER_CLASSES[30])
        res = {"class_id": class_id, **info}
        self.write_cached_json(cache_key, res)
        return res

    def filter_candidate(self, lat: float, lon: float, expected_scene_type: str) -> float:
        """Score compatibility between detected scene type and land cover.
        
        Returns a likelihood multiplier between 0.1 and 1.0.
        """
        lc = self.classify_point(lat, lon)
        cat = lc["category"]

        if expected_scene_type == "desert":
            if cat in ("desert_bare", "tundra"):
                return 1.0
            if cat in ("forest", "water"):
                return 0.1  # Highly incompatible
            return 0.5
        elif expected_scene_type == "forest":
            if cat == "forest":
                return 1.0
            if cat in ("desert_bare", "snow_ice"):
                return 0.15
            return 0.6
        elif expected_scene_type == "snow_ice":
            if cat in ("snow_ice", "tundra"):
                return 1.0
            if cat in ("forest", "grass"):
                return 0.3
            return 0.1
        elif expected_scene_type == "urban":
            if cat == "urban":
                return 1.0
            if cat in ("snow_ice", "desert_bare"):
                return 0.2
            return 0.7

        return 1.0
