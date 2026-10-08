"""Unit and synthetic integration tests for Stage 2 (Global Prior & Biomes)."""
import json
import pytest
from pathlib import Path
from PIL import Image

from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.stage0_intake import Stage0Intake
from geolocator.pipeline.stage1_clues import Stage1Clues
from geolocator.pipeline.stage2_prior import Stage2Prior
from geolocator.pipeline.geo_utils import is_in_region, haversine_distance_km, cluster_points


def test_geo_utils():
    # Distance between London (51.5074, -0.1278) and Paris (48.8566, 2.3522) ~ 343 km
    dist = haversine_distance_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 340.0 < dist < 350.0

    # Region bounds
    assert is_in_region(60.1699, 24.9384, "scandinavia")  # Helsinki, Finland
    assert not is_in_region(25.0, 30.0, "scandinavia")      # Egypt/Sahara
    assert is_in_region(25.0, 30.0, "sahara")


def test_clustering_points():
    points = [
        {"lat": 41.9028, "lon": 12.4964, "prob": 0.05, "country": "Italy"},  # Rome
        {"lat": 41.9100, "lon": 12.5000, "prob": 0.04, "country": "Italy"},  # Near Rome
        {"lat": 48.8566, "lon": 2.3522, "prob": 0.03, "country": "France"},  # Paris
    ]
    clusters = cluster_points(points, radius_km=50.0)
    assert len(clusters) == 2  # Rome cluster + Paris cluster
    assert clusters[0]["country"] == "Italy"
    assert len(clusters[0]["points"]) == 2


def test_sahara_vs_scandinavia_synthetic_exclusion(tmp_path):
    """Synthetic test: verify a photo of the Sahara does not place candidate mass in Scandinavia."""
    job_dir = tmp_path / "sahara_job"
    board = CandidateBoard(photo_path=tmp_path / "sahara.jpg", board_path=job_dir / "board.json")

    # Board with arid / desert cues
    board.add_clue(text="High aridity observed, barren desert ground", kind="colorimetry", status="observed")

    # Set of candidate points spanning Sahara and Scandinavia
    mock_predictions = [
        # Sahara / Arid locations
        {"lat": 24.0, "lon": 12.0, "prob": 0.002},   # Sahara (Algeria/Libya)
        {"lat": 26.5, "lon": 29.8, "prob": 0.0018},  # Western Egypt
        {"lat": 22.1, "lon": 5.3, "prob": 0.0015},   # Ahaggar / Sahara
        # Scandinavia locations (cold / boreal / subarctic)
        {"lat": 63.8, "lon": 20.2, "prob": 0.0005},  # Sweden
        {"lat": 60.2, "lon": 24.9, "prob": 0.0004},  # Finland
        {"lat": 68.4, "lon": 14.5, "prob": 0.0003},  # Northern Norway
    ]

    stage2 = Stage2Prior()
    summary, board = stage2.process(
        job_dir=job_dir,
        board=board,
        mock_predictions=mock_predictions,
    )

    clusters = summary["top_clusters"]
    assert len(clusters) > 0

    # Verify top cluster is in Sahara / arid zone, NOT in Scandinavia
    top_cluster = clusters[0]
    top_lat = top_cluster["center"][0]
    top_lon = top_cluster["center"][1]
    assert not is_in_region(top_lat, top_lon, "scandinavia")
    assert is_in_region(top_lat, top_lon, "sahara")

    # Verify Scandinavian probability mass is virtually zero
    scandi_prob_mass = sum(
        c["probability"] for c in clusters
        if is_in_region(c["center"][0], c["center"][1], "scandinavia")
    )
    assert scandi_prob_mass < 0.001, f"Expected < 0.001 Scandinavian mass, got {scandi_prob_mass}"


def test_hint_conditioning(tmp_path):
    job_dir = tmp_path / "hint_job"
    board = CandidateBoard(photo_path=tmp_path / "shot.jpg", board_path=job_dir / "board.json")

    # User hinted Italy
    board.add_clue(text="Italy", kind="hint_country", status="observed")

    mock_predictions = [
        {"lat": 48.8566, "lon": 2.3522, "prob": 0.005},   # France (higher raw prob)
        {"lat": 41.9028, "lon": 12.4964, "prob": 0.002},  # Italy (lower raw prob)
    ]

    stage2 = Stage2Prior()
    summary, board = stage2.process(
        job_dir=job_dir,
        board=board,
        mock_predictions=mock_predictions,
    )

    top_cluster = summary["top_clusters"][0]
    assert top_cluster["country"] == "Italy"


def test_geoclip_end_to_end_inference(tmp_path):
    """End-to-end execution of GeoCLIP model via ModelManager."""
    job_dir = tmp_path / "e2e_job"
    img_path = tmp_path / "desert_scene.jpg"

    # Create a simple test image (warm sandy color)
    im = Image.new("RGB", (600, 400), (210, 180, 120))
    im.save(img_path, format="JPEG")

    board = CandidateBoard(photo_path=img_path, board_path=job_dir / "board.json")
    stage2 = Stage2Prior()

    summary, board = stage2.process(
        job_dir=job_dir,
        board=board,
        working_image_path=img_path,
        top_k=20,
    )

    assert summary["total_raw_predictions"] == 20
    assert summary["clusters_count"] > 0
    assert len(board.data["search_bboxes"]) > 0
    assert (job_dir / "prior_results.json").exists()
    assert "stage2_prior" in board.data["stages_run"]
