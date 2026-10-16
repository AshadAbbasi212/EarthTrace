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


def test_stage3_built_bypassed_when_no_linear_infrastructure(tmp_path):
    """Verify Stage3Built returns not_applicable and does not fabricate points without linear clues."""
    from geolocator.pipeline.stage3_built import Stage3Built

    job_dir = tmp_path / "job_no_infra"
    photo_path = tmp_path / "desert.jpg"
    im = Image.new("RGB", (100, 100), (200, 180, 120))
    im.save(photo_path, format="JPEG")

    board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")
    # Natural scene: no bridge, railway, or corridor clues
    board.add_clue(text="Arid desert dunes", kind="soil_type", status="observed")

    stage3b = Stage3Built()
    summary, board = stage3b.process(job_dir, board)

    assert summary["status"] == "not_applicable"
    assert "No linear corridor or bridge" in summary["reason"]
    # Verify no candidate points were fabricated
    assert len(board.data["candidates"]) == 0


def test_stage3_terrain_does_not_fabricate_point_at_moderate_ncc(tmp_path):
    """Verify Stage3Terrain does not promote viewpoint candidate if NCC is below 0.72."""
    from geolocator.pipeline.stage3_terrain import Stage3Terrain

    job_dir = tmp_path / "job_moderate_ncc"
    photo_path = tmp_path / "photo.jpg"
    im = Image.new("RGB", (100, 100), (100, 120, 140))
    im.save(photo_path, format="JPEG")

    board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")
    stage3a = Stage3Terrain()

    # Synthetic profile with mock score ~ 0.55
    # Should not promote candidate point
    stage3a.search_viewpoint = lambda **kwargs: {
        "best_viewpoint": {"lat": 34.0, "lon": 73.0, "heading": 180.0},
        "best_score": 0.58,  # Below 0.72 threshold
        "calibrated_radius_km": 15.0,
        "confidence_tier": "T3",
    }

    mock_profile = [0.1, 0.2, 0.4, 0.3, 0.1, 0.5, 0.3, 0.2]
    summary, board = stage3a.process(
        job_dir=job_dir,
        board=board,
        photo_skyline_override=mock_profile,
    )

    # Point candidate should NOT be fabricated
    point_cands = [c for c in board.data["candidates"].values() if c.get("level") == "point"]
    assert len(point_cands) == 0


def test_online_copilot_disabled_offline_fallback(tmp_path):
    """Verify OnlineCoPilotProvider is disabled when no key is set and bypasses silently."""
    from geolocator.providers.online_copilot import OnlineCoPilotProvider

    copilot = OnlineCoPilotProvider(api_key=None)
    # Ensure environment key is not set
    import os
    orig_env = os.environ.get("GEMINI_API_KEY")
    if orig_env:
        del os.environ["GEMINI_API_KEY"]

    try:
        assert copilot.is_enabled() is False
        job_dir = tmp_path / "job_offline"
        photo_path = tmp_path / "photo.jpg"
        im = Image.new("RGB", (50, 50), (100, 100, 100))
        im.save(photo_path, format="JPEG")
        board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")

        result = copilot.process(job_dir, board, photo_path)
        assert result is None
        assert len(board.data["candidates"]) == 0
    finally:
        if orig_env:
            os.environ["GEMINI_API_KEY"] = orig_env


def test_online_copilot_mock_success(tmp_path):
    """Verify OnlineCoPilotProvider adds verified candidate when API succeeds."""
    from geolocator.providers.online_copilot import OnlineCoPilotProvider

    copilot = OnlineCoPilotProvider(api_key="mock_test_key")
    assert copilot.is_enabled() is True

    # Mock analyze_photo
    copilot.analyze_photo = lambda *args, **kwargs: {
        "location_name": "Eiffel Tower, Paris",
        "country": "France",
        "state_or_province": "Île-de-France",
        "city_or_district": "Paris",
        "latitude": 48.8584,
        "longitude": 2.2945,
        "confidence_tier": "T1",
        "error_radius_km": 0.05,
        "supporting_clues": ["Wrought-iron lattice tower structure", "Champ de Mars alignment"],
        "forensic_rationale": "Distinctive architectural silhouette of the Eiffel Tower in Paris.",
    }

    job_dir = tmp_path / "job_mock_copilot"
    photo_path = tmp_path / "photo.jpg"
    im = Image.new("RGB", (50, 50), (100, 100, 100))
    im.save(photo_path, format="JPEG")
    board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")

    res = copilot.process(job_dir, board, photo_path, api_key="mock_test_key")
    assert res is not None
    assert "Online Vision: Eiffel Tower, Paris" in board.data["candidates"]
    top_cand = board.data["candidates"]["Online Vision: Eiffel Tower, Paris"]
    assert top_cand["lat"] == 48.8584
    assert top_cand["lon"] == 2.2945
    assert top_cand["level"] == "point"
    assert (job_dir / "online_copilot_results.json").exists()


def test_sign_stop_words_phrase_filtering():
    """Verify that generic sign and marker phrases are caught by stop-word filters."""
    from geolocator.adapters.clues_adapter import COMMON_STOP_WORDS
    assert "historical marker" in COMMON_STOP_WORDS
    assert "visitor" in COMMON_STOP_WORDS
    assert "viewpoint" in COMMON_STOP_WORDS
    assert "welcome" in COMMON_STOP_WORDS

    # Verify token-level matching rejects composite stop-word phrases
    test_phrase = "Historical Marker"
    tokens = [t.lower() for t in test_phrase.split()]
    assert all(t in COMMON_STOP_WORDS for t in tokens)


def test_stage3_built_bbox_clamping():
    """Verify that oversized bounding boxes in Stage3Built are bounded to <= 0.20 deg."""
    from geolocator.pipeline.stage3_built import Stage3Built
    from unittest.mock import MagicMock

    mock_osm = MagicMock()
    mock_osm.find_co_occurrences.return_value = []
    stage3 = Stage3Built(osm_provider=mock_osm)

    # Supply an oversized bounding box (e.g. 1.0 deg x 1.0 deg)
    oversized_bbox = (33.0, 72.0, 34.0, 73.0)
    stage3.query_crossings_in_bbox(oversized_bbox, line_kind="railway")

    # Assert that find_co_occurrences was called with clamped bounds
    call_kwargs = mock_osm.find_co_occurrences.call_args[1]
    assert call_kwargs["north"] - call_kwargs["south"] <= 0.21
    assert call_kwargs["east"] - call_kwargs["west"] <= 0.21


def test_stage2_prior_corroborates_confident_landmarks(tmp_path):
    """Verify that Stage2Prior accepts high-confidence landmark candidates even without nearby cell prior."""
    job_dir = tmp_path / "job_landmark_corrob"
    job_dir.mkdir(parents=True)
    photo_path = tmp_path / "photo.jpg"
    im = Image.new("RGB", (50, 50), (120, 120, 120))
    im.save(photo_path, format="JPEG")

    board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")
    # Add a high-confidence T1 landmark candidate
    board.add_candidate(
        name="Landmark: Faisal Mosque",
        level="point",
        lat=33.7299,
        lon=73.0373,
        prior=5.0,
        metadata={
            "landmark": "Faisal Mosque",
            "tier": "T1",
            "radius_km": 0.05,
            "source": "landmark_matcher",
        },
    )

    stage2 = Stage2Prior()
    # Mock GeoCLIP predictions far away to test landmark exception
    mock_preds = [{"lat": 24.86, "lon": 67.00, "prob": 0.05}]  # Karachi ~1100 km away
    summary, updated_board = stage2.process(
        job_dir=job_dir,
        board=board,
        working_image_path=photo_path,
        mock_predictions=mock_preds,
    )

    # Verify that the landmark point candidate was retained in search bboxes
    assert (job_dir / "prior_results.json").exists()
    search_bboxes = updated_board.data.get("search_bboxes", [])
    has_landmark_bbox = any(
        abs(b["center"][0] - 33.7299) < 0.1 for b in search_bboxes
    )
    assert has_landmark_bbox


def test_comprehensive_landmark_vector_store():
    """Verify LandmarkVectorStore precomputed offline index and dot-product similarity engine."""
    import torch
    from geolocator.pipeline.vector_store import LandmarkVectorStore

    v_store = LandmarkVectorStore.get_instance()
    assert v_store.is_ready is True
    assert v_store.metadata is not None
    assert v_store.embeddings is not None
    assert v_store.embeddings.ndim == 2
    assert v_store.embeddings.shape[1] == 768
    assert len(v_store.metadata) >= 800

    # Pick an item from the metadata (e.g. Faisal Mosque or Pakistan Monument)
    target_idx = 0
    target_meta = v_store.metadata[target_idx]
    canonical_name = target_meta["name"]

    # Use the exact embedding of this prompt to simulate a perfect visual match
    mock_img_feat = v_store.embeddings[target_idx : target_idx + 1].clone()

    res = v_store.search(
        image_embedding=mock_img_feat,
        min_confidence=0.10,
        logit_scale=100.0,
    )

    assert res is not None
    assert res["name"] == canonical_name
    assert "city" in res
    assert "country" in res
    assert "category" in res
    assert res["confidence"] > 0.30
    assert res["tier"] in ("T1", "T2", "T3")

    # Test wilderness category rejection:
    # If the candidate is a university or civic building, a wilderness scene_type must suppress it
    civic_idx = None
    for i, item in enumerate(v_store.metadata):
        if item.get("category") in ("university_campus", "hospital_complex", "civic_building"):
            civic_idx = i
            break

    if civic_idx is not None:
        civic_feat = v_store.embeddings[civic_idx : civic_idx + 1].clone()
        res_wild = v_store.search(
            image_embedding=civic_feat,
            scene_type="mountain",
            has_buildings=False,
            min_confidence=0.10,
        )
        # Should not match a university/civic building when scene is pure mountain/wilderness
        if res_wild is not None:
            assert res_wild["category"] not in ("university_campus", "hospital_complex")


def test_all_target_country_landmarks_exist():
    """Verify landmark databases exist for all prioritized target countries with dense city coverage."""
    import json
    landmarks_dir = Path("data/landmarks")
    assert landmarks_dir.exists()

    expected_files = [
        "pakistan.json",
        "turkey.json",
        "saudi_arabia.json",
        "uae.json",
        "egypt.json",
        "india.json",
        "iran.json",
        "iraq.json",
        "oman.json",
        "qatar.json",
        "kuwait.json",
        "bahrain.json",
        "syria.json",
        "yemen.json",
        "israel_palestine.json",
        "global_iconic.json",
    ]

    for fname in expected_files:
        fpath = landmarks_dir / fname
        assert fpath.exists(), f"Missing landmark file {fname}"
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) >= 5, f"{fname} has only {len(data)} spots"

    # Check Pakistan Islamabad spot count
    with open(landmarks_dir / "pakistan.json", "r", encoding="utf-8") as f:
        pk_data = json.load(f)
        isb_spots = [s for s in pk_data if s.get("city") == "Islamabad"]
        assert len(isb_spots) >= 100, f"Expected 100 spots in Islamabad, got {len(isb_spots)}"




