"""Unit and synthetic integration tests for Stage 3b (Built/Rural & Coastal Branches)."""
import json
import pytest
from pathlib import Path

from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.stage3_built import Stage3Built
from geolocator.pipeline.geo_utils import haversine_distance_km


def test_sample_points_along_polyline():
    # 10 km straight line eastwards at lat 50.0
    p1 = (50.0, 0.0)
    p2 = (50.0, 0.14)
    dist_total_km = haversine_distance_km(p1[0], p1[1], p2[0], p2[1])

    sampled = Stage3Built.sample_points_along_polyline([p1, p2], step_m=500.0)
    assert len(sampled) >= 15
    assert sampled[0]["lat"] == p1[0]
    assert sampled[0]["lon"] == p1[1]

    # Verify spacing between consecutive points is ~500m
    for i in range(len(sampled) - 1):
        step_km = haversine_distance_km(
            sampled[i]["lat"], sampled[i]["lon"],
            sampled[i + 1]["lat"], sampled[i + 1]["lon"],
        )
        assert 0.45 <= step_km <= 0.55


def test_synthetic_corridor_point_recovery():
    """Synthetic corridor test: recovers point along a line to <= 1 km."""
    # A 20 km railway line corridor across southern England / Thames valley
    corridor = [
        (51.4800, -0.2500),
        (51.4900, -0.1500),
        (51.5000, -0.0500),  # Midpoint
        (51.5100, 0.0500),
    ]

    # Ground truth: a distinctive railway bridge crossing at km ~14 along the line
    true_lat = 51.5000
    true_lon = -0.0500

    crossings = [
        {
            "lat": true_lat,
            "lon": true_lon,
            "type": "bridge",
            "tags": {"railway": "rail", "bridge": "yes"},
        },
        {
            "lat": 51.4820,
            "lon": -0.2300,
            "type": "level_crossing",
            "tags": {"railway": "level_crossing"},
        },
    ]

    stage3b = Stage3Built()
    match_res = stage3b.match_corridor_point(
        corridor_polyline=corridor,
        crossings=crossings,
        target_features={"is_bridge": True},
        max_deviation_km=1.0,
    )

    best_pt = match_res["best_point"]
    assert best_pt is not None
    assert match_res["score"] >= 3.0

    rec_lat = best_pt["lat"]
    rec_lon = best_pt["lon"]
    error_km = haversine_distance_km(rec_lat, rec_lon, true_lat, true_lon)

    # Strict requirement: recovers point along line to <= 1 km!
    assert error_km <= 1.0, f"Corridor point recovery error {error_km:.3f} km exceeds 1 km threshold"
    assert match_res["confidence_tier"] in ("T1", "T2")


def test_stage3_built_pipeline(tmp_path):
    job_dir = tmp_path / "built_job"
    board = CandidateBoard(photo_path=tmp_path / "shot.jpg", board_path=job_dir / "board.json")

    mock_corridor = [
        (48.8500, 2.3000),
        (48.8566, 2.3522),  # Near Seine bridge
        (48.8600, 2.4000),
    ]
    mock_crossings = [{
        "lat": 48.8566,
        "lon": 2.3522,
        "type": "bridge",
        "tags": {"bridge": "yes", "highway": "primary"},
    }]

    stage3b = Stage3Built()
    summary, board = stage3b.process(
        job_dir=job_dir,
        board=board,
        mock_corridor=mock_corridor,
        mock_crossings=mock_crossings,
        target_features={"is_bridge": True},
    )

    assert "stage3_built" in board.data["stages_run"]
    assert (job_dir / "osm_corridor_results.json").exists()
    ranked = board.rank()
    assert len(ranked) > 0
    assert "lat" in ranked[0]
