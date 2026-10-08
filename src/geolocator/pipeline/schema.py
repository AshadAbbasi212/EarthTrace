"""Strict Pydantic schemas for Stage 1 VLM perception and clue extraction."""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class TerrainCues(BaseModel):
    relief: Literal["flat", "hilly", "mountainous", "unknown"] = "unknown"
    landforms: List[str] = Field(default_factory=list)
    rock_soil_color: str = "unknown"
    horizon_visible: bool = False


class VegetationCues(BaseModel):
    type: str = "unknown"
    density: Literal["none", "sparse", "moderate", "dense", "unknown"] = "unknown"
    notable_species: List[str] = Field(default_factory=list)


class ClimateCues(BaseModel):
    season_guess: str = "unknown"
    snow: bool = False
    aridity: Literal["arid", "semi_arid", "humid", "unknown"] = "unknown"


class BuiltEnvironmentCues(BaseModel):
    road_markings: str = "unknown"
    driving_side: Literal["left", "right", "unknown"] = "unknown"
    utility_poles: str = "unknown"
    architecture: str = "unknown"
    vehicles: str = "unknown"


class TextSignItem(BaseModel):
    text: str
    script: Literal["latin", "cyrillic", "arabic", "hanzi", "devanagari", "greek", "hebrew", "other", "unknown"] = "unknown"
    language_guess: str = "unknown"


class SunShadowCues(BaseModel):
    shadows_visible: bool = False
    time_of_day_guess: str = "unknown"


class WaterCues(BaseModel):
    type: Literal["none", "sea", "lake", "river", "glacier", "unknown"] = "none"
    notes: str = ""


class RegionGuessItem(BaseModel):
    place: str
    reason: str
    confidence: float = 0.5


class ClueExtractionResult(BaseModel):
    scene_type: Literal[
        "urban", "rural_road", "farmland", "forest", "mountain", "desert",
        "valley", "coast", "lake_river", "snow_ice", "island", "indoor", "other"
    ] = "other"
    terrain: TerrainCues = Field(default_factory=TerrainCues)
    vegetation: VegetationCues = Field(default_factory=VegetationCues)
    climate_cues: ClimateCues = Field(default_factory=ClimateCues)
    built_environment: BuiltEnvironmentCues = Field(default_factory=BuiltEnvironmentCues)
    text_and_signs: List[TextSignItem] = Field(default_factory=list)
    sun_shadow: SunShadowCues = Field(default_factory=SunShadowCues)
    water: WaterCues = Field(default_factory=WaterCues)
    region_guesses: List[RegionGuessItem] = Field(default_factory=list)
    distinctive_features: List[str] = Field(default_factory=list)
    overall_confidence: float = 0.0

    @classmethod
    def create_default(cls) -> "ClueExtractionResult":
        """Return a safe fallback instance with default 'unknown' values."""
        return cls()
