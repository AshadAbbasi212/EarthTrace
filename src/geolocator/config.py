"""Configuration management using Pydantic and YAML."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    passphrase_enabled: bool = False
    passphrase: str = ""
    rate_limit_per_minute: int = 30


class StorageConfig(BaseModel):
    jobs_dir: str = "jobs"
    cache_dir: str = ".geo-cache"
    models_dir: str = "models"
    data_dir: str = "data"
    eval_dir: str = "eval"
    logs_dir: str = "logs"
    retention_hours: int = 24
    auto_delete_expired: bool = True
    strip_exif_on_store: bool = True


class HardwareConfig(BaseModel):
    device: str = "cuda"
    max_vram_gb: float = 4.0
    unload_after_use: bool = True
    empty_cache_after_step: bool = True


class VLMConfig(BaseModel):
    model_id: str = "Qwen/Qwen2.5-VL-3B-Instruct"
    fallback_model_id: str = "HuggingFaceTB/SmolVLM-Instruct"
    quantization: str = "4bit"
    max_image_dim: int = 1024
    temperature: float = 0.1
    max_tokens: int = 1024


class ModelItemConfig(BaseModel):
    model_id: str
    device: str = "cuda"


class ModelsConfig(BaseModel):
    vlm: VLMConfig = Field(default_factory=VLMConfig)
    clip: ModelItemConfig = Field(default_factory=lambda: ModelItemConfig(model_id="openai/clip-vit-base-patch32", device="cuda"))
    dinov2: ModelItemConfig = Field(default_factory=lambda: ModelItemConfig(model_id="facebook/dinov2-small", device="cuda"))
    geo_prior: ModelItemConfig = Field(default_factory=lambda: ModelItemConfig(model_id="vincent-claes/GeoCLIP", device="cpu"))


class OSMProviderConfig(BaseModel):
    endpoints: List[str] = Field(default_factory=lambda: [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ])
    timeout_sec: int = 45
    min_retry_delay_sec: float = 2.0
    max_retries: int = 3


class NominatimProviderConfig(BaseModel):
    endpoint: str = "https://nominatim.openstreetmap.org/search"
    rate_limit_sec: float = 1.1
    user_agent: str = "GlobalPhotoGeolocator/1.0 (Local Open-Source Tool)"


class DEMProviderConfig(BaseModel):
    terrarium_tile_url: str = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
    default_zoom: int = 12
    max_zoom: int = 14


class SatelliteProviderConfig(BaseModel):
    default_source: str = "google"
    sources: dict[str, str] = Field(default_factory=lambda: {
        "google": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "esri": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "sentinel": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg"
    })


class GeoPhotoProviderConfig(BaseModel):
    wikipedia_endpoint: str = "https://en.wikipedia.org/w/api.php"
    thumb_base_url: str = "https://thumb.wikimedia.org/"
    max_search_radius_m: int = 5000


class ProvidersConfig(BaseModel):
    osm: OSMProviderConfig = Field(default_factory=OSMProviderConfig)
    nominatim: NominatimProviderConfig = Field(default_factory=NominatimProviderConfig)
    dem: DEMProviderConfig = Field(default_factory=DEMProviderConfig)
    satellite: SatelliteProviderConfig = Field(default_factory=SatelliteProviderConfig)
    geophoto: GeoPhotoProviderConfig = Field(default_factory=GeoPhotoProviderConfig)


class PipelineWeightsConfig(BaseModel):
    geo_prior: float = 0.35
    biome_climate: float = 0.25
    vlm_guess: float = 0.20
    user_hint: float = 0.20


class PipelineConfig(BaseModel):
    max_search_regions: int = 8
    max_candidates_per_region: int = 20
    sift_min_inliers_for_t1: int = 15
    skyline_rms_t2_threshold: float = 12.0
    weights: PipelineWeightsConfig = Field(default_factory=PipelineWeightsConfig)


class AppConfig(BaseSettings):
    server: ServerConfig = Field(default_factory=ServerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    offline_mode: bool = False

    @classmethod
    def load(cls, config_path: str | Path = "config.yaml") -> "AppConfig":
        path = Path(config_path)
        data: dict[str, Any] = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        # Allow environment variable overrides
        if os.getenv("HOST"):
            data.setdefault("server", {})["host"] = os.getenv("HOST")
        if os.getenv("PORT"):
            data.setdefault("server", {})["port"] = int(os.getenv("PORT"))
        if os.getenv("PASSPHRASE"):
            data.setdefault("server", {})["passphrase"] = os.getenv("PASSPHRASE")
            data.setdefault("server", {})["passphrase_enabled"] = True
        if os.getenv("OFFLINE_MODE"):
            data["offline_mode"] = os.getenv("OFFLINE_MODE", "").lower() in ("true", "1", "yes")

        return cls(**data)


# Global singleton helper
_config_instance: Optional[AppConfig] = None


def get_config(config_path: str | Path = "config.yaml") -> AppConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig.load(config_path)
    return _config_instance
