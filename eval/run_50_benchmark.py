"""50-Photo Global Benchmark Evaluation Script.

Selects 50 diverse images across all 11 biomes and all 7 continents,
runs the complete geolocation pipeline on local GPU, and generates
a comprehensive performance report with metric breakdowns.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

# Ensure UTF-8 stdout on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from geolocator.config import get_config
from geolocator.pipeline.geo_utils import haversine_distance_km
from geolocator.pipeline.orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_50")


def select_50_photos(manifest_path: Path) -> List[Dict[str, str]]:
    """Select exactly 50 photos balanced across 11 biomes and all continents."""
    with open(manifest_path, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # Group by category
    by_category: Dict[str, List[Dict[str, str]]] = {}
    for r in reader:
        cat = r.get("category", "unknown")
        by_category.setdefault(cat, []).append(r)

    selected: List[Dict[str, str]] = []
    # 11 categories: pick 5 from the first 6 categories (30), and 4 from the remaining 5 (20) = 50 total
    categories = list(by_category.keys())
    for idx, cat in enumerate(categories):
        items = by_category[cat]
        quota = 5 if idx < 6 else 4
        selected.extend(items[:quota])

    return selected[:50]


def compute_metrics(errors_km: List[float]) -> Dict[str, float]:
    """Compute error percentiles and milestone distance bands."""
    if not errors_km:
        return {}
    s = sorted(errors_km)
    n = len(s)
    median = s[n // 2] if n % 2 != 0 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    mean = sum(s) / n

    def pct_within(threshold_km: float) -> float:
        return round((sum(1 for e in s if e <= threshold_km) / n) * 100.0, 1)

    return {
        "count": n,
        "median_km": round(median, 2),
        "mean_km": round(mean, 2),
        "min_km": round(s[0], 2),
        "max_km": round(s[-1], 2),
        "pct_within_1km": pct_within(1.0),
        "pct_within_25km": pct_within(25.0),
        "pct_within_200km": pct_within(200.0),
        "pct_within_750km": pct_within(750.0),
        "pct_within_2500km": pct_within(2500.0),
    }


def main():
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "eval" / "manifest.csv"
    photos_dir = repo_root / "eval" / "photos"
    output_dir = repo_root / "eval" / "results" / "benchmark_50"
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_rows = select_50_photos(manifest_path)
    logger.info("Selected %d test photos across %d biomes for global evaluation",
                len(selected_rows), len(set(r["category"] for r in selected_rows)))

    orchestrator = PipelineOrchestrator()
    results: List[Dict[str, Any]] = []
    categories_data: Dict[str, List[float]] = {}
    tier_counts: Dict[str, int] = {"T1": 0, "T2": 0, "T3": 0, "T4": 0, "T5": 0, "T6": 0}
    evidence_counts: Dict[str, Dict[str, int]] = {
        "osm_geometry": {"used": 0, "not_available": 0, "not_applicable": 0},
        "elevation_skyline": {"used": 0, "not_available": 0, "not_applicable": 0},
        "satellite_imagery": {"used": 0, "not_available": 0, "not_applicable": 0},
        "street_imagery": {"used": 0, "not_available": 0, "not_applicable": 0},
    }

    calibrated_matches = 0
    total_start = time.time()
    peak_vram_mb = 0.0

    print("=" * 105)
    print(f"{'#':<3} | {'ID':<7} | {'Name':<24} | {'Category':<11} | {'True Lat/Lon':<19} | {'Pred Lat/Lon':<19} | {'Error (km)':<10} | {'Tier'}")
    print("=" * 105)

    for idx, row in enumerate(selected_rows, 1):
        target_id = row["id"]
        filename = row["file"]
        true_lat = float(row["lat"])
        true_lon = float(row["lon"])
        category = row.get("category", "unknown")
        continent = row.get("continent", "unknown")
        name = row.get("name", filename)

        photo_path = photos_dir / filename
        if not photo_path.exists():
            logger.warning("Photo not found: %s, skipping", photo_path)
            continue

        item_job_dir = output_dir / f"job_{target_id}"
        item_job_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.time()
        try:
            report = orchestrator.run(
                photo_path=photo_path,
                job_dir=item_job_dir,
                user_hint_text=None,
            )
            dur = time.time() - t0
        except Exception as err:
            logger.error("Error evaluating %s: %s", target_id, err, exc_info=True)
            dur = time.time() - t0
            report = {
                "top_hypothesis": {
                    "confidence_tier": "T6",
                    "error_radius_m": 1000000.0,
                    "coordinates": {"latitude": 0.0, "longitude": 0.0},
                    "rationale": f"Execution error: {err}",
                },
                "evidence": {},
            }

        top = report.get("top_hypothesis") or report.get("best_location") or {}
        coords = top.get("coordinates")
        if isinstance(coords, dict):
            est_lat = float(coords.get("latitude") or 0.0)
            est_lon = float(coords.get("longitude") or 0.0)
        elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
            est_lat, est_lon = float(coords[0]), float(coords[1])
        else:
            est_lat, est_lon = 0.0, 0.0

        tier = top.get("confidence_tier", "T6")
        radius_km = top.get("calibrated_radius_km") or (top.get("error_radius_m", 500000.0) / 1000.0)

        error_km = haversine_distance_km(true_lat, true_lon, est_lat, est_lon)
        is_calibrated = error_km <= radius_km
        if is_calibrated:
            calibrated_matches += 1

        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        categories_data.setdefault(category, []).append(error_km)

        ev = report.get("evidence", {})
        for mod in ("osm_geometry", "elevation_skyline", "satellite_imagery", "street_imagery"):
            item_status = ev.get(mod, {}).get("status", "not_applicable").lower()
            if item_status not in evidence_counts[mod]:
                evidence_counts[mod][item_status] = 0
            evidence_counts[mod][item_status] += 1

        if torch.cuda.is_available():
            mem = torch.cuda.max_memory_allocated() / (1024 * 1024)
            if mem > peak_vram_mb:
                peak_vram_mb = mem

        print(f"{idx:<3} | {target_id:<7} | {name[:24]:<24} | {category[:11]:<11} | {true_lat:8.4f}, {true_lon:8.4f} | {est_lat:8.4f}, {est_lon:8.4f} | {error_km:8.1f} km | {tier} ({dur:.1f}s)")

        results.append({
            "id": target_id,
            "name": name,
            "category": category,
            "continent": continent,
            "true_lat": true_lat,
            "true_lon": true_lon,
            "est_lat": est_lat,
            "est_lon": est_lon,
            "error_km": round(error_km, 2),
            "tier": tier,
            "radius_km": round(radius_km, 2),
            "is_calibrated": is_calibrated,
            "duration_s": round(dur, 2),
            "evidence": {
                k: ev.get(k, {}).get("status", "not_applicable") for k in ev
            },
        })

    print("=" * 105)

    total_dur = time.time() - total_start
    all_errors = [r["error_km"] for r in results]
    overall_metrics = compute_metrics(all_errors)
    overall_metrics["calibration_rate_pct"] = round((calibrated_matches / len(results) * 100.0) if results else 0.0, 1)

    category_metrics = {}
    for cat, errs in categories_data.items():
        category_metrics[cat] = compute_metrics(errs)

    benchmark_summary = {
        "total_evaluated": len(results),
        "total_duration_s": round(total_dur, 2),
        "avg_duration_per_photo_s": round(total_dur / len(results), 2) if results else 0.0,
        "peak_vram_mb": round(peak_vram_mb, 2),
        "overall": overall_metrics,
        "by_category": category_metrics,
        "tier_distribution": tier_counts,
        "evidence_coverage": evidence_counts,
        "items": results,
    }

    # Save JSON Report
    json_path = output_dir / "benchmark_50_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    # Save Markdown Report
    md_path = output_dir / "benchmark_50_summary.md"
    generate_markdown_report(benchmark_summary, md_path)

    logger.info("50-Photo Benchmark Complete. Results saved to %s and %s", json_path, md_path)


def generate_markdown_report(summary: Dict[str, Any], output_path: Path):
    """Generate Markdown report for the 50-photo test."""
    ov = summary.get("overall", {})
    tiers = summary.get("tier_distribution", {})
    ev = summary.get("evidence_coverage", {})
    by_cat = summary.get("by_category", {})
    items = summary.get("items", [])

    lines = [
        "# 50-Photo Global Geolocator Benchmark Report",
        "",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Photos Evaluated:** {summary.get('total_evaluated', 0)}",
        f"**Total Execution Time:** {summary.get('total_duration_s', 0):.1f} s ({summary.get('avg_duration_per_photo_s', 0):.2f} s/photo)",
        f"**Peak VRAM Usage:** {summary.get('peak_vram_mb', 0.0):.1f} MB (Quadro M1200 VRAM-safe single resident execution)",
        "",
        "## 1. Overall Key Performance Indicators",
        "",
        "| Metric | Value | Description |",
        "|--------|-------|-------------|",
        f"| **Median Error** | **{ov.get('median_km', 0.0)} km** | 50th percentile localization error |",
        f"| **Mean Error** | **{ov.get('mean_km', 0.0)} km** | Average global error across all biomes |",
        f"| **Within 1 km (Exact Mark)** | **{ov.get('pct_within_1km', 0.0)}%** | Pinpoint/street/cadastral accuracy |",
        f"| **Within 25 km (Local Area)** | **{ov.get('pct_within_25km', 0.0)}%** | City/valley/mountain range scale |",
        f"| **Within 200 km (Regional)** | **{ov.get('pct_within_200km', 0.0)}%** | Province/state level accuracy |",
        f"| **Within 750 km (Sub-continental)** | **{ov.get('pct_within_750km', 0.0)}%** | Sub-continental zone accuracy |",
        f"| **Within 2500 km (Continental)** | **{ov.get('pct_within_2500km', 0.0)}%** | Continental prior accuracy |",
        f"| **Honest Calibration Rate** | **{ov.get('calibration_rate_pct', 0.0)}%** | Ground truth within predicted error radius |",
        "",
        "## 2. Accuracy Breakdown by Biome / Category",
        "",
        "| Biome / Category | Count | Median Error (km) | Mean Error (km) | <= 25 km (%) | <= 200 km (%) |",
        "|------------------|-------|-------------------|-----------------|--------------|---------------|",
    ]

    for cat, m in sorted(by_cat.items()):
        lines.append(
            f"| `{cat}` | {m.get('count', 0)} | {m.get('median_km', 0.0):.1f} | {m.get('mean_km', 0.0):.1f} | {m.get('pct_within_25km', 0.0)}% | {m.get('pct_within_200km', 0.0)}% |"
        )

    lines.extend([
        "",
        "## 3. Four Evidence Types Audit",
        "",
        "| Modality | Used | Not Applicable | Not Available |",
        "|----------|------|----------------|---------------|",
        f"| **OpenStreetMap Geometry** | {ev.get('osm_geometry', {}).get('used', 0)} | {ev.get('osm_geometry', {}).get('not_applicable', 0)} | {ev.get('osm_geometry', {}).get('not_available', 0)} |",
        f"| **Elevation Skylines (DEM)** | {ev.get('elevation_skyline', {}).get('used', 0)} | {ev.get('elevation_skyline', {}).get('not_applicable', 0)} | {ev.get('elevation_skyline', {}).get('not_available', 0)} |",
        f"| **Satellite Imagery** | {ev.get('satellite_imagery', {}).get('used', 0)} | {ev.get('satellite_imagery', {}).get('not_applicable', 0)} | {ev.get('satellite_imagery', {}).get('not_available', 0)} |",
        f"| **Street-Level Imagery** | {ev.get('street_imagery', {}).get('used', 0)} | {ev.get('street_imagery', {}).get('not_applicable', 0)} | {ev.get('street_imagery', {}).get('not_available', 0)} |",
        "",
        "## 4. Confidence Tier Distribution",
        "",
        "| Tier | Definition | Count | Share (%) |",
        "|------|------------|-------|-----------|",
        f"| **T1** | Exact building/cadastral (radius <= 1.5 km) | {tiers.get('T1', 0)} | {tiers.get('T1', 0)/len(items)*100:.1f}% |",
        f"| **T2** | Street corridor / Landmark (radius <= 10 km) | {tiers.get('T2', 0)} | {tiers.get('T2', 0)/len(items)*100:.1f}% |",
        f"| **T3** | City / Mountain valley (radius <= 25 km) | {tiers.get('T3', 0)} | {tiers.get('T3', 0)/len(items)*100:.1f}% |",
        f"| **T4** | Sub-region / Province (radius <= 150 km) | {tiers.get('T4', 0)} | {tiers.get('T4', 0)/len(items)*100:.1f}% |",
        f"| **T5** | Macro-region / Country (radius <= 1500 km) | {tiers.get('T5', 0)} | {tiers.get('T5', 0)/len(items)*100:.1f}% |",
        f"| **T6** | Unknown / Insufficient signal | {tiers.get('T6', 0)} | {tiers.get('T6', 0)/len(items)*100:.1f}% |",
        "",
        "## 5. Detailed Test Sample Log (All 50 Images)",
        "",
        "| # | ID | Name | Category | Continent | Ground Truth | Prediction | Error (km) | Tier | Calibrated? |",
        "|---|---|------|----------|-----------|--------------|------------|------------|------|-------------|",
    ])

    for idx, it in enumerate(items, 1):
        cal_str = "PASS" if it["is_calibrated"] else "FAIL"
        lines.append(
            f"| {idx} | `{it['id']}` | {it['name']} | `{it['category']}` | {it['continent']} | {it['true_lat']:.4f}, {it['true_lon']:.4f} | {it['est_lat']:.4f}, {it['est_lon']:.4f} | **{it['error_km']:.1f}** | {it['tier']} | {cal_str} |"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
