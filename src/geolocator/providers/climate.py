"""Global Köppen-Geiger climate and biome provider for regional prior scoring."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.climate")

# Major Köppen climate groups
KOPPEN_GROUPS = {
    "A": "Tropical",
    "B": "Arid / Desert",
    "C": "Temperate",
    "D": "Continental / Boreal",
    "E": "Polar / Alpine",
}

KOPPEN_CLASSES = {
    "Af": {"group": "A", "desc": "Tropical rainforest", "aridity": "humid", "snow": False},
    "Am": {"group": "A", "desc": "Tropical monsoon", "aridity": "humid", "snow": False},
    "Aw": {"group": "A", "desc": "Tropical savanna", "aridity": "semi_arid", "snow": False},
    "BWh": {"group": "B", "desc": "Hot desert", "aridity": "arid", "snow": False},
    "BWk": {"group": "B", "desc": "Cold desert", "aridity": "arid", "snow": True},
    "BSh": {"group": "B", "desc": "Hot semi-arid", "aridity": "semi_arid", "snow": False},
    "BSk": {"group": "B", "desc": "Cold semi-arid", "aridity": "semi_arid", "snow": True},
    "Csa": {"group": "C", "desc": "Mediterranean hot summer", "aridity": "semi_arid", "snow": False},
    "Csb": {"group": "C", "desc": "Mediterranean warm summer", "aridity": "semi_arid", "snow": False},
    "Cfa": {"group": "C", "desc": "Humid subtropical", "aridity": "humid", "snow": False},
    "Cfb": {"group": "C", "desc": "Oceanic / Marine", "aridity": "humid", "snow": True},
    "Dfa": {"group": "D", "desc": "Hot-summer continental", "aridity": "humid", "snow": True},
    "Dfb": {"group": "D", "desc": "Warm-summer continental", "aridity": "humid", "snow": True},
    "Dfc": {"group": "D", "desc": "Subarctic / Taiga", "aridity": "humid", "snow": True},
    "ET": {"group": "E", "desc": "Tundra", "aridity": "arid", "snow": True},
    "EF": {"group": "E", "desc": "Ice cap", "aridity": "arid", "snow": True},
}


class ClimateProvider(BaseProvider):
    """Provides keyless global Köppen-Geiger climate classification and compatibility scoring."""

    def __init__(
        self,
        cache_dir: str | Path = ".geo-cache",
        data_dir: str | Path = "data/climate",
        offline_mode: bool = False,
    ):
        super().__init__(name="climate", cache_dir=cache_dir, offline_mode=offline_mode)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._climate_grid: Optional[Dict[str, str]] = None
        self._load_or_create_grid()

    def _load_or_create_grid(self) -> None:
        """Load climate classification grid or initialize algorithmic approximation."""
        grid_file = self.data_dir / "koppen_grid.json"
        if grid_file.exists():
            try:
                self._climate_grid = json.loads(grid_file.read_text(encoding="utf-8"))
                return
            except Exception as e:
                logger.warning("[climate] Failed to load grid file: %s", e)

        # Fallback to algorithmic approximation based on latitude, elevation, and continents
        self._climate_grid = {}

    def get_climate_classification(self, lat: float, lon: float, elevation_m: float = 0.0) -> Dict[str, Any]:
        """Classify coordinates into Köppen-Geiger code and environmental properties."""
        abs_lat = abs(lat)

        # Check pre-indexed grid if available
        grid_key = f"{int(round(lat))}_{int(round(lon))}"
        if self._climate_grid and grid_key in self._climate_grid:
            code = self._climate_grid[grid_key]
            info = KOPPEN_CLASSES.get(code, {"group": "C", "desc": "Temperate", "aridity": "humid", "snow": False})
            return {"code": code, **info}

        # Global analytical baseline (Beck/Geiger zoning approximation)
        if abs_lat > 66.5 or elevation_m > 3800:
            code = "EF" if (abs_lat > 75 and elevation_m > 500) else "ET"
        elif 50.0 <= abs_lat <= 66.5:
            code = "Dfc" if elevation_m > 400 else "Dfb"
        elif 35.0 <= abs_lat < 50.0:
            # Check major desert longitudes
            if (-118 <= lon <= -100 and lat > 0) or (15 <= lon <= 85 and 20 <= lat <= 45):
                code = "BWk" if elevation_m > 1000 else "BSk"
            elif -10 <= lon <= 40 and 30 <= lat <= 45:
                code = "Csa"  # Mediterranean
            else:
                code = "Cfb" if abs_lat > 42 else "Cfa"
        elif 20.0 <= abs_lat < 35.0:
            # Subtropical desert belts (Sahara, Arabia, Sonoran, Atacama, Outback)
            if (-15 <= lon <= 60 and 15 <= lat <= 32) or (115 <= lon <= 145 and -35 <= lat <= -18):
                code = "BWh"
            elif -75 <= lon <= -68 and -30 <= lat <= -18:
                code = "BWh"  # Atacama
            else:
                code = "Cfa"
        else:
            # Equatorial tropics
            code = "Af" if (-75 <= lon <= -50 or 100 <= lon <= 140 or 10 <= lon <= 30) else "Aw"

        info = KOPPEN_CLASSES.get(code, {"group": "C", "desc": "Temperate", "aridity": "humid", "snow": False})
        return {"code": code, **info}

    def score_compatibility(
        self,
        lat: float,
        lon: float,
        aridity_cue: Optional[str] = None,
        snow_present: Optional[bool] = None,
        vegetation_density: Optional[str] = None,
        elevation_m: float = 0.0,
    ) -> float:
        """Compute compatibility score [0.05, 1.0] between visual cues and regional climate."""
        climate = self.get_climate_classification(lat, lon, elevation_m)
        score = 1.0

        # Aridity check
        if aridity_cue:
            if aridity_cue == "arid":
                if climate["group"] == "B":
                    score *= 1.0
                elif climate["group"] in ("A", "C"):
                    score *= 0.2  # Heavy downweight for lush rainforest/marine in desert photo
            elif aridity_cue == "humid":
                if climate["group"] == "B":
                    score *= 0.15  # Heavy downweight for arid desert in lush humid photo
                elif climate["group"] in ("A", "C", "D"):
                    score *= 1.0

        # Snow check
        if snow_present is True:
            # Tropical lowlands cannot have natural snow
            if climate["group"] == "A" and elevation_m < 3500:
                score *= 0.05
            elif climate["group"] in ("D", "E") or elevation_m > 1500:
                score *= 1.0

        # Vegetation density check
        if vegetation_density == "dense":
            if climate["code"] in ("BWh", "BWk", "EF"):
                score *= 0.05
        elif vegetation_density == "none":
            if climate["code"] in ("Af", "Cfb") and elevation_m < 2000:
                score *= 0.3

        return max(0.05, min(1.0, score))
