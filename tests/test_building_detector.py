"""Unit tests for Building and Architectural Facade Detection & Cadastral Matching."""
from pathlib import Path
import json
import pytest
from PIL import Image, ImageDraw

from geolocator.pipeline.building_detector import BuildingDetector
from geolocator.pipeline.stage3_built import Stage3Built
from geolocator.pipeline.board import CandidateBoard


@pytest.fixture
def synthetic_city_image(tmp_path) -> Path:
    """Create a synthetic urban scene with vertical building towers and sky."""
    img_path = tmp_path / "urban_test.jpg"
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color=(135, 206, 235))  # Sky blue
    draw = ImageDraw.Draw(img)

    # Ground street
    draw.rectangle([0, int(h * 0.75), w, h], fill=(60, 60, 60))

    # Building 1: Glass tower (left)
    draw.rectangle([60, int(h * 0.20), 280, int(h * 0.75)], fill=(70, 130, 180))
    for y in range(int(h * 0.22), int(h * 0.73), 25):
        for x in range(75, 265, 30):
            draw.rectangle([x, y, x + 20, y + 15], fill=(200, 240, 255))

    # Building 2: Red brick hotel/edifice (center-right)
    draw.rectangle([340, int(h * 0.28), 580, int(h * 0.75)], fill=(160, 60, 50))
    for y in range(int(h * 0.30), int(h * 0.73), 30):
        for x in range(355, 565, 35):
            draw.rectangle([x, y, x + 22, y + 20], fill=(240, 230, 200))

    # Building 3: Concrete office block (far right)
    draw.rectangle([620, int(h * 0.35), 760, int(h * 0.75)], fill=(180, 180, 180))

    img.save(img_path, quality=90)
    return img_path


def test_building_detection_contours_and_overlay(synthetic_city_image, tmp_path):
    detector = BuildingDetector()
    out_dir = tmp_path / "bldg_output"
    res = detector.detect_building_regions(synthetic_city_image, output_dir=out_dir, max_buildings=4)

    assert res["count"] >= 2, f"Expected at least 2 detected buildings, got {res['count']}"
    assert len(res["buildings"]) >= 2
    assert res["overlay_path"] is not None
    assert Path(res["overlay_path"]).exists()

    # Verify crops exist and have valid aspect ratios
    for b in res["buildings"]:
        assert Path(b["crop_path"]).exists()
        assert b["aspect_ratio"] > 0.0
        assert b["palette"] in ("blue_glass_curtain", "beige_stone", "red_terracotta_brick", "grey_concrete")

    manifest = json.loads((out_dir / "detected_buildings.json").read_text(encoding="utf-8"))
    assert manifest["count"] == res["count"]


def test_building_cadastral_matching():
    detector = BuildingDetector()
    detected_buildings = [
        {
            "id": "bldg_01",
            "classification": "luxury hotel or hospitality building",
            "confidence": 0.88,
            "palette": "beige_stone",
            "ocr_text": "pearl continental",
        },
        {
            "id": "bldg_02",
            "classification": "sports club or cricket pavilion",
            "confidence": 0.75,
            "palette": "red_terracotta_brick",
            "ocr_text": "gymkhana",
        },
    ]

    # Karachi candidate bbox
    karachi_bbox = (24.80, 67.00, 24.90, 67.10)
    matches = detector.match_buildings_against_osm(
        detected_buildings=detected_buildings,
        candidate_bbox=karachi_bbox,
    )

    assert len(matches) >= 1
    matched_names = [m["matched"]["name"] for m in matches]
    # Check that Pearl Continental Hotel or Karachi Gymkhana is matched
    assert any("Pearl Continental" in n or "Gymkhana" in n for n in matched_names)


def test_stage3_built_with_building_detection(synthetic_city_image, tmp_path):
    job_dir = tmp_path / "job_bldg"
    job_dir.mkdir(parents=True)
    board = CandidateBoard(photo_path=synthetic_city_image, board_path=job_dir / "board.json")

    # Add candidate Karachi region and text clues from Stage 1
    board.add_candidate(
        name="Karachi, Pakistan",
        level="city",
        lat=24.8607,
        lon=67.0011,
        prior=1.5,
    )
    board.add_clue(
        text="Hotel view near club road",
        kind="text",
        status="read",
    )

    stage3b = Stage3Built()
    summary, board = stage3b.process(
        job_dir=job_dir,
        board=board,
        image_path=synthetic_city_image,
        search_bbox=(24.82, 67.01, 24.88, 67.06),
    )

    assert "detected_buildings" in summary
    assert summary["building_count"] >= 2
    assert (job_dir / "building_detection_overlay.png").exists()

    # Check candidates on board for Cadastral Building entries
    point_cands = [c for c in board.data["candidates"].values() if c.get("level") == "point"]
    assert len(point_cands) >= 1
    top_pt = point_cands[0]
    assert top_pt["metadata"].get("tier") == "T1"
    assert top_pt["metadata"].get("radius_km") <= 0.05
