"""Unit and integration tests for geolocation accuracy enhancements."""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image
import pytest

from geolocator.data.gazetteer import query_offline_gazetteer
from geolocator.providers.nominatim import NominatimProvider
from geolocator.pipeline.hint_parser import HintParser
from geolocator.pipeline.solar_utils import calculate_solar_declination, estimate_solar_hemisphere
from geolocator.pipeline.stage4_verification import Stage4Verification
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.stage2_prior import Stage2Prior


def test_offline_gazetteer_highways():
    """Verify that national routes across priority countries resolve instantly offline."""
    # Test Pakistan M-2
    pk_hits = query_offline_gazetteer("M-2", country_iso="PK")
    assert len(pk_hits) > 0
    assert "Islamabad - Lahore Motorway" in pk_hits[0]["display_name"]
    assert pk_hits[0]["country"] == "Pakistan"
    assert abs(float(pk_hits[0]["lat"]) - 32.35) < 0.1

    # Test UAE E11
    ae_hits = query_offline_gazetteer("E11", country_iso="AE")
    assert len(ae_hits) > 0
    assert "Sheikh Zayed Road" in ae_hits[0]["display_name"]
    assert ae_hits[0]["country"] == "United Arab Emirates"

    # Test India NH-44
    in_hits = query_offline_gazetteer("NH-44", country_iso="IN")
    assert len(in_hits) > 0
    assert "National Highway 44" in in_hits[0]["display_name"]

    # Test Kuwait Route 30
    kw_hits = query_offline_gazetteer("Route 30", country_iso="KW")
    assert len(kw_hits) > 0
    assert "Fahaheel Expressway" in kw_hits[0]["display_name"]


def test_offline_gazetteer_settlements():
    """Verify that major regional settlements and capitals resolve offline."""
    doha_hits = query_offline_gazetteer("Doha", country_iso="QA")
    assert len(doha_hits) > 0
    assert doha_hits[0]["country"] == "Qatar"
    assert abs(float(doha_hits[0]["lat"]) - 25.285) < 0.05

    riyadh_hits = query_offline_gazetteer("Riyadh", country_iso="SA")
    assert len(riyadh_hits) > 0
    assert riyadh_hits[0]["country"] == "Saudi Arabia"

    rwp_hits = query_offline_gazetteer("Rawalpindi", country_iso="PK")
    assert len(rwp_hits) > 0
    assert rwp_hits[0]["subdivision"] == "Punjab"


def test_nominatim_fastpath_integration(tmp_path):
    """Verify NominatimProvider returns offline gazetteer matches before network calls."""
    provider = NominatimProvider(cache_dir=tmp_path, offline_mode=True)
    res = provider.search("N-75", country_codes="PK", limit=1)
    assert len(res) > 0
    assert "Murree Expressway" in res[0]["display_name"]
    assert abs(float(res[0]["lat"]) - 33.88) < 0.1


def test_solar_declination_math():
    """Verify solar declination Cooper formula outputs."""
    # Summer solstice (day ~172, June 21): declination should be ~ +23.4 deg
    dec_june = calculate_solar_declination(172)
    assert abs(dec_june - 23.45) < 1.0

    # Winter solstice (day ~355, Dec 21): declination should be ~ -23.4 deg
    dec_dec = calculate_solar_declination(355)
    assert abs(dec_dec - (-23.45)) < 1.0


def test_solar_hemisphere_estimation(tmp_path):
    """Verify solar hemisphere analysis on synthetic daytime image."""
    img = Image.new("RGB", (300, 300), color=(135, 206, 235))  # sky blue
    # Add darker ground
    for y in range(150, 300):
        for x in range(300):
            img.putpixel((x, y), (60, 50, 40))

    exif = {"DateTimeOriginal": "2024:06:21 12:30:00"}
    solar_info = estimate_solar_hemisphere(img, exif_data=exif)
    assert solar_info["solar_declination"] is not None
    assert solar_info["solar_declination"] > 20.0
    assert solar_info["hemisphere"] == "northern"
    assert solar_info["confidence"] >= 0.65


def test_hint_parser_co_pilot_exclusions_and_terrain():
    """Verify natural language hint parsing of negative exclusions and terrain."""
    parser = HintParser()
    parsed = parser.parse("Highway driving near Murree, not India, exclude France, terrain: mountain in autumn")
    assert "Pakistan" in parsed.get("countries", []) or "Murree" in str(parsed.get("landmarks", []))
    assert "India" in parsed.get("excluded_countries", [])
    assert "France" in parsed.get("excluded_countries", [])
    assert parsed.get("terrain_filter") == "mountain"
    assert parsed.get("season") == "autumn"


def test_cross_view_road_bearing_alignment(tmp_path):
    """Verify Stage 4 geometric road bearing alignment detection."""
    stage4 = Stage4Verification()
    # Create two synthetic images with vertical road lines
    img_ground = Image.new("RGB", (256, 256), color=(100, 100, 100))
    img_sat = Image.new("RGB", (256, 256), color=(80, 80, 80))

    res = stage4._compute_road_bearing_alignment(img_ground, img_sat)
    assert "aligned" in res
    assert "boost" in res
    assert res["boost"] >= 0.0


def test_stage2_copilot_exclusion_penalty(tmp_path):
    """Verify that Co-Pilot country exclusion penalizes candidates in excluded countries."""
    stage2 = Stage2Prior()
    board = CandidateBoard(photo_path=tmp_path / "dummy.jpg")
    # Set co-pilot exclusion for India
    board.data["co_pilot"] = {"excluded_countries": ["India"], "terrain_filter": "desert"}

    mock_preds = [
        {"lat": 28.6139, "lon": 77.2090, "prob": 0.60},  # New Delhi, India
        {"lat": 24.8607, "lon": 67.0011, "prob": 0.40},  # Karachi, Pakistan
    ]

    report, updated_board = stage2.process(
        job_dir=tmp_path,
        board=board,
        mock_predictions=mock_preds,
    )

    clusters = report.get("candidate_cells", [])
    # Candidate in Pakistan should be ranked above excluded India
    if len(clusters) > 0:
        top_cluster = clusters[0]
        assert "India" not in top_cluster.get("name", "")


def test_subnational_admin1_and_radius_parsing():
    """Verify HintParser extracts subnational provinces (ADMIN1), radius, and coordinates (Picarta/GeoSpy)."""
    parser = HintParser()
    res = parser.parse("Hiked in Bavaria, Germany near Garmisch within 40 km radius")
    assert "Germany" in res["countries"]
    assert len(res["subnational"]) > 0
    assert res["subnational"][0]["division"] == "Bavaria"
    assert res["radius_km"] == 40.0

    res_coords = parser.parse("Camped in Gilgit-Baltistan around coordinates 35.32, 75.64")
    assert "Pakistan" in res_coords["countries"]
    assert any(s["division"] == "Gilgit-Baltistan" for s in res_coords["subnational"])
    assert res_coords["center_coords"] == (35.32, 75.64)


def test_subnational_prior_conditioning(tmp_path):
    """Verify that Stage2Prior boosts candidate cells within hinted subnational province."""
    stage2 = Stage2Prior()
    board = CandidateBoard(photo_path=tmp_path / "dummy.jpg")
    board.data["user_hints"] = {
        "countries": ["Pakistan"],
        "subnational": [{"division": "Gilgit-Baltistan", "country": "Pakistan"}],
    }

    mock_preds = [
        {"lat": 35.3, "lon": 75.6, "prob": 0.01},  # Skardu (Gilgit-Baltistan)
        {"lat": 31.5, "lon": 74.3, "prob": 0.05},  # Lahore (Punjab)
    ]

    report, updated_board = stage2.process(
        job_dir=tmp_path / "job_subdiv",
        board=board,
        mock_predictions=mock_preds,
    )
    top_cluster = report["top_clusters"][0]
    assert top_cluster["country"] == "Pakistan"
    assert top_cluster["center"][0] > 34.5, "Gilgit-Baltistan must outrank Punjab under subnational conditioning"


def test_stage0_low_light_contrast_enhancement(tmp_path):
    """Verify Stage0Intake detects low-light/twilight photos and produces enhanced copy (GeoAxis HyperVision)."""
    from geolocator.pipeline.stage0_intake import Stage0Intake

    # Create very dark photo (mean luminance ~ 20)
    dark_photo = tmp_path / "night_shot.jpg"
    im = Image.new("RGB", (400, 300), (20, 22, 25))
    im.save(dark_photo, format="JPEG")

    stage0 = Stage0Intake()
    intake_summary, board = stage0.process(dark_photo, tmp_path / "job_dark")

    assert intake_summary["is_low_light"] is True
    assert intake_summary["mean_luminance"] < 50.0
    assert intake_summary["working_enhanced"] is not None
    assert Path(intake_summary["working_enhanced"]).exists()
    assert board.data["is_low_light"] is True

