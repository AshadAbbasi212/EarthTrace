import csv
import json
import logging
import sys
import time
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add src to sys.path
sys.path.insert(0, str(Path("src").resolve()))

from geolocator.pipeline.orchestrator import PipelineOrchestrator
from geolocator.pipeline.geo_utils import haversine_distance_km

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("web_10_benchmark")


def main():
    manifest_path = Path("eval/manifest_web_10.csv")
    output_base = Path("eval/results/web_10_run")
    output_base.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print("\n=======================================================")
    print("RUNNING 10-IMAGE ACCURACY BENCHMARK ON NEW WEB PHOTOS")
    print("=======================================================\n")

    orchestrator = PipelineOrchestrator()
    results = []

    for idx, r in enumerate(rows, 1):
        target_id = r["id"]
        name = r["name"]
        country = r["country"]
        true_lat = float(r["true_lat"])
        true_lon = float(r["true_lon"])
        photo_path = Path(r["filepath"])

        print(f"\n[{idx}/10] Evaluating {target_id}: {name} ({country})...")
        print(f"       Ground truth: ({true_lat:.4f}, {true_lon:.4f})")
        print(f"       Photo: {photo_path}")

        item_job = output_base / f"job_{target_id}"
        item_job.mkdir(parents=True, exist_ok=True)

        if (item_job / "report.json").exists():
            print(f"       Found existing report for {target_id}, loading cached result...")
            with open(item_job / "report.json", "r", encoding="utf-8") as rf:
                report = json.load(rf)
            dur = 0.0
        else:
            import shutil
            if item_job.exists():
                shutil.rmtree(item_job, ignore_errors=True)
                item_job.mkdir(parents=True, exist_ok=True)
            t0 = time.time()
            try:
                report = orchestrator.run(
                    photo_path=photo_path,
                    job_dir=item_job,
                    user_hint_text=None,
                )
                dur = time.time() - t0
            except Exception as e:
                logger.error("Pipeline failure on %s: %s", target_id, e, exc_info=True)
                dur = time.time() - t0
                report = {}

        top = report.get("top_hypothesis") or report.get("best_location") or {}
        coords = top.get("coordinates")
        if isinstance(coords, dict):
            est_lat = float(coords.get("latitude") or 0.0)
            est_lon = float(coords.get("longitude") or 0.0)
        elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
            est_lat, est_lon = float(coords[0]), float(coords[1])
        else:
            est_lat, est_lon = 0.0, 0.0

        est_name = top.get("name", "Unknown")
        tier = top.get("confidence_tier", "T6")

        if est_lat == 0.0 and est_lon == 0.0:
            error_km = 20000.0
        else:
            error_km = haversine_distance_km(true_lat, true_lon, est_lat, est_lon)

        ev_summary = report.get("mandatory_evidence_summary", {})
        bldg_count = report.get("building_count", 0)

        record = {
            "id": target_id,
            "target_name": name,
            "country": country,
            "true_lat": true_lat,
            "true_lon": true_lon,
            "pred_name": est_name,
            "pred_lat": est_lat,
            "pred_lon": est_lon,
            "error_km": round(error_km, 2),
            "tier": tier,
            "duration_sec": round(dur, 2),
            "building_count": bldg_count,
            "evidence": ev_summary,
        }
        results.append(record)

        status_icon = "[POINT]" if error_km <= 25.0 else ("[LOCAL]" if error_km <= 200.0 else ("[REGION]" if error_km <= 750.0 else "[MISS]"))
        print(f"       {status_icon} Predicted: {est_name} ({est_lat:.4f}, {est_lon:.4f})")
        print(f"       Distance Error: {error_km:.1f} km | Tier: {tier} | Time: {dur:.1f}s | Buildings: {bldg_count}")

    # Aggregate metrics
    errors = [r["error_km"] for r in results]
    s_errors = sorted(errors)
    n = len(errors)
    median_err = s_errors[n // 2]
    mean_err = sum(errors) / n
    within_25km = sum(1 for e in errors if e <= 25.0) / n * 100.0
    within_200km = sum(1 for e in errors if e <= 200.0) / n * 100.0
    within_750km = sum(1 for e in errors if e <= 750.0) / n * 100.0
    within_2500km = sum(1 for e in errors if e <= 2500.0) / n * 100.0

    print("\n=======================================================")
    print("📊 10-IMAGE BENCHMARK SUMMARY RESULTS")
    print("=======================================================")
    print(f"Total Photos Tested:   {n}")
    print(f"Median Error:          {median_err:.1f} km")
    print(f"Mean Error:            {mean_err:.1f} km")
    print(f"Accuracy <= 25 km:     {within_25km:.1f}%")
    print(f"Accuracy <= 200 km:    {within_200km:.1f}%")
    print(f"Accuracy <= 750 km:    {within_750km:.1f}% (Sub-continental)")
    print(f"Accuracy <= 2500 km:   {within_2500km:.1f}% (Continental)")
    print("-------------------------------------------------------")
    for r in results:
        print(f"  {r['id']:<7} | {r['target_name'][:25]:<25} | Err: {r['error_km']:>7.1f} km | Pred: {r['pred_name'][:30]}")
    print("=======================================================\n")

    summary_file = output_base / "summary.json"
    summary_file.write_text(json.dumps({
        "metrics": {
            "count": n,
            "median_km": round(median_err, 2),
            "mean_km": round(mean_err, 2),
            "pct_25km": within_25km,
            "pct_200km": within_200km,
            "pct_750km": within_750km,
            "pct_2500km": within_2500km,
        },
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"Summary JSON saved to {summary_file}")


if __name__ == "__main__":
    main()
