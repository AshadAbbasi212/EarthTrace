"""Unit and integration tests for Stage 4 (Verification & Pose) and Stage 5 (Decision & Report)."""
import json
import pytest
from pathlib import Path
from PIL import Image

from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.pose_solver import CameraPoseSolver
from geolocator.pipeline.stage4_verification import Stage4Verification
from geolocator.report.generator import ReportGenerator


def test_camera_pose_solver():
    solver = CameraPoseSolver()

    # Forward heading from London (51.5074, -0.1278) directly north (52.5074, -0.1278) -> ~0°
    h_north = solver.solve_heading_from_bearing_points(51.5074, -0.1278, 52.5074, -0.1278)
    assert abs(h_north - 0.0) < 1.0 or abs(h_north - 360.0) < 1.0

    # East heading -> ~90°
    h_east = solver.solve_heading_from_bearing_points(51.5074, -0.1278, 51.5074, 1.0)
    assert 85.0 < h_east < 95.0

    # Resection from correspondences
    pts_2d = [(100.0, 100.0), (300.0, 120.0), (500.0, 110.0)]
    pts_3d = [(51.51, -0.12, 100.0), (51.52, -0.11, 120.0), (51.51, -0.10, 90.0)]
    pose_res = solver.solve_pose_from_correspondences(
        points_2d=pts_2d,
        points_3d=pts_3d,
        image_size=(600, 400),
        init_pos=(51.50, -0.12, 50.0),
        init_heading=45.0,
    )
    assert pose_res["converged"] is True
    assert "heading_deg" in pose_res
    assert "camera_lat" in pose_res


def test_stage4_verification_pipeline(tmp_path):
    job_dir = tmp_path / "job_verif"
    photo_path = tmp_path / "query.jpg"
    im = Image.new("RGB", (400, 300), (70, 120, 80))
    im.save(photo_path, format="JPEG")

    board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")
    board.add_candidate("Highland Peak", level="point", lat=56.5, lon=-4.5, prior=1.0)

    stage4 = Stage4Verification()
    mock_sat = Image.new("RGB", (256, 256), (65, 115, 75))
    summary, board = stage4.process(
        job_dir=job_dir,
        board=board,
        working_image_path=photo_path,
        mock_satellite_img=mock_sat,
        mock_street_results=[],  # No street photos found
    )

    assert "stage4_verification" in board.data["stages_run"]
    assert (job_dir / "verification_results.json").exists()
    assert (job_dir / "satellite_evidence.png").exists()

    # Verify street-level imagery honestly records 'not available'
    street_res = summary["street_level_verification"]
    assert street_res["status"] == "not available"
    assert "No keyless street-level" in street_res["reason"]


def test_stage5_report_generator_and_evidence_types(tmp_path):
    job_dir = tmp_path / "job_report"
    photo_path = tmp_path / "photo.jpg"
    im = Image.new("RGB", (400, 300), (100, 150, 200))
    im.save(photo_path, format="JPEG")

    board = CandidateBoard(photo_path=photo_path, board_path=job_dir / "board.json")
    board.data["photo_sha256"] = "abc123def456"

    # Add candidate with metadata
    board.add_candidate(
        name="Loch Lomond Viewpoint",
        level="point",
        lat=56.1,
        lon=-4.6,
        prior=5.0,
        metadata={"heading": 210.0, "fit_score": 0.88, "radius_km": 2.0},
    )
    board.add_candidate("Alternative Ridge", level="point", lat=56.2, lon=-4.4, prior=2.0)

    # Simulate run stages
    board.data["stages_run"] = [
        "stage0_intake",
        "stage1_clues",
        "stage2_prior",
        "stage3_terrain",
        "stage3_built",
        "stage4_verification",
    ]

    generator = ReportGenerator()
    report_data = generator.process(job_dir, board)

    # 1. Verify files generated
    assert (job_dir / "report.json").exists()
    assert (job_dir / "report.geojson").exists()
    assert (job_dir / "report.md").exists()
    assert (job_dir / "report.html").exists()

    # 2. Verify all four mandatory evidence types are present
    ev = report_data["mandatory_evidence_summary"]
    assert "osm_geometry" in ev
    assert "elevation_skylines" in ev
    assert "satellite_imagery" in ev
    assert "street_level_imagery" in ev

    # 3. Verify GeoJSON structure
    geojson = json.loads((job_dir / "report.geojson").read_text(encoding="utf-8"))
    assert geojson["type"] == "FeatureCollection"
    feat_types = [f["geometry"]["type"] for f in geojson["features"]]
    assert "Point" in feat_types
    assert "Polygon" in feat_types
    assert "LineString" in feat_types

    # 4. Verify Responsible Use Notice in HTML
    html_content = (job_dir / "report.html").read_text(encoding="utf-8")
    assert "Responsible Use Notice" in html_content
    assert "Unlawful surveillance" in html_content


def test_pipeline_orchestrator_fast_path(tmp_path):
    """Test orchestrator fast path when EXIF GPS is present."""
    from geolocator.pipeline.orchestrator import PipelineOrchestrator

    job_dir = tmp_path / "fast_job"
    photo_path = tmp_path / "gps_photo.jpg"
    im = Image.new("RGB", (300, 200), (80, 140, 90))
    im.save(photo_path, format="JPEG")

    # Mock Stage 0 process to return exif_gps
    orchestrator = PipelineOrchestrator()
    orig_stage0_proc = orchestrator.stage0.process

    def mock_stage0(p, jd):
        res, board = orig_stage0_proc(p, jd)
        res["exif_gps"] = [45.4387, 12.3271]
        board.add_candidate("EXIF GPS Location", level="point", lat=45.4387, lon=12.3271, prior=50.0)
        return res, board

    orchestrator.stage0.process = mock_stage0

    progress_log = []
    report = orchestrator.run(
        photo_path=photo_path,
        job_dir=job_dir,
        progress_callback=lambda step, pct: progress_log.append((step, pct)),
    )

    assert report["best_location"]["coordinates"] == [45.4387, 12.3271]
    assert (job_dir / "report.json").exists()
    assert (job_dir / "report.html").exists()
    assert len(progress_log) > 0
