"""Unit tests for configuration loading."""
from pathlib import Path
from geolocator.config import AppConfig, get_config


def test_config_loads_defaults():
    config = AppConfig()
    assert config.server.port == 8000
    assert config.hardware.device in ("cuda", "cpu")
    assert config.pipeline.sift_min_inliers_for_t1 == 15
    assert len(config.providers.osm.endpoints) >= 1


def test_config_loads_yaml():
    yaml_path = Path("config.yaml")
    assert yaml_path.exists()
    config = get_config(yaml_path)
    assert config.models.vlm.model_id == "Qwen/Qwen2.5-VL-3B-Instruct"
    assert config.hardware.max_vram_gb == 4.0
    assert config.providers.dem.terrarium_tile_url.startswith("https://")
