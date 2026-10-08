# Repository Audit: geo-sleuth (`docs/REPO_AUDIT.md`)

This document is the Milestone 0 deliverable analyzing `vendor/geo-sleuth/` (`https://github.com/Oldcircle/geo-sleuth`). Every script has been audited for purpose, arguments, network calls, credentials, dependencies, and integration strategy.

---

## Script-by-Script Audit

### 1. `_net.py`
- **Purpose:** Centralized HTTP helper and curl wrapper with proxy resolution (`resolve_proxy`, `fetch_bytes`, `curl_args`, `model_proxy_env`).
- **CLI Arguments:** None (imported helper module).
- **Inputs / Outputs:** Takes URL, headers, proxy configuration. Returns raw response bytes.
- **Network Calls:** Invokes system `curl` to fetch arbitrary URLs.
- **Credentials Required:** None.
- **Dependencies & GPU:** Python standard library (`subprocess`, `os`). 0 MB VRAM.
- **Status:** **KEEP AS-IS / ADAPT** (wrapped or reused in adapters).
- **LLM Expectation:** None.

### 2. `_browser.py`
- **Purpose:** Launches headless Google Chrome or Playwright Chromium for web-based reverse image search.
- **CLI Arguments:** None (imported helper module).
- **Inputs / Outputs:** Takes proxy configuration, returns browser instance.
- **Network Calls:** None directly (controls browser).
- **Credentials Required:** None.
- **Dependencies & GPU:** `playwright`. 0 MB VRAM.
- **Status:** **DISABLE** (associated with web reverse image search which sends user photos to third parties).
- **LLM Expectation:** None.

### 3. `doctor.py`
- **Purpose:** Environment diagnostic tool checking local Python version, `uv`, `curl`, directory permissions, local lookup tables, and remote service endpoints.
- **CLI Arguments:** `--network` (probe endpoints), `--proxy` (proxy URL), `--json` (machine-readable output).
- **Inputs / Outputs:** JSON or stdout status lines `[PASS|WARN|FAIL]`.
- **Network Calls:** Probes Baidu, Yandex, Google Satellite, Google Street View, Overpass, Terrarium, Hugging Face.
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library + optional Playwright. 0 MB VRAM.
- **Status:** **KEEP** (adapted into `/healthz` endpoint and `check_gpu.py`).
- **LLM Expectation:** None (informational for diagnostics).

### 4. `exif.py`
- **Purpose:** Reads EXIF metadata from photo: GPS coordinates, timestamp, camera make/model, focal length, FOV, altitude, heading.
- **CLI Arguments:** `<photo> [<photo> ...]`
- **Inputs / Outputs:** Input: JPEG/PNG/HEIC image file. Output: JSON on stdout with `gps_wgs84`, `gps_gcj02`, `DateTimeOriginal`, `focal_35mm`, `fov_4x3_long_short`, `altitude_m`, `image_direction_deg`.
- **Network Calls:** None.
- **Credentials Required:** None.
- **Dependencies & GPU:** `pillow`, optional `pillow-heif`. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (wrapped in `src/geolocator/adapters/exif.py`).
- **LLM Expectation:** Output is parsed directly into Stage 0 candidate board metadata.

### 5. `imgprep.py`
- **Purpose:** Image preprocessing: zoom/upscale crops, 4-edge and 4-corner crops (`edges`), search variants (flip, grayscale, gray-world balance, perspective rectification), N×M grid tiling, and bridge pier brightness profile extraction (`piers`).
- **CLI Arguments:** `zoom`, `edges`, `variants`, `grid`, `piers` with associated flags (`--box`, `--scale`, `--rows`, `--cols`, `--persp`, etc.).
- **Inputs / Outputs:** Input image file -> output cropped/transformed images and `cols.json` for pier analysis.
- **Network Calls:** None.
- **Credentials Required:** None.
- **Dependencies & GPU:** `numpy`, `pillow`. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (wrapped in pipeline adapters).
- **LLM Expectation:** Edge crops and zoomed crops provide visual inputs for Stage 1 clue extraction.

### 6. `clues.py`
- **Purpose:** Local lookup tables for license plate prefixes (China), landline area codes, international calling codes, driving side (left vs right), overseas territories/dependencies, and administrative hierarchies.
- **CLI Arguments:** `lookup <kind> <value>`, `list`, `update`.
- **Inputs / Outputs:** Local JSON datasets in `data/`. Outputs matched admin entities and regions.
- **Network Calls:** Offline lookups. Update subcommand queries Wikipedia (not used at runtime).
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (fully offline, reliable tabular knowledge).
- **LLM Expectation:** Stage 1 extracted text/symbols are passed to `clues.py` to produce candidate regions.

### 7. `geo.py`
- **Purpose:** Comprehensive geospatial coordinate conversion (WGS84, GCJ-02, BD-09, BDMC), bearing/distance calculations, distance estimation from angular width (`range`), line alignment (`line`), sight-line intersection (`intersect`), camera visibility test (`frame`), and bridge pier spacing solver (`spacing`).
- **CLI Arguments:** `convert`, `bearing`, `dest`, `range`, `line`, `intersect`, `bearings`, `frame`, `spacing`.
- **Inputs / Outputs:** Inputs coordinates, angles, GeoJSON files. Outputs calculated distances, coordinates, candidate positions.
- **Network Calls:** None.
- **Credentials Required:** None.
- **Dependencies & GPU:** `numpy`, `pillow`. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (foundational geospatial library for all pipeline geometry).
- **LLM Expectation:** Pure algorithmic computation; output fed into candidate board.

### 8. `sun.py`
- **Purpose:** Astronomical solar calculations (NOAA Meeus algorithm): solar azimuth and elevation, shadow length ratios, latitude/longitude band derivation from solar elevation (`locate`), time of capture estimation (`when`), satellite dish azimuths, camera heading from lit/shaded facades (`facing`), and true bearing from visible sun (`compass`).
- **CLI Arguments:** `pos`, `ratio`, `locate`, `when`, `dish`, `street`, `facing`, `compass`.
- **Inputs / Outputs:** Inputs date/time, coordinates, shadow angles. Outputs solar geometry parameters and geographic constraints.
- **Network Calls:** None.
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library, `pillow` (for optional diagram generation). 0 MB VRAM.
- **Status:** **KEEP AS-IS** (used across natural terrain and built branches).
- **LLM Expectation:** Solar cues observed by VLM (shadow directions, time of day) are resolved into mathematical bands.

### 9. `terrain.py`
- **Purpose:** DEM elevation modeling using global AWS Terrarium tiles (~30m): synthesized 3D horizon rendering (`view`), numerical skyline elevation profile (`profile`), spot elevation lookup (`elev`), linear infrastructure horizon scanning (`scan`), photo ridgeline extraction (`ridge`), and candidate camera position skyline fitting (`fit`).
- **CLI Arguments:** `view`, `profile`, `elev`, `scan`, `ridge`, `fit` with various bounding box, heading, and FOV parameters.
- **Inputs / Outputs:** Inputs coordinates, DEM tiles, photo ridgelines. Outputs rendered terrain PNGs, skyline JSON profiles, RMS fit scores, and overlay comparison images.
- **Network Calls:** Downloads Terrarium DEM tiles from `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`.
- **Credentials Required:** None (Anonymous AWS Open Data access).
- **Dependencies & GPU:** `numpy`, `pillow`. 0 MB VRAM (CPU rendering).
- **Status:** **KEEP AS-IS / PRIMARY ENGINE** (core of the Stage 3 natural terrain branch).
- **LLM Expectation:** Generates skyline overlays and fit metrics; VLM assists only in judging top 3 candidate overlays.

### 10. `tiles.py`
- **Purpose:** Satellite tile downloading (Google Satellite / Esri World Imagery), mosaic stitching, marking candidate points/corridors/wedges (`mark`), thumbnail contact sheets (`sheet`), and pixel/coordinate transforms.
- **CLI Arguments:** `fetch`, `mark`, `sheet`, `px2ll`.
- **Inputs / Outputs:** Coordinates, bounding boxes, GeoJSON files. Outputs stitched JPEG mosaics, metadata JSON, marked overlays.
- **Network Calls:** Downloads tiles from `mt1.google.com` or `server.arcgisonline.com`.
- **Credentials Required:** None.
- **Dependencies & GPU:** `pillow`. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (used for satellite verification and evidence image creation).
- **LLM Expectation:** None (produces imagery for visual verification).

### 11. `osm.py`
- **Purpose:** OpenStreetMap Overpass QL query engine: feature finding (`find`), co-occurrence matching (`near`), line crossings (`crossings`), route corridors (`route`), linear intersections (`intersect`), street orientation scan (`street-scan`), roadside sampling (`along`), building footprints (`buildings`), and GeoJSON export (`geom`).
- **CLI Arguments:** Subcommands listed above.
- **Inputs / Outputs:** Queries Overpass API, outputs JSON coordinate dictionaries or GeoJSON files.
- **Network Calls:** Overpass API endpoints (`overpass-api.de`, `overpass.private.coffee`, `maps.mail.ru`, `overpass.kumi.systems`).
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (core of built/rural infrastructure and coastal matching).
- **LLM Expectation:** None (pure vector spatial queries).

### 12. `poi.py`
- **Purpose:** Geocodes place names, compound names, and addresses into coordinates using 360 Maps REST API, OSM Nominatim, and Baidu suggestions.
- **CLI Arguments:** `"<query>" [--city <city>] [--sources osm|so] [--country <code>]`
- **Inputs / Outputs:** JSON list of matched POIs with coordinates and address details.
- **Network Calls:** `restapi.map.so.com`, `nominatim.openstreetmap.org`, `map.baidu.com`.
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library. 0 MB VRAM.
- **Status:** **KEEP (ADAPTED)** (prioritize Nominatim worldwide, 360 Maps where relevant).
- **LLM Expectation:** Translates text recognized by VLM/OCR into candidate coordinates.

### 13. `gazetteer.py`
- **Purpose:** Administrative division hierarchy and bounding box resolver using OSM Overpass relations and local `cn_admin.json`.
- **CLI Arguments:** `children`, `info`, `urban`, `cost`.
- **Inputs / Outputs:** Outputs admin division hierarchy, bounding boxes, and built-up urban extents.
- **Network Calls:** Overpass API.
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library. 0 MB VRAM.
- **Status:** **KEEP AS-IS**.
- **LLM Expectation:** None.

### 14. `ocr.py`
- **Purpose:** Local optical character recognition: detects and transcribes text in full image, edge crops, and tiles.
- **CLI Arguments:** `<photo> [--langs zh-Hans,en] [--upscale N] [--tiles NxN] [--out ocr.json] [--draw ocr.png]`
- **Inputs / Outputs:** Input image -> JSON list of detected text strings, confidence scores, bounding boxes.
- **Network Calls:** None.
- **Credentials Required:** None.
- **Dependencies & GPU:** `rapidocr-onnxruntime` on Windows/Linux (Apple Vision on macOS). 0 MB VRAM (ONNX Runtime CPU).
- **Status:** **KEEP AS-IS** (tested and verified offline local OCR).
- **LLM Expectation:** Output is merged with VLM text extraction in Stage 1.

### 15. `sat_scan.py`
- **Purpose:** Zero-shot satellite imagery scanning: divides an area into a grid, scores each cell with CLIP against preset prompts (tracks, stadiums, factories, silos, dams, bridges, solar, etc.) or custom queries, and ranks candidate cells.
- **CLI Arguments:** `grid`, `points`, `presets` with `--bbox`, `--zoom`, `--preset`, `--top`, `--out`.
- **Inputs / Outputs:** Generates ranked candidate cells JSON, top-N contact sheet, and heatmap image.
- **Network Calls:** Fetches satellite tiles via `tiles.py`. Downloads CLIP weights from Hugging Face on first use.
- **Credentials Required:** None (ungated `openai/clip-vit-base-patch32`).
- **Dependencies & GPU:** `torch`, `transformers`, `pillow`, `numpy`. ~400 MB VRAM.
- **Status:** **KEEP AS-IS** (managed via `ModelManager` to run sequentially).
- **LLM Expectation:** Script ranks cells; VLM inspects only the top candidates if needed.

### 16. `match.py`
- **Purpose:** Visual image matching between query photo and candidate scene images: global descriptor ranking via DINOv2 (`facebook/dinov2-small`) or CLIP, followed by SIFT feature extraction and RANSAC geometric verification.
- **CLI Arguments:** `rank`, `index` with `--query`, `--panos`, `--items`, `--method dino|clip`, `--refine sift`, `--top`.
- **Inputs / Outputs:** Ranked candidate images JSON and contact sheet image.
- **Network Calls:** Downloads DINOv2 weights on first use from Hugging Face.
- **Credentials Required:** None (ungated `facebook/dinov2-small`).
- **Dependencies & GPU:** `torch`, `transformers`, `opencv-python-headless`, `pillow`, `numpy`. ~500 MB VRAM.
- **Status:** **KEEP AS-IS** (managed via `ModelManager` during Stage 4 verification).
- **LLM Expectation:** Ranks candidates by geometric inliers and feature similarity.

### 17. `pose.py`
- **Purpose:** Camera pose resection (6-DoF): Levenberg-Marquardt optimizer solving camera latitude, longitude, altitude, heading, pitch, roll, and focal length from 2D pixel to 3D terrain/map correspondences (`solve`). Discrete candidate checking (`check`) and forward projection (`project`).
- **CLI Arguments:** `solve`, `check`, `project`.
- **Inputs / Outputs:** Input `spec.json` with point correspondences -> estimated 6-DoF camera state and error radius.
- **Network Calls:** None.
- **Credentials Required:** None.
- **Dependencies & GPU:** `numpy`, `pillow`. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (used for Stage 4/5 pose estimation and T1/T2 precision validation).
- **LLM Expectation:** Algorithmic verification; validates whether camera elevation and pitch match the terrain.

### 18. `evidence.py`
- **Purpose:** Compiles final visual evidence artifact: satellite basemap with camera location, heading wedge, labeled landmarks, and ground comparison panels.
- **CLI Arguments:** `spec.json --out evidence.jpg`
- **Inputs / Outputs:** Input specification JSON -> synthesized evidence JPEG.
- **Network Calls:** None (uses locally fetched/cached satellite mosaic).
- **Credentials Required:** None.
- **Dependencies & GPU:** `pillow`. 0 MB VRAM.
- **Status:** **KEEP AS-IS** (used in Stage 5 report generation).
- **LLM Expectation:** None.

### 19. `board.py`
- **Purpose:** Central candidate board state machine: manages candidates across hierarchical levels (`country` down to `point`), logs clues with provenance status, computes likelihood ratios, enforces strict exclusion rules (requiring computed artifact proofs), ranks candidates, and generates decision reports.
- **CLI Arguments:** `init`, `add`, `children`, `clue`, `evidence`, `exclude`, `scan-bbox`, `urban`, `falsify`, `rank`, `next`, `check`, `report`, `apply`.
- **Inputs / Outputs:** Read/write `board.json`. Generates structured result sections.
- **Network Calls:** None directly (calls child scripts when needed).
- **Credentials Required:** None.
- **Dependencies & GPU:** Standard library. 0 MB VRAM.
- **Status:** **KEEP AS-IS / ORCHESTRATOR CORE** (reused/wrapped in `src/geolocator/pipeline/board.py`).
- **LLM Expectation:** Guides step transitions and bounds LLM judgment to evidentiary facts.

### 20. `intake.py`
- **Purpose:** All-in-one initial processing script combining metadata (`exif.py`), edge crops (`imgprep.py`), OCR (`ocr.py`), and search variants.
- **CLI Arguments:** `photo.jpg --out-dir <dir> [--no-rev] [--no-ocr] ...`
- **Inputs / Outputs:** Generates `exif.json`, `edges/`, `variants/`, `ocr.json`, `intake.md`, `intake.json`.
- **Network Calls:** None when `--no-rev` is passed.
- **Credentials Required:** None.
- **Dependencies & GPU:** `pillow`. 0 MB VRAM.
- **Status:** **KEEP WITH `--no-rev`** (reverse image search disabled).
- **LLM Expectation:** Outputs fed into Stage 1 VLM clue extraction.

### 21. `revimg.py`
- **Purpose:** Scrapes Baidu and Yandex reverse image search using Playwright.
- **CLI Arguments:** `--photo`, `--query`, etc.
- **Network Calls:** Baidu and Yandex image search endpoints.
- **Credentials Required:** None (scraping), but uploads user images.
- **Dependencies & GPU:** `playwright`.
- **Status:** **DISABLE / FORBIDDEN** (violates privacy rule against sending photos to external services).
- **LLM Expectation:** N/A.

### 22. `baidu_pano.py`
- **Purpose:** Fetches Baidu panorama metadata and perspective renderings.
- **Status:** **UNUSED** (left vendored but not called; excluded per brief §2a).

### 23. `gsv.py`
- **Purpose:** Fetches Google Street View panorama metadata and thumbnails.
- **Status:** **UNUSED** (left vendored but not called; excluded per brief §2a).

---

## Frozen Script Disposition Table

| Script Name | Category | Disposition | Notes / Replacement |
|---|---|---|---|
| `_net.py` | Helper | **KEEP** | Wrapped/adapted for resilient HTTP requests. |
| `_browser.py` | Helper | **DISABLE** | Playwright browser automation not needed without revimg. |
| `doctor.py` | Diagnostic | **KEEP** | Adapted into healthz probes and GPU checking. |
| `exif.py` | Stage 0 | **KEEP** | Core EXIF extraction; handles GPS, focal length, FOV. |
| `imgprep.py` | Stage 0 | **KEEP** | Crop edges, generate variants, zoom patches, pier extraction. |
| `intake.py` | Stage 0 | **KEEP (Modified)** | Runs with `--no-rev` (strictly offline/local). |
| `ocr.py` | Stage 1 | **KEEP** | RapidOCR ONNX backend for local keyless text detection. |
| `clues.py` | Stage 1/2 | **KEEP** | Offline tabular lookups for plates, codes, driving sides. |
| `geo.py` | Core Math | **KEEP** | Foundational coordinate math and photogrammetry. |
| `sun.py` | Core Math | **KEEP** | NOAA Meeus solar position and shadow math. |
| `gazetteer.py` | Stage 2 | **KEEP** | Resolves administrative hierarchy via Overpass/local tables. |
| `osm.py` | Stage 3 | **KEEP** | Vector feature matching and corridor intersections via Overpass. |
| `poi.py` | Stage 3 | **KEEP** | Geocodes place names using Nominatim and 360 Maps. |
| `terrain.py` | Stage 3 | **KEEP** | Primary natural terrain skyline modeling with Terrarium DEM. |
| `tiles.py` | Stage 4 | **KEEP** | Satellite tile acquisition and mosaic stitching. |
| `sat_scan.py` | Stage 4 | **KEEP** | CLIP-based zero-shot satellite tile ranking. |
| `match.py` | Stage 4 | **KEEP** | DINOv2 + SIFT ground-level image matching. |
| `pose.py` | Stage 4 | **KEEP** | Levenberg-Marquardt camera resection solver. |
| `evidence.py` | Stage 5 | **KEEP** | Evidence composite image builder. |
| `board.py` | Pipeline | **KEEP** | Candidate board state machine and likelihood scoring. |
| `revimg.py` | Stage 0 | **DISABLE** | Violates privacy constraint (uploads photos to third parties). |
| `gsv.py` | Street View | **UNUSED** | Gated/proprietary; left vendored but unused per brief §2a. |
| `baidu_pano.py` | Street View | **UNUSED** | Gated/proprietary; left vendored but unused per brief §2a. |
