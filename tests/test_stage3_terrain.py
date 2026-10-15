"""Unit and synthetic integration tests for Stage 3a (Natural Terrain Branch)."""
import json
import math
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

from geolocator.providers.dem import DEMProvider
from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.skyline_extractor import SkylineExtractor
from geolocator.pipeline.stage3_terrain import Stage3Terrain
from geolocator.pipeline.geo_utils import haversine_distance_km


def test_skyline_extractor(tmp_path):
    """Test ridgeline extraction on synthetic mountain image."""
    img_path = tmp_path / "mountain_shot.jpg"
    w, h = 400, 300
    im = Image.new("RGB", (w, h), (180, 210, 255))  # Bright sky
    draw = ImageDraw.Draw(im)

    # Draw dark triangular mountain peak in lower half
    mountain_pts = [(0, h), (200, 100), (w, h)]
    draw.polygon(mountain_pts, fill=(60, 50, 45))
    im.save(img_path, format="JPEG")

    extractor = SkylineExtractor(target_width=120)
    overlay_path = tmp_path / "overlay.png"
    result = extractor.extract_from_image(img_path, save_overlay_path=overlay_path)

    assert result["samples"] == 120
    assert len(result["normalized_profile"]) == 120
    assert overlay_path.exists()

    # The peak at x=200 corresponds to normalized center ~ sample 60 having maximum elevation
    profile = np.array(result["raw_elevations"])
    center_idx = len(profile) // 2
    # Mountain peak should be significantly higher than the edges
    assert profile[center_idx] > profile[5]
    assert profile[center_idx] > profile[-5]


def test_synthetic_terrain_viewpoint_recovery(tmp_path):
    """Synthetic terrain test: recovers viewpoint to <= 5 km from DEM skyline."""
    # True camera viewpoint: Mt. Fuji vantage point from Lake Kawaguchi
    true_lat = 35.4983
    true_lon = 138.7688
    true_heading = 194.0

    dem = DEMProvider()
    # Compute ground truth synthetic DEM skyline from true position
    true_profile = dem.compute_skyline_profile(
        lat=true_lat,
        lon=true_lon,
        heading=true_heading,
        hfov=50.0,
        range_m=35000.0,
        samples=80,
    )
    ground_truth_angles = np.array(true_profile["skyline_angles"], dtype=np.float32)

    # Add slight sensor noise (simulating optical distortion / extraction noise)
    noise = np.random.normal(0.0, 0.05, size=ground_truth_angles.shape).astype(np.float32)
    photo_profile = ground_truth_angles + noise

    # Search from an offset center (4.0 km away from truth)
    offset_center_lat = true_lat + 0.03   # ~3.3 km north
    offset_center_lon = true_lon - 0.02   # ~1.8 km west
    initial_offset_km = haversine_distance_km(offset_center_lat, offset_center_lon, true_lat, true_lon)
    assert 3.0 < initial_offset_km < 6.0

    stage3 = Stage3Terrain(dem_provider=dem)
    fit_res = stage3.search_viewpoint(
        photo_profile=photo_profile,
        center_lat=offset_center_lat,
        center_lon=offset_center_lon,
        radius_km=10.0,
        coarse_step_km=2.0,
        fine_step_km=0.4,
        heading_hint=true_heading,
        hfov=50.0,
        range_m=35000.0,
    )

    best_vp = fit_res["best_viewpoint"]
    assert best_vp is not None
    assert fit_res["best_score"] > 0.80

    rec_lat = best_vp["lat"]
    rec_lon = best_vp["lon"]
    error_km = haversine_distance_km(rec_lat, rec_lon, true_lat, true_lon)

    # Strict requirement: recovers viewpoint to <= 5 km!
    assert error_km <= 5.0, f"Recovered viewpoint error {error_km:.2f} km exceeds 5 km threshold"
    assert abs(best_vp["heading"] - true_heading) <= 15.0


def test_stage3_terrain_process_pipeline(tmp_path):
    """Test full process() flow writing candidates and evidence to CandidateBoard."""
    job_dir = tmp_path / "terrain_job"
    board = CandidateBoard(photo_path=tmp_path / "scenic.jpg", board_path=job_dir / "board.json")

    # Set up Stage 2 search bboxes pointing to Mt Fuji region
    board.data["search_bboxes"] = [{
        "cluster_id": "cell_1",
        "candidate_name": "Fuji Region",
        "bbox": [35.40, 138.65, 35.60, 138.85],
        "center": [35.4983, 138.7688],
        "score": 5.0,
    }]

    # Provide synthetic profile override for fast test execution
    dem = DEMProvider()
    prof = dem.compute_skyline_profile(35.4983, 138.7688, heading=194.0, hfov=50.0, samples=40)

    stage3 = Stage3Terrain(dem_provider=dem)
    summary, board = stage3.process(
        job_dir=job_dir,
        board=board,
        photo_skyline_override=prof["skyline_angles"],
        radius_km=6.0,
    )

    assert "stage3_terrain" in board.data["stages_run"]
    assert (job_dir / "terrain_results.json").exists()
    assert (job_dir / "skyline_extracted.json").exists()

    ranked = board.rank()
    assert len(ranked) > 0
    top = ranked[0]
    assert "lat" in top
    assert top["lat"] is not None


def test_skyline_extractor_rejects_manmade_roofline(tmp_path):
    """Verify that building rooflines with terracotta/red tile roofs are rejected as non-terrain."""
    img_path = tmp_path / "church_roof_shot.jpg"
    w, h = 400, 300
    im = Image.new("RGB", (w, h), (180, 210, 255))  # Bright sky
    draw = ImageDraw.Draw(im)

    # Draw pitched red terracotta church roof and steeple
    roof_pts = [(0, h), (100, 140), (200, 70), (300, 140), (w, h)]
    draw.polygon(roof_pts, fill=(210, 65, 45))  # Vibrant terracotta red roof
    im.save(img_path, format="JPEG")

    extractor = SkylineExtractor(target_width=120)
    overlay_path = tmp_path / "overlay_roof.png"
    result = extractor.extract_from_image(img_path, save_overlay_path=overlay_path)

    assert result["is_manmade_roofline"] is True
    assert result["is_non_flat"] is False
    assert "terracotta" in result["roofline_reason"].lower() or "roof" in result["roofline_reason"].lower()


def test_stage3_terrain_bypasses_manmade_roofline(tmp_path):
    """Verify Stage3Terrain honestly outputs not_applicable on building roofline scenes."""
    job_dir = tmp_path / "roof_job"
    job_dir.mkdir(parents=True, exist_ok=True)
    img_path = job_dir / "working_1024.jpg"
    w, h = 400, 300
    im = Image.new("RGB", (w, h), (180, 210, 255))
    draw = ImageDraw.Draw(im)
    draw.polygon([(0, h), (200, 80), (w, h)], fill=(215, 60, 40))
    im.save(img_path, format="JPEG")

    board = CandidateBoard(photo_path=img_path, board_path=job_dir / "board.json")
    dem = DEMProvider()
    stage3 = Stage3Terrain(dem_provider=dem)
    summary, board = stage3.process(job_dir=job_dir, board=board, working_image_path=img_path)

    assert summary["status"] == "not_applicable"
    assert "roof" in summary["reason"].lower() or "architecture" in summary["reason"].lower()
    assert summary["fit_results"]["best_viewpoint"] is None
    # Ensure no spurious viewpoint point candidate was added to the board
    point_cands = [c for c in board.data.get("candidates", {}).values() if c.get("level") == "point"]
    assert len(point_cands) == 0
