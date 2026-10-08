"""Comprehensive provider integration tests with recorded fixtures and offline validation."""
import json
import pytest
from pathlib import Path
from PIL import Image
import numpy as np

from geolocator.providers.base import BaseProvider
from geolocator.providers.osm import OSMProvider
from geolocator.providers.nominatim import NominatimProvider
from geolocator.providers.dem import DEMProvider
from geolocator.providers.satellite import SatelliteProvider
from geolocator.providers.street_image import StreetImageProvider
from geolocator.providers.climate import ClimateProvider
from geolocator.providers.landcover import LandCoverProvider


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "cache"


def test_base_provider_caching_and_offline(tmp_cache):
    provider = BaseProvider(name="test_base", cache_dir=tmp_cache, offline_mode=False)
    
    # Write to cache
    key = "sample_key"
    payload = {"status": "ok", "count": 42}
    provider.write_cached_json(key, payload)
    
    assert provider.is_cached(key, ext=".json")
    read_back = provider.read_cached_json(key)
    assert read_back == payload

    # Test offline mode with cached item
    offline_provider = BaseProvider(name="test_base", cache_dir=tmp_cache, offline_mode=True)
    assert offline_provider.read_cached_json(key) == payload

    # Test offline mode with uncached item raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        offline_provider.fetch_bytes("https://example.invalid/missing", cache_key="missing")


def test_osm_provider_with_fixture(tmp_cache):
    osm = OSMProvider(cache_dir=tmp_cache, offline_mode=True)
    
    # Create recorded Overpass fixture
    query = """[out:json];node(35.0,138.0,36.0,139.0)["amenity"="parking"];out;"""
    key = osm._hash_key(query)
    mock_data = {
        "elements": [
            {"type": "node", "id": 12345, "lat": 35.5, "lon": 138.5, "tags": {"amenity": "parking", "name": "Station Parking"}}
        ]
    }
    osm.write_cached_json(key, mock_data)

    res = osm.query_ql(query)
    assert len(res["elements"]) == 1
    assert res["elements"][0]["id"] == 12345


def test_nominatim_provider_with_fixture(tmp_cache):
    nom = NominatimProvider(cache_dir=tmp_cache, offline_mode=True)
    
    # Pre-cache recorded response
    params = {"q": "Eiffel Tower", "format": "jsonv2", "limit": "5", "addressdetails": "1"}
    key = nom._hash_key(params)
    mock_res = [
        {"place_id": 999, "lat": "48.8584", "lon": "2.2945", "display_name": "Eiffel Tower, Paris, France"}
    ]
    nom.write_cached_json(key, mock_res)

    results = nom.search("Eiffel Tower", limit=5)
    assert len(results) == 1
    assert results[0]["lat"] == "48.8584"


def test_dem_provider_with_fixture(tmp_cache):
    dem = DEMProvider(cache_dir=tmp_cache, offline_mode=True)
    
    # Create synthetic Terrarium DEM tile (256x256 RGB) representing 500m elevation
    # Terrarium formula: elev = R * 256 + G + B/256 - 32768
    # Target 500m -> R*256 + G = 33268 -> R = 129, G = 244, B = 0
    tile_im = Image.new("RGB", (256, 256), (129, 244, 0))
    cache_file = dem.get_cache_path("terrarium_12_2000_1500.png", ext="")
    tile_im.save(cache_file, format="PNG")

    tile_arr = dem.get_tile(zoom=12, tile_x=2000, tile_y=1500)
    assert tile_arr.shape == (256, 256)
    assert abs(tile_arr[0, 0] - 500.0) < 1.0


def test_satellite_provider_with_fixture(tmp_cache):
    sat = SatelliteProvider(cache_dir=tmp_cache, offline_mode=True)
    
    # Pre-cache a 256x256 tile
    tile_im = Image.new("RGB", (256, 256), (30, 80, 120))
    cache_file = sat.get_cache_path("google_17_100_100.jpg", ext="")
    tile_im.save(cache_file, format="JPEG")

    loaded_tile = sat.get_tile(zoom=17, x=100, y=100, source="google")
    assert loaded_tile.size == (256, 256)


def test_street_image_provider_with_fixture(tmp_cache):
    prov = StreetImageProvider(cache_dir=tmp_cache, offline_mode=True)
    
    cache_key = prov._hash_key("geosearch_48.8584_2.2945_1000")
    mock_data = [
        {"id": "1", "title": "Tour Eiffel", "distance_m": 12.0, "lat": 48.8584, "lon": 2.2945, "image_url": "https://thumb.wikimedia.org/test.jpg"}
    ]
    prov.write_cached_json(cache_key, mock_data)

    res = prov.search_nearby(48.8584, 2.2945, radius_m=1000)
    assert len(res) == 1
    assert res[0]["title"] == "Tour Eiffel"


def test_climate_provider():
    climate = ClimateProvider()
    
    # Sahara coordinates (North Africa): Should classify as Arid (B)
    sahara = climate.get_climate_classification(lat=25.0, lon=20.0)
    assert sahara["group"] == "B"
    assert climate.score_compatibility(lat=25.0, lon=20.0, aridity_cue="arid") > 0.8
    assert climate.score_compatibility(lat=25.0, lon=20.0, aridity_cue="humid") < 0.3

    # Equatorial Amazon: Tropical (A)
    amazon = climate.get_climate_classification(lat=-3.0, lon=-60.0)
    assert amazon["group"] == "A"
    assert climate.score_compatibility(lat=-3.0, lon=-60.0, snow_present=True) < 0.2


def test_landcover_provider():
    lc = LandCoverProvider()
    
    # Sahara desert: desert_bare
    res_desert = lc.classify_point(lat=24.0, lon=15.0)
    assert res_desert["category"] == "desert_bare"
    assert lc.filter_candidate(24.0, 15.0, "desert") == 1.0
    assert lc.filter_candidate(24.0, 15.0, "forest") < 0.3

    # Polar ice
    res_polar = lc.classify_point(lat=82.0, lon=0.0)
    assert res_polar["category"] == "snow_ice"
    assert lc.filter_candidate(82.0, 0.0, "snow_ice") == 1.0
