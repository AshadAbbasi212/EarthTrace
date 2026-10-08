# Project Progress Log

## Milestone Status Overview

| Milestone | Title | Status | Completion Date | Git Commit |
|-----------|-------|--------|-----------------|------------|
| **M0** | Environment and Audit | **Completed** | 2026-10-08 | `a250c83` |
| **M1** | Project Skeleton & ModelManager | **Completed** | 2026-10-08 | `dfe48fc` |
| **M2** | Keyless Data Providers & Caching | **Completed** | 2026-10-08 | Pending |
| **M3** | Stage 0 (Intake) & Stage 1 (Clues/VLM) | In Progress | 2026-10-08 | - |
| **M4** | Stage 2 (Global Prior & Biomes) | Planned | - | - |
| **M5** | Stage 3a (Natural Terrain Branch & DEM Skylines) | Planned | - | - |
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
