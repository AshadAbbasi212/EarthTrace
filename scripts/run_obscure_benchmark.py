"""Benchmark test for obscure, lesser-known, non-famous places worldwide.

Loads the 10 authentic, non-famous photographs from eval/photos_obscure/ and eval/manifest_obscure.csv,
runs the full end-to-end geolocation pipeline on local GPU, and computes accuracy metrics,
calibrated error radii, and multimodal evidence usage.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import math
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from geolocator.config import get_config
from geolocator.pipeline.geo_utils import haversine_distance_km
from geolocator.pipeline.orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("obscure_benchmark")


def compute_metrics(errors_km: List[float]) -> Dict[str, float]:
    """Compute error percentiles and milestone distance bands."""
    if not errors_km:
        return {}
    s = sorted(errors_km)
    n = len(s)
    med = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    mean_val = sum(s) / float(n)

    bands = {
        "within_1km_pct": round(sum(1 for e in s if e <= 1.0) / n * 100.0, 1),
        "within_25km_pct": round(sum(1 for e in s if e <= 25.0) / n * 100.0, 1),
        "within_200km_pct": round(sum(1 for e in s if e <= 200.0) / n * 100.0, 1),
        "within_750km_pct": round(sum(1 for e in s if e <= 750.0) / n * 100.0, 1),
        "within_2500km_pct": round(sum(1 for e in s if e <= 2500.0) / n * 100.0, 1),
    }

    return {
        "count": n,
        "median_error_km": round(med, 2),
        "mean_error_km": round(mean_val, 2),
        "min_error_km": round(s[0], 2),
        "max_error_km": round(s[-1], 2),
        **bands,
    }


def main():
    root = Path(__file__).resolve().parent.parent
    manifest_csv = root / "eval" / "manifest_obscure.csv"
    output_dir = root / "eval" / "results" / "obscure_10_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(manifest_csv, "r", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))

    logger.info("Loaded %d obscure photos from %s", len(manifest), manifest_csv)

    config = get_config()
    orchestrator = PipelineOrchestrator(config=config)

    print("\n" + "=" * 115)
    print(f"{'Idx':<3} | {'ID':<6} | {'Location':<24} | {'Country':<10} | {'True Lat/Lon':<19} | {'Est Lat/Lon':<19} | {'Error':<10} | {'Tier/Rad':<12}")
    print("=" * 115)

    results = []
    total_start = time.time()
    calibrated_count = 0
    tier_counts = {}
    evidence_counts = {
        "osm_geometry": {},
        "elevation_skyline": {},
        "satellite_imagery": {},
        "street_imagery": {},
    }

    for idx, item in enumerate(manifest, 1):
        target_id = item["id"]
        name = item["name"]
        country = item["country"]
        cat = item["category"]
        true_lat = float(item["true_lat"])
        true_lon = float(item["true_lon"])
        photo_path = Path(item["filepath"])

        job_dir = output_dir / f"job_{target_id}"
        # Clean previous job dir if any
        if job_dir.exists():
            shutil.rmtree(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.time()

        try:
            report_dict = orchestrator.run(
                photo_path=photo_path,
                job_dir=job_dir,
                user_hint_text=None,  # Pure zero-hint evaluation on raw photo!
            )
        except Exception as err:
            logger.error("Error on %s: %s", target_id, err, exc_info=True)
            report_dict = {
                "top_hypothesis": {
                    "confidence_tier": "T6",
                    "calibrated_radius_km": 1500.0,
                    "coordinates": {"latitude": 0.0, "longitude": 0.0},
                    "rationale": f"Pipeline execution error: {err}",
                },
                "evidence": {},
            }

        dur = time.time() - t0
        top = report_dict.get("top_hypothesis") or {}
        coords = top.get("coordinates") or {}
        est_lat = float(coords.get("latitude", 0.0))
        est_lon = float(coords.get("longitude", 0.0))
        tier = top.get("confidence_tier", "T5")
        radius_km = float(top.get("calibrated_radius_km") or (top.get("error_radius_m", 500000.0) / 1000.0))
        pred_name = top.get("location_name") or top.get("name") or "Estimated Area"
        subdiv = top.get("subnational_division") or ""

        error_km = haversine_distance_km(true_lat, true_lon, est_lat, est_lon)
        is_calibrated = bool(error_km <= radius_km)
        if is_calibrated:
            calibrated_count += 1

        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        ev = report_dict.get("evidence", {})
        for mod in ("osm_geometry", "elevation_skyline", "satellite_imagery", "street_imagery"):
            item_status = ev.get(mod, {}).get("status", "not_applicable").lower()
            evidence_counts[mod][item_status] = evidence_counts[mod].get(item_status, 0) + 1

        print(
            f"{idx:<3} | {target_id:<6} | {name[:24]:<24} | {country[:10]:<10} | "
            f"{true_lat:8.4f}, {true_lon:8.4f} | {est_lat:8.4f}, {est_lon:8.4f} | "
            f"{error_km:7.1f} km | {tier} (±{radius_km:.0f}km) ({dur:.1f}s)"
        )

        results.append({
            "id": target_id,
            "name": name,
            "category": cat,
            "country": country,
            "continent": item["continent"],
            "true_lat": true_lat,
            "true_lon": true_lon,
            "est_lat": est_lat,
            "est_lon": est_lon,
            "pred_name": pred_name,
            "subnational_division": subdiv,
            "error_km": round(error_km, 2),
            "calibrated_radius_km": round(radius_km, 2),
            "tier": tier,
            "is_calibrated": is_calibrated,
            "duration_s": round(dur, 2),
            "evidence": {k: ev.get(k, {}).get("status", "not_applicable") for k in ev},
            "rationale": top.get("rationale") or "",
        })

    print("=" * 115)
    total_dur = time.time() - total_start
    all_errors = [r["error_km"] for r in results]
    metrics = compute_metrics(all_errors)
    metrics["calibration_rate_pct"] = round(calibrated_count / len(results) * 100.0, 1)

    summary = {
        "benchmark_title": "10-Photo Obscure and Non-Famous Real-World Locations Benchmark",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_evaluated": len(results),
        "total_duration_s": round(total_dur, 2),
        "avg_duration_s": round(total_dur / len(results), 2),
        "overall_metrics": metrics,
        "tier_distribution": tier_counts,
        "evidence_counts": evidence_counts,
        "items": results,
    }

    report_json_path = output_dir / "obscure_10_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    report_md_path = output_dir / "obscure_10_summary.md"
    generate_markdown_report(summary, report_md_path)

    logger.info("Obscure benchmark complete! Report saved to %s", report_md_path)


def generate_markdown_report(summary: Dict[str, Any], output_path: Path):
    """Render executive Markdown report."""
    ov = summary.get("overall_metrics", {})
    items = summary.get("items", [])

    lines = [
        "# Benchmark: Geolocation of 10 Obscure & Non-Famous Places from the Internet",
        "",
        f"**Date:** {summary.get('date')}",
        f"**Test Set:** 10 authentic photographs of lesser-known rural towns, country roads, local rivers, and remote settlements across 6 continents.",
        f"**Condition:** 100% EXIF stripped, zero user hints (`user_hints=None`), local NVIDIA GPU execution, zero paid APIs.",
        "",
        "## Executive Summary",
        "",
        f"- **Median Localization Error:** `{ov.get('median_error_km', 0):.1f} km`",
        f"- **Mean Localization Error:** `{ov.get('mean_error_km', 0):.1f} km`",
        f"- **Error Range:** `{ov.get('min_error_km', 0):.1f} km` to `{ov.get('max_error_km', 0):.1f} km`",
        f"- **Calibration Rate (Error $\le$ Radius):** `{ov.get('calibration_rate_pct', 0):.1f}%`",
        f"- **Local/Regional Accuracy ($\le$ 200 km):** `{ov.get('within_200km_pct', 0):.1f}%`",
        f"- **Sub-continental Accuracy ($\le$ 750 km):** `{ov.get('within_750km_pct', 0):.1f}%`",
        f"- **Continental Accuracy ($\le$ 2,500 km):** `{ov.get('within_2500km_pct', 0):.1f}%`",
        "",
        "## Detailed Results Table",
        "",
        "| ID | Location | True Country | Pred Country / Area | True (Lat, Lon) | Pred (Lat, Lon) | Error (km) | Tier | Calibrated? |",
        "|:---|:---|:---|:---|:---|:---|:---:|:---:|:---:|",
    ]

    for it in items:
        calib_str = "✅ Yes" if it["is_calibrated"] else "❌ No"
        lines.append(
            f"| `{it['id']}` | **{it['name']}** | {it['country']} | {it['pred_name'][:25]} | "
            f"({it['true_lat']:.4f}, {it['true_lon']:.4f}) | ({it['est_lat']:.4f}, {it['est_lon']:.4f}) | "
            f"**{it['error_km']:.1f}** | `{it['tier']}` (±{it['calibrated_radius_km']:.0f}km) | {calib_str} |"
        )

    lines.extend([
        "",
        "## Evidence Pillars Used",
        "",
        "| ID | Location | OSM Geometry | Elevation Skyline | Satellite Orthophoto | Street-Level Imagery |",
        "|:---|:---|:---:|:---:|:---:|:---:|",
    ])

    for it in items:
        ev = it.get("evidence", {})
        lines.append(
            f"| `{it['id']}` | {it['name']} | `{ev.get('osm_geometry', 'n/a')}` | `{ev.get('elevation_skyline', 'n/a')}` | `{ev.get('satellite_imagery', 'n/a')}` | `{ev.get('street_imagery', 'n/a')}` |"
        )

    lines.extend([
        "",
        "## Detailed Case-by-Case Analysis",
        "",
    ])

    for it in items:
        lines.extend([
            f"### `{it['id']}`: {it['name']} ({it['country']})",
            f"- **Category / Environment:** {it['category']} ({it['continent']})",
            f"- **True Coordinates:** `{it['true_lat']:.4f}, {it['true_lon']:.4f}`",
            f"- **Estimated Coordinates:** `{it['est_lat']:.4f}, {it['est_lon']:.4f}`",
            f"- **Error Distance:** `{it['error_km']:.1f} km`",
            f"- **Confidence Tier:** `{it['tier']}` (Calibrated Radius: `±{it['calibrated_radius_km']:.0f} km`)",
            f"- **Calibration Assessment:** {'Error within calibrated confidence bounds.' if it['is_calibrated'] else 'Error exceeded confidence radius.'}",
            f"- **Forensic Rationale:** {it.get('rationale', 'N/A')}",
            "",
        ])

    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
