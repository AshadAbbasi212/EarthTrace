"""Unit and integration tests for Milestone 10: Evaluation manifest, biome balance, metrics calculation, and calibration."""
import csv
import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from eval.run_eval import compute_metrics


def test_eval_manifest_integrity_and_biome_coverage():
    """Verify eval/manifest.csv exists, has 66 entries, and covers all 11 categories and 7 continents."""
    root = Path(__file__).resolve().parent.parent
    manifest_path = root / "eval" / "manifest.csv"
    photos_dir = root / "eval" / "photos"
    photos_exif_dir = root / "eval" / "photos_exif"

    assert manifest_path.exists(), "eval/manifest.csv must exist"
    assert photos_dir.exists(), "eval/photos/ directory must exist"
    assert photos_exif_dir.exists(), "eval/photos_exif/ directory must exist"

    rows = []
    with open(manifest_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 66, f"Expected 66 entries, found {len(rows)}"

    expected_categories = {
        "urban", "rural_road", "farmland", "coast", "lake_river",
        "mountain", "valley", "desert", "forest", "snow_ice", "island",
    }
    found_categories = set(r["category"] for r in rows)
    assert found_categories == expected_categories, f"Missing categories: {expected_categories - found_categories}"

    # Verify category balance (6 photos per category)
    cat_counts = {}
    for r in rows:
        cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1
    for cat, count in cat_counts.items():
        assert count == 6, f"Category '{cat}' has {count} entries, expected 6"

    # Verify continent coverage (all 7 continents represented)
    expected_continents = {"Europe", "Asia", "North America", "South America", "Africa", "Oceania", "Antarctica"}
    found_continents = set(r["continent"] for r in rows)
    assert expected_continents.issubset(found_continents), f"Missing continents: {expected_continents - found_continents}"

    # Verify photos exist on disk
    for r in rows:
        p = photos_dir / r["file"]
        assert p.exists(), f"Photo {r['file']} does not exist in eval/photos/"
        assert p.stat().st_size > 1000, f"Photo {r['file']} is suspiciously small"


def test_compute_metrics_accuracy():
    """Verify evaluation metric computation against exact reference distributions."""
    errors = [0.5, 2.0, 15.0, 40.0, 120.0, 450.0, 1500.0, 3200.0]
    metrics = compute_metrics(errors)

    assert metrics["count"] == 8
    # Median of [0.5, 2.0, 15.0, 40.0, 120.0, 450.0, 1500.0, 3200.0] is (40.0 + 120.0) / 2 = 80.0
    assert metrics["median_km"] == 80.0
    assert metrics["min_km"] == 0.5
    assert metrics["max_km"] == 3200.0

    # Percentages
    assert metrics["pct_within_1km"] == 12.5     # 1 out of 8 (0.5)
    assert metrics["pct_within_25km"] == 37.5    # 3 out of 8 (0.5, 2.0, 15.0)
    assert metrics["pct_within_200km"] == 62.5   # 5 out of 8 (0.5, 2.0, 15.0, 40.0, 120.0)
    assert metrics["pct_within_750km"] == 75.0   # 6 out of 8
    assert metrics["pct_within_2500km"] == 87.5  # 7 out of 8


def test_empty_metrics():
    """Verify empty input handling."""
    assert compute_metrics([]) == {}
