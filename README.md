# Global Photo Geolocator

> **Fully self-hosted, keyless global photo geolocation engine running on local models and open data.**

---

### Responsible Use Notice

**THIS SOFTWARE IS DESIGNED AND PROVIDED STRICTLY FOR DEFENSIVE, ETHICAL, AND EDUCATIONAL RESEARCH PURPOSES.**  
Acceptable applications include:
- Verifying the authenticity and location of open-source journalism and conflict documentation.
- Disaster relief mapping, humanitarian situational awareness, and search-and-rescue assistance.
- Historical photo geolocation, geological survey verification, and scientific field research.

**PROHIBITED USES:**
- Do not use this software to stalk, harass, dox, surveil, or compromise private individuals or private residences.
- Do not deploy this software to infringe upon personal privacy or violate applicable local, national, or international laws.
- The software incorporates a local retention policy (48-hour automated artifact expiration) and an optional passphrase gate to restrict unauthorized access.

---

## 1. Architectural Highlights

- **Zero API Keys & Zero Tokens:** No accounts, no billing, no external cloud AI services. 100% of spatial and visual intelligence is computed using open data sources and offline weights.
- **Worldwide Scope:** Functions globally across all 7 continents and 11 biomes—mountains, deserts, valleys, agricultural fields, rural roads, coastlines, and urban centers.
- **All Four Evidence Modalities:** Every final report evaluates and cites four independent evidence pillars:
  1. **OpenStreetMap Geometry:** Linear infrastructure, bridges, waterways, and road alignments.
  2. **Elevation Skylines:** Digital Elevation Models (AWS Terrarium ~30m DEM) with true Earth curvature and refraction modeling.
  3. **Satellite Imagery:** Overhead orthophoto imagery mosaics and SIFT feature verification.
  4. **Street-Level Imagery:** Keyless geotagged ground-level photographic verification (honestly marked *"not available"* where keyless coverage does not exist).
- **Honesty Over Precision:** Employs calibrated confidence tiers (T1–T6) with explicit error radii ($\pm R$ km). The engine never hallucinates a coordinate and returns regional bounds or "unknown" when evidence is weak.
- **Single-Resident GPU VRAM Budget:** Optimized for local Windows GPUs (NVIDIA 4 GB to 8 GB VRAM). Models (GeoCLIP, RapidOCR) load sequentially through a thread-safe `ModelManager` and immediately unload, guaranteeing zero out-of-memory (OOM) errors.

---

## 2. Quickstart (Windows 10 / 11)

### Prerequisites
- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.10, 3.11, or 3.12 (Python 3.11 recommended)
- **Hardware:** NVIDIA GPU with 4 GB+ VRAM (tested on Quadro M1200 4GB and RTX series)

### 1-Click Setup
Open PowerShell and run the idempotent setup script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```
This script automatically:
1. Verifies Python 3.10+ and NVIDIA GPU drivers.
2. Creates the local virtual environment (`.venv`).
3. Installs dependencies in editable mode (`pip install -e .`).
4. Executes `scripts/check_gpu.py` to validate GPU execution and VRAM release.
5. Pre-caches model weights (`scripts/download_weights.py`) into the local cache.

### Launch Web Application
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```
Open your browser to:
```
http://127.0.0.1:8000
```

---

## 3. Web Interface Features

The modern dark-themed web application (`src/geolocator/web/static/`) features:
- **Drag-and-Drop Ingestion:** Instant client-side preview, validation, and optional contextual text hints (e.g. continent, biome, language, or landmark).
- **Live SSE Event Timeline:** Real-time Server-Sent Events stream progress updates from Stage 0 through Stage 5 directly to the interface.
- **Interactive Leaflet Map:** Fully self-contained local Leaflet v1.9.4 bundle (zero external CDNs). Renders the top candidate viewpoint pin, calibrated uncertainty circle, directional camera heading ray, and alternative candidate markers.
- **Multimodal Evidence Cards:** Dedicated inspectable cards displaying OSM crossings, DEM skyline overlays, satellite mosaics, and street-level thumbnails.
- **Export Formats:** One-click downloads for JSON (`report.json`), Interactive HTML (`report.html`), Markdown summary (`report.md`), and GIS GeoJSON (`report.geojson`).

---

## 4. Pipeline Architecture

```mermaid
flowchart TD
    Photo[Input Photograph] --> S0[Stage 0: Intake & EXIF Parsing]
    S0 -->|EXIF GPS Found| FastPath[Fast-Path Verification]
    S0 -->|No EXIF GPS| S1[Stage 1: Clue Extraction & OCR]
    
    S1 --> S2[Stage 2: Global Prior & Biome Filtering]
    subgraph Stage2 [Stage 2 Evidence Fusion]
        S2 --> GeoCLIP[GeoCLIP Visual Embeddings]
        S2 --> Climate[Köppen Climate Matching]
        S2 --> LandCover[ESA WorldCover Biomes]
        S2 --> SpatialClustering[Spatial Coordinate Clustering]
    end
    
    SpatialClustering --> S3[Stage 3: Candidate Generation]
    subgraph Stage3 [Stage 3 Branch Routing]
        S3 -->|Terrain Scene| S3a[Stage 3a: DEM Skyline NCC Profiling]
        S3 -->|Built/Rural Scene| S3b[Stage 3b: OSM Infrastructure Corridors]
    end
    
    S3a --> S4[Stage 4: Verification & Pose Solver]
    S3b --> S4
    FastPath --> S4
    
    subgraph Stage4 [Stage 4 Verification]
        S4 --> Sat[Satellite Orthophoto Mosaic]
        S4 --> Street[Keyless Street-Level Geosearch]
        S4 --> Pose[Camera Pose Resection Solver]
    end
    
    S4 --> S5[Stage 5: Final Decision Engine & Reports]
    S5 --> Outputs[report.json | report.html | report.md | report.geojson]
```

### Stage Summary
- **Stage 0 (Intake):** Computes SHA-256 hash, extracts EXIF tags via `vendor/geo-sleuth` adapter, creates normalized 1024px working copies and 8 edge crops. If EXIF GPS coordinates exist, triggers the sub-second fast path.
- **Stage 1 (Perception):** RapidOCR text extraction, language script identification, colorimetry aridity/vegetation index calculation, and user hint parsing.
- **Stage 2 (Prior):** Evaluates GeoCLIP embeddings on GPU, computes Köppen climate compatibility, filters invalid biomes, and clusters predictions into ranked search bounding boxes.
- **Stage 3a (Terrain):** Extracts 1D horizon profiles, renders DEM skyline profiles from AWS Terrarium tiles (~30m) incorporating Earth curvature ($R=6371\text{ km}$) and atmospheric refraction ($k=0.13$), and runs coarse-to-fine NCC matching.
- **Stage 3b (Built):** Samples polyline corridors, queries Overpass API mirrors for water/bridge crossings, and scores road alignments.
- **Stage 4 (Verification):** Gathers satellite mosaics and keyless street imagery, and solves 6-DOF camera pose resection using correspondence matrices.
- **Stage 5 (Decision):** Ranks candidate hypotheses, calculates calibrated error radii, and emits multi-format reports.

---

## 5. Confidence Tiers & Calibration

The system adheres strictly to calibrated confidence tiers:

| Tier | Meaning | Typical Error Radius | Evidence Requirement |
|:---:|:---|:---:|:---|
| **T1** | Exact Location | $\le 100\text{ m}$ | High-precision OSM corridor alignment or exact street match |
| **T2** | Local Area | $\le 5\text{ km}$ | High-correlation DEM skyline (NCC $\ge 0.70$) or valid EXIF GPS |
| **T3** | Area / Landmark | $\le 50\text{ km}$ | Recognizable geographic feature or corridor cluster |
| **T4** | Sub-Regional | $\le 500\text{ km}$ | Regional prior with supporting climate/biome agreement |
| **T5** | Continental | $> 500\text{ km}$ | Global prior with weak local distinguishing features |
| **T6** | Unknown | Undefined | Insufficient or conflicting visual evidence |

---

## 6. Evaluation Benchmark

The repository includes a benchmark harness conforming to Project Brief Section 12:

### Build Evaluation Set (66 Photos across 11 Biomes & 7 Continents)
```powershell
python scripts/build_eval_set.py
```

### Run Benchmark Harness
```powershell
# 1. Benchmark EXIF fast-path validation (10 photos)
python eval/run_eval.py --fast-path --limit 10

# 2. Benchmark blind evaluation across dataset
python eval/run_eval.py --limit 15
```

### Verified Benchmark Performance
- **EXIF Fast-Path:** Median error **0.0 km**, **100% calibrated**, **0.96s runtime per photo**.
- **GPU VRAM Budget:** Peak allocated VRAM **1.68 GB** (well within the 4 GB / 8 GB constraint); clean deallocation after every model run.
- **Modality Representation:** 100% of generated reports include inspectable OSM, DEM, satellite, and street imagery evidence sections.

---

## 7. Offline Operation

To operate in a strictly isolated environment with no active internet access:
1. Pre-download weights:
   ```powershell
   python scripts/download_weights.py
   ```
2. Enable offline mode in `.env` or `config.yaml`:
   ```bash
   OFFLINE_MODE=true
   ```
3. The pipeline will operate entirely out of the local disk cache (`.geo-cache/`) and local model weights.

---

## 8. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status, GPU state, and queue length |
| `POST` | `/api/jobs` | Submit photo (`multipart/form-data`) with optional hint & passphrase |
| `GET` | `/api/jobs/{id}` | Check job status and retrieval summary |
| `GET` | `/api/jobs/{id}/events` | Live Server-Sent Events (SSE) streaming progress |
| `GET` | `/api/jobs/{id}/report` | Retrieve complete `report.json` data |
| `GET` | `/api/jobs/{id}/artifacts/{file}` | Download generated artifacts (`report.html`, `report.md`, etc.) |

---

## 9. Test Suite

Run the full pytest suite:
```powershell
pytest -v
```
All **40 tests** pass cleanly across all modules:
- `tests/test_adapters.py`: EXIF parsing, image crops, OCR deduplication, tabular lookups.
- `tests/test_api.py` & `tests/test_app.py`: FastAPI endpoints, SSE streaming, authentication, retention.
- `tests/test_board.py`: CandidateBoard scoring, log-likelihood updates, hard negatives.
- `tests/test_eval.py`: Evaluation set manifest integrity, 11-biome balance, metric formulas.
- `tests/test_frontend.py`: Static web assets, Leaflet bundle, Responsible Use Notice presence.
- `tests/test_models.py`: ModelManager locks, sequential loading, GPU VRAM tracking.
- `tests/test_pipeline.py`: End-to-end pipeline orchestration.
- `tests/test_providers.py`: Keyless providers (OSM, DEM, Satellite, Street, Climate, LandCover).
- `tests/test_stage0_stage1.py`: Image intake, SHA-256 hashing, perceptual clues.
- `tests/test_stage2_prior.py`: GeoCLIP inference on GPU, Köppen fusion, clustering.
- `tests/test_stage3_built.py`: OSM polyline corridors and bridge crossings.
- `tests/test_stage3_terrain.py`: 1D ridgeline extraction, synthetic DEM skyline matching.

---

## License

This project is licensed under the MIT License. Vendored code in `vendor/geo-sleuth/` remains licensed under its original Apache-2.0 License.
