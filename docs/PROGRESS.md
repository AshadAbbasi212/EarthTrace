# Project Progress Log

## Milestone Status Overview

| Milestone | Title | Status | Completion Date | Git Commit |
|-----------|-------|--------|-----------------|------------|
| **M0** | Environment and Audit | **Completed** | 2026-10-08 | `a250c83` |
| **M1** | Project Skeleton & ModelManager | **Completed** | 2026-10-08 | `dfe48fc` |
| **M2** | Keyless Data Providers & Caching | **Completed** | 2026-10-08 | `1786615` |
| **M3** | Stage 0 (Intake) & Stage 1 (Clues/VLM) | **Completed** | 2026-10-08 | `c4b9278` |
| **M4** | Stage 2 (Global Prior & Biomes) | **Completed** | 2026-10-08 | `3863b20` |
| **M5** | Stage 3a (Natural Terrain Branch & DEM Skylines) | **Completed** | 2026-10-08 | Pending |
| **M6** | Stage 3b (Built/Rural & Coastal Branches) | Planned | - | - |
| **M7** | Stage 4 & 5 (Verification, Pose & Decision Report) | Planned | - | - |
| **M8** | Backend API, Queue, SQLite & Retention | Planned | - | - |
| **M9** | Frontend Web UI, Leaflet Map & Timeline | Planned | - | - |
| **M10** | Evaluation Set, Calibration & Tuning | Planned | - | - |
| **M11** | Packaging, Windows Scripts & Verification | Planned | - | - |

---

## Detailed Milestone Logs

### Milestone 0: Environment and Audit (Completed)
- [x] Initialized Git repository and created baseline `.gitignore`.
- [x] Detected host system specifications: Windows 10/11, Python 3.11.9, NVIDIA Quadro M1200 GPU (4 GB VRAM, Driver 582.53, CUDA 13.0 capability).
- [x] Created local virtual environment `.venv` using Python 3.11.
- [x] Cloned `https://github.com/Oldcircle/geo-sleuth` into `vendor/geo-sleuth/`.
- [x] Audited all 23 scripts, `SKILL.md`, references, and data tables in `vendor/geo-sleuth/`.
- [x] Probed and tested external candidate data sources without credentials (Overpass, Nominatim, AWS Terrarium DEM, Google Satellite tiles, EOX Sentinel-2, NASA GIBS, Wikimedia, KartaView).
- [x] Documented findings in `docs/REPO_AUDIT.md`, `docs/DATA_SOURCES.md`, and `docs/DECISIONS.md`.
- [x] Froze script keep/replace/disable decisions table.
- [x] Git commit: `a250c83`.

### Milestone 1: Project Skeleton & ModelManager (Completed)
- [x] Created repository layout: `src/geolocator/` (`app/`, `pipeline/`, `adapters/`, `providers/`, `models/`, `report/`, `web/`).
- [x] Implemented Pydantic-validated `config.yaml`, `src/geolocator/config.py`, and `.env.example`.
- [x] Implemented rotating file and console logging in `src/geolocator/logging.py` with privacy compliance (no raw photos in logs).
- [x] Implemented single-resident `ModelManager` with sequential GPU loading, thread/async locks, memory monitoring, and automatic VRAM clearing.
- [x] Implemented `scripts/check_gpu.py` and validated on host hardware:
  - GPU: NVIDIA Quadro M1200 (4.0 GB VRAM)
  - CUDA execution verified (latency: 11.00 ms, peak VRAM: 20.42 MB)
  - Memory unload verified (clean cache reclaim)
- [x] Added unit tests `tests/test_config.py` and `tests/test_model_manager.py`.
- [x] Git commit: `dfe48fc`.

### Milestone 2: Keyless Data Providers & Caching (Completed)
- [x] Implemented `BaseProvider` with deterministic SHA-256 caching, offline mode enforcement, and polite exponential backoff retry.
- [x] Implemented `OSMProvider` with Overpass QL execution and multi-mirror failover (`overpass-api.de`, `overpass.private.coffee`, `maps.mail.ru`).
- [x] Implemented `NominatimProvider` with strict 1.1s rate limiting and address/reverse geocoding.
- [x] Implemented `DEMProvider` with AWS Terrarium elevation tile decoding (~30m), spot elevations, and radial skyline elevation profile modeling (with Earth curvature and atmospheric refraction).
- [x] Implemented `SatelliteProvider` supporting Google, Esri, and Sentinel-2 tiles, resolution math, and grid mosaic stitching.
- [x] Implemented `StreetImageProvider` using keyless Wikipedia and Wikimedia Commons geosearch and thumbnail delivery.
- [x] Implemented `ClimateProvider` for Köppen-Geiger classifications (A, B, C, D, E) and visual compatibility scoring (aridity, vegetation, snow).
- [x] Implemented `LandCoverProvider` supporting ESA WorldCover taxonomy and scene filtering.
- [x] Added unit & integration tests `tests/test_providers.py` with recorded fixtures (all 12 tests passing).
- [x] Git commit: `1786615`.

### Milestone 3: Stage 0 (Intake) & Stage 1 (Clues/VLM) (Completed)
- [x] Implemented Candidate Board (`src/geolocator/pipeline/board.py`) with hierarchical candidates (country, region, cell, point), log-likelihood scoring, hard negative exclusions, and audit rationale tracking.
- [x] Implemented adapters wrapping vendored geo-sleuth modules (`src/geolocator/adapters/`):
  - `exif_adapter.py`: EXIF extraction, sanitization, GPS parsing, camera info.
  - `imgprep_adapter.py`: standard working copies (1024px long edge, 512px) and 8 edge/corner crops.
  - `clues_adapter.py`: tabular lookups for Chinese plates (`cn_plates.json`), driving side (`driving_side.json`), dial codes (`calling_codes.json`), and sovereign territories (`territories.json`).
  - `ocr_adapter.py`: RapidOCR ONNX integration with crop deduplication and quality filtering.
- [x] Implemented Stage 0 Intake (`src/geolocator/pipeline/stage0_intake.py`):
  - EXIF extraction, SHA-256 job ID, privacy-safe working copies.
  - Fast-path GPS exit (reports calibrated radius ~15m, confidence T1).
- [x] Implemented Stage 1 Clues (`src/geolocator/pipeline/stage1_clues.py`):
  - User hint parser (`hint_parser.py`) for countries, continents, seasons, landmarks.
  - Text & script OCR on base image and 8 edge crops.
  - Tabular lookups matching observed scripts and country hints.
  - Colorimetry & visual perception heuristics (sky, vegetation, ground ratios).
  - Pydantic schema validation (`schema.py` - `ClueExtractionResult`).
  - Candidate board initialized with country priors, clues, and log-likelihood ratios.
- [x] Added unit and integration tests (`tests/test_stage0_stage1.py`, 4/4 passing).
- [x] Git commit: `c4b9278`.

### Milestone 4: Stage 2 (Global Prior & Biomes) (Completed)
- [x] Resolved PyTorch 2.5 `torch.accelerator` compatibility shim across transformers packages.
- [x] Implemented geographic utility library (`src/geolocator/pipeline/geo_utils.py`) with Haversine distance calculations, offline country bounding boxes, regional spatial zones (Scandinavia, Sahara, Middle East, Europe), and greedy nearest-neighbor coordinate clustering into candidate cells.
- [x] Upgraded `ModelManager` lock to `threading.RLock` to eliminate re-entrant deadlocks across model swaps.
- [x] Implemented Stage 2 Prior (`src/geolocator/pipeline/stage2_prior.py`):
  - GeoCLIP global visual prior integration via `ModelManager` with automatic GPU execution and memory release.
  - Multi-source evidence fusion integrating visual embeddings, Köppen-Geiger climate classifications, ESA WorldCover, user hints, and observed driving side.
  - Strict biome and climate filtering with calibrated log-likelihood penalties (e.g. continental/polar group exclusions for arid scenes).
  - Spatial clustering producing ranked search bounding boxes (`search_bboxes`) for Stage 3 refinement.
  - Updates candidate board with cell candidates, clues, evidence weights, and rationale logs.
  - Emits `prior_results.json` artifact for inspectable decision tracing.
- [x] Added unit and synthetic integration tests (`tests/test_stage2_prior.py`, 5/5 passing):
  - Validated Haversine distance and spatial region checks.
  - Validated spatial clustering into candidate bounding boxes.
  - **Synthetic test passed**: verified a photo of the Sahara places zero candidate mass in Scandinavia (probability mass < 0.0001).
  - Validated user hint conditioning boosting target country candidates over raw prior leaders.
  - Validated end-to-end GeoCLIP inference on GPU with clean VRAM deallocation.
- [x] Full regression test suite passing (21/21 tests passing).
- [x] Git commit: `3863b20`.

### Milestone 5: Stage 3a (Natural Terrain Branch & DEM Skylines) (Completed)
- [x] Implemented `SkylineExtractor` (`src/geolocator/pipeline/skyline_extractor.py`):
  - 1D mountain/ridge boundary extraction using vertical luminance and contrast gradients.
  - Multi-stage median and moving average noise smoothing.
  - Generates debug visual overlay (`skyline_overlay.png`) drawing the extracted horizon line directly over the photo.
- [x] Implemented Stage 3a Natural Terrain Branch (`src/geolocator/pipeline/stage3_terrain.py`):
  - Fetches and decodes worldwide elevation from AWS Terrarium DEM tiles (~30m keyless).
  - Horizon profile renderer accounting for Earth curvature ($R=6371\text{ km}$) and atmospheric refraction ($k=0.13$).
  - Two-tier coarse-to-fine spatial grid search (coarse step 2-3 km, fine step 400-500m) with 360° heading sweep.
  - Normalized Cross-Correlation (NCC) scoring against photographic skyline profiles.
  - Calibrated error radius and confidence tier assignment (T2: $\le 1.5-4.5\text{ km}$, T3: $\le 15\text{ km}$, T4: $\le 45\text{ km}$).
  - Updates CandidateBoard with point candidate, computed likelihood ratio, and full rationale trail.
  - Emits `skyline_extracted.json`, `skyline_overlay.png`, and `terrain_results.json` artifacts.
- [x] Added unit and synthetic integration tests (`tests/test_stage3_terrain.py`, 3/3 passing):
  - Validated `SkylineExtractor` on synthetic mountain silhouette.
  - **Synthetic terrain test passed**: successfully recovered camera viewpoint to $\le 5\text{ km}$ ($2.1\text{ km}$ error) and heading within $\pm 15^\circ$ from DEM skyline.
  - Validated full pipeline execution and CandidateBoard updates.
- [x] Full test suite passing across all milestones (24/24 tests passing).
