# PROJECT BRIEF: Self-hosted Global Photo Geolocator

> Read this whole file before writing any code. It is the single source of truth for what to build.
> Written without access to the geo-sleuth source code. **Every statement about that repo, and every
> "candidate" data source below, is unverified until you check it in Milestone 0.** Where reality
> differs from this brief, follow reality, and record the deviation in `docs/DECISIONS.md`.

---

## 1. Goal

Build a **self-hosted chat web app** where a user uploads **one photo** (plus optional text hints such as
country, season, "I think it's near a lake") and the system answers: **where on Earth was this photo taken?**

It must work **anywhere on the globe**, not only in cities: mountains, deserts, valleys, coasts, farmland,
forests, polar and island scenes. Urban scenes are the easy case; natural terrain is a first-class requirement.

The answer is a **full report**: coordinates, error radius, camera heading (when determinable), a confidence
tier, evidence images, ranked alternatives, and the step-by-step reasoning.

The reasoning engine is built **from the open-source `Oldcircle/geo-sleuth` repo**
(https://github.com/Oldcircle/geo-sleuth, an agent skill: `SKILL.md` + ~20 single-purpose Python scripts +
`references/` + `data/`). We reuse its scripts and methodology, but we replace the "coding agent that drives the
skill" with **our own Python orchestrator and a local vision-language model**.

## 2. Non-negotiable constraints

1. **No API keys, no paid services, no tokens, no accounts** for any external service. This includes AI
   providers (no Claude/OpenAI/Gemini APIs), map/street-view providers, and Hugging Face tokens (use only
   **ungated** model repos; download weights once, then run offline).
2. **Local AI only.** All inference runs on the host GPU via **Hugging Face `transformers` in Python**.
3. **Hardware target:** Windows 10/11, one NVIDIA GPU with **8 GB VRAM**. The design must fit 8 GB by
   loading models **one at a time** (see §7).
4. **Data sources must be keyless.** Open data only (OpenStreetMap, open DEMs, open satellite/land-cover
   products). Anything that needs a key (e.g. Google Street View, Baidu panoramas, Mapillary) is **not used**, and is never faked. The app must be fully functional without any of them.
5. **Worldwide scope** with no region restriction. The system queries open data online on demand and caches
   it on disk. Internet access is required for data lookups (model inference itself stays local).
6. **Deployment shape:** runs on the owner's Windows PC; a few friends open it in a browser.
7. **Honesty over bravado.** The system must say "region-level only" or "unknown" when evidence is weak.
   Never output false precision (see §3).
8. **No telemetry, no analytics, no external fonts/CDNs required at runtime** except what is needed for map
   tiles (document it). Bundle JS/CSS locally where practical.

## 2a. Zero-input rule and mandatory evidence methods

**The owner provides nothing.** The building agent fetches everything itself from the internet: the
geo-sleuth repo, Python packages, model weights (ungated), datasets (climate, ecoregions, land cover), map
data, imagery, and the **evaluation photos** (see section 12). No manual downloads and no files supplied by
the owner. If a step truly cannot be automated, state exactly why in `docs/DECISIONS.md` and continue with
everything else.

**The pipeline must actually use all four evidence types, and the report must show each one:**
1. **OpenStreetMap geometry:** roads, railways, bridges, waterways, coastlines, power lines, buildings,
   used for corridor and geometry matching.
2. **Elevation skylines:** ridge/horizon profiles extracted from the photo and matched against profiles
   computed from a DEM.
3. **Satellite imagery:** tile ranking and visual verification around candidate locations.
4. **Street-level imagery:** candidate locations are compared with street-level photos wherever a keyless
   source has coverage (see section 8).

For every photo, the reasoning timeline lists each of the four as **used**, **not applicable** or **not
available** (with the reason), what it found, and the artifact file that proves it.

**Street-level honesty:** Google Street View, Mapillary and Baidu need keys or tokens, so they are **not
used** (leave the vendored `gsv.py` and `baidu_pano.py` untouched and unused; do not add key slots for them).
Keyless street-level coverage (e.g. KartaView, Wikimedia Commons geotagged photos; verify) is sparse,
especially away from roads. In mountains and deserts this evidence will often be "not available". That is
expected and must be reported as such, not hidden.

## 3. Honest accuracy expectations (design to these)

Precision depends on how much locatable signal a photo contains. Build the output around **tiers**:

| Tier | Meaning | Typical radius |
|------|---------|----------------|
| T1 | Verified position (overlay/feature match confirmed) | <= 100 m |
| T2 | Local | <= 5 km |
| T3 | Area | <= 50 km |
| T4 | Region | <= 500 km |
| T5 | Country / continent | > 500 km |
| T6 | Unknown, insufficient evidence | n/a |

- A photo with visible ridgelines, bridges, coastlines, roads or distinctive landforms can reach T1-T2.
- Featureless desert, open ocean, uniform forest or cropland may only reach T4-T5. That is correct behavior.
- The report must state the tier, the radius, **what evidence supports it**, and what would improve it
  (e.g. "if you know the month or country, say so").
- Error radii must be **calibrated** on the evaluation set (§12), not guessed.

## 4. Handling the source repo (`geo-sleuth`)

- Clone into `vendor/geo-sleuth/` (git submodule or pinned commit). **Keep its LICENSE and attribution**
  (reported as MIT, verify). Do **not** edit vendored files in place; wrap them with adapters in
  `src/geolocator/adapters/`. If a patch is unavoidable, store it as a patch file in `patches/` and apply it
  in the setup script.
- **Milestone 0 audit (mandatory, before design freezes):** read `SKILL.md`, every file in `scripts/`,
  `references/`, `data/`, and the dependency list. Produce `docs/REPO_AUDIT.md` with, for **each script**:
  - purpose, CLI arguments, input files, output files/JSON shape;
  - network calls it makes (hosts/URLs) and whether each needs a key/login;
  - Python and GPU dependencies and rough VRAM use;
  - whether it can run keyless as-is, needs a replacement data provider, or must be disabled;
  - whether it expects an LLM to interpret its output (and what that interpretation is).
- Scripts named in the repo's own flow diagram (verify names): `intake.py` (EXIF, OCR, reverse image search),
  `board.py` (candidate board: clues, likelihood ratios, ranking, suggested next step), `sun.py`, `terrain.py`,
  `osm.py`, `pose.py`, `sat_scan.py` (CLIP-ranked satellite tiles), `match.py` (DINOv2+SIFT matching),
  `gsv.py`, `baidu_pano.py` (street view; expected to need keys -> leave unused, and replace with the keyless providers in section 8), `evidence.py`
  (coordinates +/- radius, evidence image, graded confidence).
- Reverse image search in `intake.py` probably depends on an external service. If it needs a key or scraping,
  disable it and document that.
- The repo's own rule applies to our pipeline: **every claim in the final report must cite the step that
  produced it and the artifact file it created.** Population or fame is not evidence.

## 5. Architecture

**Principle (from the repo): scripts search, score and rank; the model only perceives and judges among the
top few.** A small local model is unreliable at long open-ended tool loops, so **code drives the workflow**
and the model is called at fixed, narrow points with strict output schemas.

```
Photo (+ optional user hints)
  |
  v
[Stage 0] Intake ........ validate, EXIF (GPS fast path, time, orientation), resized copies, hash
  |
  v
[Stage 1] Clue extraction  (VLM -> strict JSON)
  |
  v
[Stage 2] Global prior ..... region probabilities from: image-geolocation model + biome/climate rasters
  |                          + VLM region guess + user hints  -> ranked search regions
  v
[Stage 3] Candidate generation, routed by scene type
  |   - natural terrain  : DEM horizon/skyline matching, landform + water + land cover, sun/shadow
  |   - built / rural infra: OSM corridor and geometry matching, text/OCR, driving side, utilities
  |   - coastal / water  : OSM coastline & island geometry + DEM
  |   - always           : sun/shadow constraints when time/season known
  v
[Stage 4] Verification ..... satellite tile ranking (CLIP), feature matching (DINOv2+SIFT), overlays, pose
  |
  v
[Stage 5] Decision & report  tier + radius + heading + alternatives + evidence + reasoning log
```

State lives in a per-job **candidate board** (JSON, persisted to disk after every step). It records clues,
candidate regions/points with scores, which steps ran, and artifact paths. The repo's `board.py` should be
reused if it fits; otherwise implement an equivalent in `src/geolocator/board.py`.

### 5.1 Stage 0: Intake
- Accept JPEG/PNG/WebP/HEIC (convert HEIC if a keyless library is available). Max size configurable
  (default 25 MB). Verify it is a real image (decode it), not just by extension.
- Read EXIF: GPS (if present, **use as a fast path but still sanity-check**: EXIF can be wrong or edited),
  timestamp, timezone offset, camera orientation, focal length. Many photos have EXIF stripped; that is normal.
- Produce working copies (e.g. 1024 px and 512 px long edge) for models; keep the original untouched.

### 5.2 Stage 1: Clue extraction (VLM, strict JSON)
Prompt the VLM to return JSON validated by a schema (use `pydantic`; retry once, then fall back to a
degraded "unknown" value per field). Fields (extend as needed):

```json
{
  "scene_type": "urban|rural_road|farmland|forest|mountain|desert|valley|coast|lake_river|snow_ice|island|indoor|other",
  "terrain": {"relief": "flat|hilly|mountainous", "landforms": ["ridge","dune","canyon","..."],
              "rock_soil_color": "string", "horizon_visible": true},
  "vegetation": {"type": "string", "density": "none|sparse|moderate|dense", "notable_species": ["..."]},
  "climate_cues": {"season_guess": "string", "snow": false, "aridity": "arid|semi_arid|humid|unknown"},
  "built_environment": {"road_markings": "string", "driving_side": "left|right|unknown",
                        "utility_poles": "string", "architecture": "string", "vehicles": "string"},
  "text_and_signs": [{"text": "string", "script": "latin|cyrillic|arabic|hanzi|...", "language_guess": "string"}],
  "sun_shadow": {"shadows_visible": true, "time_of_day_guess": "string"},
  "water": {"type": "none|sea|lake|river|glacier", "notes": "string"},
  "region_guesses": [{"place": "string", "reason": "string", "confidence": 0.0}],
  "distinctive_features": ["string"],
  "overall_confidence": 0.0
}
```

- The VLM must only describe what is **visible**; it must not invent. Instruct it to use `"unknown"`.
- Optional: run OCR with a local, keyless library (e.g. EasyOCR/PaddleOCR/Tesseract; pick what installs
  cleanly on Windows) for text and signs, and merge with VLM output.
- Parse **user hints** from chat text (country, season, nearby landmark) into the same schema and treat
  them as **strong but fallible** priors (store provenance: `source: user_hint`).

### 5.3 Stage 2: Global prior
Goal: turn "a photo of a dry valley with sparse shrubs" into a ranked set of **search regions** worldwide.
- **Image geolocation prior:** use an open, locally runnable model that predicts GPS or a ranked list of
  places from an image (candidates to evaluate: **GeoCLIP**, others you find; verify license and that weights
  download **without a token**; note non-commercial licenses in `docs/DATA_SOURCES.md`). Use its top-k as a
  **soft prior only**.
- **Biome/climate prior:** download once and cache a global Koppen-Geiger climate raster and a terrestrial
  ecoregion/biome dataset (verify keyless download and licenses). Map VLM cues (aridity, vegetation, snow)
  to compatible zones and down-weight impossible ones.
- **Combine** the priors, VLM `region_guesses` and user hints into a probability map (simple log-linear
  combination with documented weights in `config.yaml`; calibrate on the eval set).
- Output: top N (default 5-10) **search regions** as polygons/bounding boxes with scores and reasons.
- A strong user hint (e.g. "Peru") can restrict regions but must not be treated as infallible. If evidence
  contradicts it, say so in the report.

### 5.4 Stage 3: Candidate generation (routed)

**Natural terrain branch (priority: this is what makes it "whole globe")**
- **DEM horizon/skyline matching** (reuse `terrain.py` ideas): extract the ridge/horizon profile from the
  photo (segmentation of sky vs ground, e.g. with a local keyless method), then compare against horizons
  computed from a DEM over a grid of candidate camera points in the search regions. Use coarse-to-fine:
  region grid (km) -> local grid (hundreds of metres) -> refined positions + heading. Account for camera
  FOV (from EXIF focal length if present, otherwise estimate/search over plausible FOVs).
- **Landform and hydrology cues:** rivers, lakes, glaciers, valley shape, dune fields, canyons, volcanic
  cones, matched against OSM water features, DEM derivatives (slope, curvature, drainage) and land-cover.
- **Land cover:** use a global open land-cover product (e.g. ESA WorldCover on open cloud storage; verify
  keyless access) to filter candidates (e.g. "bare/sparse vegetation" vs "tree cover").
- **Sun/shadow (`sun.py`):** if time is known (EXIF) or guessed, use shadow direction and solar geometry to
  constrain latitude/longitude bands and camera heading.
- **Deserts / featureless terrain:** combine rock/soil colour, dune morphology, climate prior, sun geometry
  and any visible horizon. Expect T4-T5 outcomes unless a horizon or landmark exists. Say so.

**Built / rural infrastructure branch**
- OSM corridor and geometry matching (`osm.py`): roads, railways, bridges, power lines, field patterns,
  with spacing/ruler tricks as in the repo's showcase (pier spacing, pole spacing, lane widths).
- Language/script, driving side, road markings and utility styles narrow the country quickly.
- Landmark/near-duplicate check via a keyless geotagged-photo source (e.g. Wikimedia Commons geosearch;
  verify) as an optional signal.

**Coastal / water branch**
- Coastline and island geometry from OSM + DEM bathymetry-free horizon checks; lake shape matching.

Every branch ends by writing candidates (point/area, score, reasons, artifact paths) to the board.
Scores must be **comparable across branches** (normalize to a log-likelihood-style score).

### 5.5 Stage 4: Verification
- **Satellite tile ranking** (`sat_scan.py` idea, CLIP): fetch keyless imagery tiles around top candidates
  and rank similarity to the photo's scene. Treat as weak evidence; it cannot confirm alone.
- **Street-level matching** (`match.py` idea, DINOv2 + SIFT): for the top candidates, query the keyless
  street-level providers (section 8) for images near each candidate and match them against the photo
  (global descriptors first, then local features and geometric verification). Log how many images were found,
  which provider, and the match scores. When no coverage exists, record "not available" and fall back to
  satellite/orthophoto crops and rendered DEM views where meaningful.
- **Overlay checks:** draw the predicted ridge line / geometry back onto the photo and score alignment;
  save as evidence images. A candidate reaches T1 only with a passing overlay or geometric verification.
- **Pose (`pose.py`):** estimate camera heading (and position refinement) from verified geometry.

### 5.6 Stage 5: Decision and report
- Choose the final answer with a **fixed rule set** in code (top score, margin over runner-up, verification
  status), not by asking the model to pick freely. The VLM may be asked to **judge among the top 3** using
  the evidence images, and to **write the narrative**, but its choice is advisory and must agree with the
  evidence trail or be flagged.
- Output `report.json` (machine-readable) and `report.html`/`report.md` (human-readable):
  coordinates, radius, tier, heading, confidence, top alternatives with reasons, evidence images, a
  timeline of steps (what ran, what it found, artifact paths), and limitations/what would help.
- Include a **map-ready GeoJSON** (point, error circle, heading ray).
- If evidence is insufficient: return T6/T5 with candidate regions and suggestions, never a fabricated point.

## 6. Application design

**Backend:** Python 3.11 or 3.12, **FastAPI**, `uvicorn`. One **GPU worker** processes jobs sequentially
(an asyncio queue + a GPU lock); users see their queue position. SQLite for persistence.

```
POST /api/sessions                    -> create chat session
POST /api/sessions/{id}/messages      -> multipart: text and/or image; starts a job when an image is present
GET  /api/sessions/{id}               -> messages + job summaries
GET  /api/jobs/{id}                   -> status + board summary
GET  /api/jobs/{id}/report.json|html  -> final report
WS   /ws/jobs/{id}                    -> progress event stream (or SSE)
GET  /artifacts/{job_id}/{file}       -> evidence images, overlays, geojson (static, safe paths only)
GET  /healthz                         -> GPU, models, data-provider status
```

Progress events: `job_queued`, `step_started`, `step_progress`, `step_finished`, `candidate_update`,
`evidence_ready`, `final_report`, `error`. The UI renders these live.

**Chat behavior**
- Photo upload -> run the pipeline -> stream steps -> final report card.
- **Follow-up questions** ("why not Chile?", "what if it's winter?") are answered by the VLM using the saved
  board and report as context, without re-running the pipeline.
- **Refinement** ("it's in Kyrgyzstan") adds a hint and re-runs from Stage 2, reusing cached data.
- The model must answer follow-ups only from the board/report and say when something was not checked.

**Frontend:** simple, fast, mobile-friendly, **no heavy framework required** (vanilla JS/HTMX or a small
Vite build; choose the simplest that works and keep it reproducible). Features: chat thread, image upload with
preview, live step timeline, Leaflet map (error circle, heading arrow, alternative markers), evidence image
gallery, expandable reasoning, copy/download report. Serve all JS/CSS locally.

**Safety and access (small private group)**
- Optional **shared passphrase** (local app setting, not an external API key) enforced on all routes; per-IP
  rate limit; upload size/type validation; sanitize file names; serve artifacts only from the job folder.
- Config option to **auto-delete photos and artifacts after N hours** (default on, e.g. 24 h) and to strip
  EXIF from stored copies.
- Show a clear **responsible-use notice** in the UI and README: do not use this to locate private
  individuals who have not consented. Do not remove this notice.

## 7. Local model plan (8 GB VRAM)

- **VLM:** default candidate **Qwen2.5-VL-7B-Instruct in 4-bit** (bitsandbytes NF4) or a newer, ungated
  open ~4-8B vision-language model that benchmarks better on your quick test. Avoid gated repos
  (they require a token). Make the model name a setting in `config.yaml`.
- **Other models:** CLIP (satellite ranking), DINOv2 (matching), image-geolocation prior (e.g. GeoCLIP), a
  segmentation model for sky/ground if needed. Each is small but they **must not all be resident at once**.
- **Memory strategy:** a `ModelManager` that loads a model on demand, runs it, then unloads and clears the
  CUDA cache, with a GPU lock. Order stages to minimize swapping (run all VLM work in a batch where
  possible). Log VRAM before/after.
- **Windows specifics:** verify the `bitsandbytes` version that supports Windows + your CUDA. If 4-bit via
  bitsandbytes is unreliable, fall back to another quantization route (e.g. AWQ/GPTQ via `transformers`) or a
  smaller model. Document what worked in `docs/DECISIONS.md`.
- **`scripts/check_gpu.py`:** prints GPU name, VRAM, CUDA/PyTorch versions, loads the chosen VLM, runs a test
  image, and reports peak VRAM and latency.
- Download all weights once into `models/` with pinned revisions; afterwards the app must run with
  `HF_HUB_OFFLINE=1`.
- If a model OOMs: automatically retry with a smaller image size, then a smaller model, and surface a clear
  error. Never crash the worker.

## 8. Keyless data sources (candidates; VERIFY each in Milestone 0/2)

Implement every source behind a **provider interface** with caching, timeouts, retries and fallbacks. At
build time, test each endpoint **without any credentials**. If it needs one, replace it or disable it.
Record the result, licence and usage policy in `docs/DATA_SOURCES.md`.

| Purpose | Candidate sources (verify) | Notes |
|---|---|---|
| Vector map data | OSM via public Overpass instances; or Geofabrik regional extracts downloaded on demand | Public Overpass is rate-limited: small bboxes, caching, polite retries, multiple mirrors |
| Reverse geocoding (names only) | Nominatim public instance | No key, but strict usage policy: <= 1 req/s, custom User-Agent, cache everything |
| Elevation | Open Terrain/DEM tiles on open cloud storage (e.g. Terrarium-format terrain tiles; Copernicus GLO-30 COGs) | Anonymous access; cache tiles; choose resolution by stage (coarse first) |
| Satellite imagery | Keyless Sentinel-2 mosaics / WMTS (e.g. EOX Sentinel-2 cloudless), NASA GIBS (coarse), open Sentinel-2 COGs via STAC | Check licence (some are non-commercial); some "free" tile services forbid bulk/automated use. Respect terms; low volume; cache |
| Land cover | ESA WorldCover on open storage | Use as a filter, not proof |
| Climate / biomes | Koppen-Geiger raster; terrestrial ecoregions dataset | Download once, ship checksums |
| Geotagged photos | Wikimedia Commons geosearch | Optional landmark signal |
| Street-level imagery | KartaView (open street-level imagery API), Wikimedia Commons geotagged photos (geosearch) | Implement a `StreetImageProvider` interface with these keyless providers; verify each works with no credentials and note licences. Google, Mapillary and Baidu are excluded (keys/tokens). Coverage is sparse off-road, so expect "not available" in wild terrain. If you find another genuinely keyless, licence-compatible source, add it |

General rules: identify the client with a descriptive `User-Agent`; cap concurrency; exponential backoff;
disk cache keyed by (provider, tile/query, version); a `--offline` mode that uses only cached data.

## 9. Repository layout (target)

```
geo-locator/
  PROJECT_BRIEF.md            (this file, keep it)
  README.md                   (user-facing quick start)
  AGENTS.md                   (short rules for coding agents; points to the brief)
  config.yaml                 (models, weights, thresholds, providers, retention)
  .env.example                (local settings only; NO external keys)
  pyproject.toml / requirements*.txt
  vendor/geo-sleuth/          (pinned upstream; LICENSE kept)
  patches/                    (only if unavoidable)
  models/                     (downloaded weights, gitignored)
  data/                       (cached datasets/tiles, gitignored)
  jobs/                       (per-job folders: input, board.json, artifacts, report; gitignored)
  src/geolocator/
    app/                      (FastAPI app, routes, websocket, auth, rate limit)
    pipeline/                 (stages 0-5, orchestrator, board)
    adapters/                 (wrappers around vendored geo-sleuth scripts)
    providers/                (osm, dem, imagery, landcover, climate, geophoto; cache layer)
    models/                   (ModelManager, VLM client, CLIP, DINOv2, geo prior)
    report/                   (json/html/md/geojson builders)
    web/                      (static frontend)
  scripts/                    (check_gpu.py, download_models.py, download_data.py, setup_windows.ps1, run.ps1)
  tests/                      (unit, integration with recorded fixtures, e2e smoke)
  eval/                       (manifest.csv, photos/, run_eval.py, results/)
  docs/                       (REPO_AUDIT.md, DATA_SOURCES.md, DECISIONS.md, ARCHITECTURE.md, PROGRESS.md)
```

## 10. Configuration

`config.yaml` holds: model names/revisions, quantization mode, image sizes, stage weights and thresholds,
provider priority lists, cache paths/limits, queue and timeout limits, retention hours, upload limits,
passphrase on/off. `.env.example` may contain only local values (host, port, passphrase, paths). **It must not
contain, request or reference any external API key.**

## 11. Windows setup and deployment ("ready to deploy" means this)

- `scripts/setup_windows.ps1`: installs Python 3.12 and Git via `winget` if missing (it only checks the NVIDIA driver and explains what to do if absent), creates a venv, installs the correct **CUDA build of
  PyTorch** and pinned dependencies, applies patches, downloads models and base datasets, runs
  `check_gpu.py`, and prints next steps. Idempotent and re-runnable.
- `scripts/run.ps1`: starts the server (default `127.0.0.1:8000`; a flag/config to bind `0.0.0.0` for LAN use).
- **LAN sharing:** document opening the Windows firewall for the chosen port and finding the PC's LAN IP.
  Note that plain HTTP on a LAN sends photos unencrypted; offer an optional self-signed-HTTPS mode.
- **Internet sharing is optional and out of the default path.** Tunnels (Cloudflare Tunnel, Tailscale, etc.)
  generally need a free account; describe them as opt-in extras, not requirements.
- Optional `Dockerfile` + `compose.yaml` for Linux/WSL2 with the NVIDIA container toolkit. Mark as optional
  and untested on the owner's machine unless you actually tested it.
- Auto-start option (Task Scheduler or NSSM) documented, not forced.
- `/healthz` reports GPU, loaded models, data-provider reachability, cache size, queue length.
- Logs to `logs/` with rotation; no photo content in logs.

## 12. Testing and evaluation (required, not optional)

**Unit tests:** EXIF parsing, schema validation and fallback for VLM output, tile/coordinate math, DEM
horizon computation, scoring normalization, path-safety, auth and rate limiting.

**Integration tests:** providers against **recorded fixtures** (no live network in CI), orchestrator
state machine, job queue and cancellation, model manager load/unload (mocked and one real-GPU smoke test).

**Synthetic terrain test (keyless ground truth):** pick random points worldwide, **render a skyline/ridge
profile from the DEM** at a known position and heading, feed it through the terrain branch, and measure
recovery error. This validates the natural-terrain matcher without needing licensed photos.

**Evaluation set (built automatically, no owner input):** `scripts/build_eval_set.py` downloads roughly
60-100 openly licensed photos with known **camera** coordinates from Wikimedia Commons (use camera-location
data only; skip photos that give only the subject's location, and skip aerial, drone and satellite shots).
Record file, lat, lon, category, licence, author and source URL in `eval/manifest.csv`. Cover every continent
and these categories: urban, rural road, farmland, coast, lake/river, mountain, valley, desert, forest,
snow/ice, island. Balance by category and region. Make an EXIF-stripped copy of every photo for the main
test and keep a separate small set to test the EXIF-GPS fast path. Caveat to document: Commons photos may
appear in the training data of the image-geolocation prior, so results can be optimistic; the synthetic DEM
test above is the unbiased check for the terrain branch.

`run_eval.py` reports, per category and overall: median error, percent within **1 km, 25 km, 200 km,
750 km, 2500 km**, tier distribution, which of the four evidence types were used, runtime, peak VRAM, and
calibration of the reported radius (does the true location fall inside the stated radius at the claimed
rate?). Use this to tune weights and to calibrate radii.

**Acceptance criteria (initial; adjust only with justification in `docs/DECISIONS.md`):**
- End-to-end run succeeds on 8 GB VRAM with no OOM across the eval set.
- Never returns a point with T1/T2 claims that fail the verification rule.
- Reported radii are calibrated (stated coverage within a reasonable margin of actual coverage).
- Natural-terrain synthetic test: median recovery error well below the stated T2 radius where a horizon exists.
- A fresh clone plus `setup_windows.ps1` plus `run.ps1` gives a working app on a clean Windows machine.

## 13. Milestones (work autonomously, commit after each, log in `docs/PROGRESS.md`)

- **M0** Environment and audit: verify GPU/CUDA, clone repo, write `REPO_AUDIT.md`, test each candidate data
  source keyless, write `DATA_SOURCES.md`. Freeze the script keep/replace/disable table.
- **M1** Project skeleton, config, logging, ModelManager, `check_gpu.py`.
- **M2** Providers with caching (OSM, DEM, satellite imagery, street-level imagery, land cover, climate), offline mode, tests with fixtures.
- **M3** Stage 0 and Stage 1 (intake, EXIF, clue extraction with schema + OCR + hint parsing).
- **M4** Stage 2 global prior (geo model + biome/climate + hints) and search-region output.
- **M5** Natural-terrain branch (DEM skyline matching, hydrology, land cover, sun/shadow) + synthetic test.
- **M6** Built/rural and coastal branches via adapters around the vendored scripts.
- **M7** Verification, pose, evidence images, decision rules, report builders.
- **M8** Backend API, queue, DB, events, auth, retention.
- **M9** Frontend chat UI with map and live timeline.
- **M10** Auto-built evaluation set, evaluation harness, calibration, performance and VRAM tuning, hardening.
- **M11** Packaging, Windows scripts, docs (README with screenshots-free quick start), final end-to-end check.

## 14. Rules of engagement for the building agent

- **Autonomy:** proceed without asking unless blocked. Valid blockers: a required source turns out to need a
  key and no keyless alternative exists, or the GPU cannot run any acceptable model. The owner supplies
  nothing; fetch everything yourself. In those cases, finish everything else first, then report the blocker precisely.
- **Scope of changes:** create/modify files only inside the project folder. Install Python packages only into
  the project venv. Downloads allowed: open datasets and ungated model weights listed here. No global system
  changes except what `setup_windows.ps1` documents and the owner can read first.
- **No secrets:** never add API keys, tokens or credentials anywhere. If something asks for one, replace or
  disable that feature and record it.
- **No invention:** do not claim a source, library or model works until you tested it. Record real versions.
- **Respect terms:** follow each data source's usage policy and licence; keep request volume low; cache.
- **Keep it simple:** prefer boring, maintainable choices; no unnecessary frameworks.
- **Document deviations** from this brief in `docs/DECISIONS.md` with the reason.
- **Definition of done:** all milestones complete, tests passing, eval harness runs, `README.md` quick start
  verified from a clean checkout, `PROGRESS.md` final summary lists limitations honestly.

## 15. Known risks (plan for them)

- Small local VLMs hallucinate: strict schemas, "unknown" defaults, evidence-gated decisions.
- Keyless imagery may be old, cloudy or licence-limited: treat as weak evidence; show provenance.
- Public Overpass/Nominatim can throttle or go down: caching, mirrors, graceful degradation, clear status.
- DEM skyline matching is compute-heavy worldwide: always go coarse-to-fine, cap candidates, time-box.
- 8 GB VRAM is tight: sequential model loading, quantization, reduced image sizes.
- Misuse risk: keep the responsible-use notice, retention limits and access control.
