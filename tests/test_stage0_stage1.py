"""Unit and integration tests for Stage 0 (Intake) and Stage 1 (Clues/Perception)."""
import json
import pytest
from pathlib import Path
from PIL import Image

from geolocator.pipeline.board import CandidateBoard
from geolocator.pipeline.stage0_intake import Stage0Intake
from geolocator.pipeline.stage1_clues import Stage1Clues
from geolocator.pipeline.schema import ClueExtractionResult
from geolocator.pipeline.hint_parser import HintParser
from geolocator.adapters.clues_adapter import lookup_plate, lookup_driving_side, lookup_calling_code


def test_hint_parser():
    parser = HintParser()
    res = parser.parse("I took this photo somewhere in Italy near Lake Como in summer")
    assert "Italy" in res["countries"]
    assert res["season"] == "summer"
    assert "Lake Como" in res["landmarks"]

    res2 = parser.parse("Desert highway in Australia, driving left")
    assert "Australia" in res2["countries"]


def test_tabular_lookups():
    # Driving side
    assert lookup_driving_side("United Kingdom") == "left"
    assert lookup_driving_side("Germany") == "right"
    assert lookup_driving_side("Japan") == "left"

    # Calling code
    cc = lookup_calling_code("+33")
    assert cc is not None
    assert cc.get("country") == "France"


def test_geoguessr_meta_lookups():
    from geolocator.adapters import (
        detect_script,
        detect_tld,
        detect_calling_code,
        extract_candidate_place_phrases,
    )

    # 1. Scripts
    cyr = detect_script("Улица Ленина 12")
    assert cyr is not None
    assert cyr["script"] == "cyrillic"
    assert "Russia" in cyr["candidate_countries"]

    kana = detect_script("ラーメン 新宿駅")
    assert kana is not None
    assert kana["script"] == "japanese_kana"
    assert "Japan" in kana["candidate_countries"]

    hangul = detect_script("서울특별시 강남구")
    assert hangul is not None
    assert hangul["script"] == "hangul"
    assert "South Korea" in hangul["candidate_countries"]

    # 2. TLDs
    tld1 = detect_tld("visit www.hotel-alpine.at for details")
    assert tld1 is not None
    assert tld1["country"] == "Austria"
    assert tld1["tld"] == "at"

    tld2 = detect_tld("contato@empresa.com.br")
    assert tld2 is not None
    assert tld2["country"] == "Brazil"
    assert tld2["tld"] == "com.br"

    # 3. Calling codes
    call1 = detect_calling_code("Call +43 1 234567")
    assert call1 is not None
    assert call1["country"] == "Austria"

    # 4. Place phrases
    phrases = extract_candidate_place_phrases("Welcome to San Pedro on Route 66")
    assert any("San Pedro" in p for p in phrases) or any("Route" in p for p in phrases)


def test_candidate_board_operations(tmp_path):
    board = CandidateBoard(photo_path=tmp_path / "test.jpg", board_path=tmp_path / "board.json")
    
    # Add candidate
    board.add_candidate("France", level="country", prior=1.0)
    board.add_candidate("Germany", level="country", prior=1.0)
    
    # Add clue
    cid = board.add_clue(text="Eiffel Tower visible", kind="landmark", status="observed")
    
    # Add evidence supporting France, opposing Germany
    board.add_evidence(cid, {"France": 4.0, "Germany": 0.25}, rationale="Visual landmark match")
    
    ranked = board.rank()
    assert ranked[0]["name"] == "France"
    assert ranked[1]["name"] == "Germany"

    # Save and reload
    saved_path = board.save()
    reloaded = CandidateBoard.load(saved_path)
    assert len(reloaded.rank()) == 2
    assert reloaded.rank()[0]["name"] == "France"


def test_stage0_and_stage1_pipeline(tmp_path):
    job_dir = tmp_path / "job_001"
    
    # Create synthetic test photo (green field with blue sky)
    test_photo = tmp_path / "camera_shot.jpg"
    im = Image.new("RGB", (1200, 800), (40, 160, 40))
    im.save(test_photo, format="JPEG")

    # Run Stage 0
    stage0 = Stage0Intake()
    intake_summary, board = stage0.process(test_photo, job_dir)

    assert intake_summary["sha256"] is not None
    assert intake_summary["dimensions"] == [1200, 800]
    assert Path(intake_summary["working_1024"]).exists()
    assert Path(intake_summary["working_512"]).exists()
    assert intake_summary["edge_crops_count"] == 8

    # Run Stage 1 with user hint
    stage1 = Stage1Clues()
    clues_res, board = stage1.process(job_dir, board, user_hint_text="In the Scottish Highlands, United Kingdom")

    assert isinstance(clues_res, ClueExtractionResult)
    assert "stage0_intake" in board.data["stages_run"]
    assert "stage1_clues" in board.data["stages_run"]
    assert "United Kingdom" in board.data["candidates"]
    assert (job_dir / "clues.json").exists()
