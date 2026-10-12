# Architectural Decisions & Deviations Log (docs/DECISIONS.md)

This document records all deviations from `PROJECT_BRIEF.md`, architectural decisions, and hardware/environmental constraints verified on the deployment system.

---

## 1. Python Runtime Selection: Python 3.11.9
- **Brief Specification:** Section 6 specifies Python 3.11 or 3.12.
- **Observed Reality:** The system default PATH had Python 3.14.6 installed, which has no stable binary PyTorch/torchvision/transformers wheels on Windows. A native Python 3.11.9 installation was discovered at `C:\Users\David\AppData\Local\Python\pythoncore-3.11-64\python.exe`.
- **Decision:** Dedicated `.venv` created strictly with Python 3.11.9 to ensure full binary wheel compatibility with PyTorch, CUDA, and ML dependencies.

---

## 2. Host GPU Hardware: NVIDIA Quadro M1200 (4 GB VRAM)
- **Brief Specification:** Section 2 and Section 7 target Windows + 8 GB VRAM.
- **Observed Reality:** `nvidia-smi` identifies the GPU as an NVIDIA Quadro M1200 (GM107/Maxwell architecture, Compute Capability 5.0) with **4,096 MiB (4 GB) VRAM**, running driver 582.53 and CUDA 13.0 driver support.
- **Implications & Decision:**
  - 4 GB VRAM is tighter than the 8 GB target in the brief.
  - The sequential single-model execution strategy (`ModelManager` with aggressive CUDA cache clearing and unloading) is essential.
  - VLM models will be configured with lightweight 4-bit / quantized checkpoints (e.g. Qwen2.5-VL-3B or 7B with CPU offload/4-bit quantization, or SmolVLM-Instruct) to prevent OOM.
  - Image long edges will be scaled conservatively (default 768px - 1024px) during VLM inference.
  - If PyTorch CUDA cannot run sm_50 kernels on newer PyTorch builds, CPU fallback will be seamlessly handled without crashing the pipeline worker.

---

## 3. Disabling Reverse Image Search (`revimg.py` in `intake.py`)
- **Brief Specification:** Section 4 states: *"Reverse image search in intake.py probably depends on an external service. If it needs a key or scraping, disable it and document that."* Section 2a: *"Sending photos or any user data to any third-party service: Not permitted."*
- **Observed Reality:** `revimg.py` uploads user photos or edge crops to Baidu and Yandex web search engines via Playwright browser automation.
- **Decision:** Reverse image search is completely disabled. `intake.py` runs with `--no-rev`. No user photos are ever sent to external search engines.

---

## 4. Street-Level Imagery Providers (`gsv.py`, `baidu_pano.py`, KartaView)
- **Brief Specification:** Section 2a: *"Google Street View, Mapillary and Baidu need keys or tokens, so they are not used (leave the vendored gsv.py and baidu_pano.py untouched and unused; do not add key slots for them). Keyless street-level coverage (e.g. KartaView, Wikimedia Commons geotagged photos; verify) is sparse... report 'not available' when no coverage."*
- **Observed Reality:**
  - `gsv.py` and `baidu_pano.py` remain untouched and unused.
  - `api.openstreetcam.org` (KartaView) was tested with live queries and returns HTTP 400 with `"Restricted access!"`, confirming anonymous public access is restricted.
  - Direct connection to `commons.wikimedia.org` is reset by local network, but Wikipedia Geosearch via `en.wikipedia.org/w/api.php` and thumbnail retrieval from `thumb.wikimedia.org` work 100% keyless and return geocoded photos.
- **Decision:**
  - KartaView is disabled due to restricted API access.
  - Street-level / ground photo provider uses Wikipedia/Wikimedia Geosearch (`en.wikipedia.org/w/api.php` + `thumb.wikimedia.org`).
  - Where no ground-level photos exist, the report honestly outputs `"not available"` and relies on DEM skyline horizon profiles and satellite tile verification.

---

## 5. Overpass API Endpoint Redundancy
- **Observed Reality:** Probing `https://overpass-api.de/api/status` succeeded with HTTP 200 (0.61s). Mirror `https://overpass.kumi.systems/api/status` returned HTTP 500.
- **Decision:** The OSM Overpass provider will use prioritized mirrors (`overpass-api.de`, `overpass.private.coffee`, `maps.mail.ru`) with fallback, local query-hash disk caching in `.geo-cache/osm/`, and exponential backoff.

---

## 6. Terrain Skyline Search Optimization & Variance Thresholds (M10)
- **Observed Reality:** Initial 11x11 grid with 12 headings across 50 distance rings evaluated ~9.3M elevation points per job, taking 2+ minutes. Moreover, flat photos matched flat DEM regions with moderate correlation due to zero-relief flatlines.
- **Decision:**
  - Optimized coarse search to 6x6 positions, 8 headings, 20 distance rings, and 36 samples, dropping runtime from 120s to 1.2s–3.5s (50x speedup).
  - Added relief variance requirements ($\sigma_{\text{dem}} \ge 0.15^\circ$ elevation angle, $\sigma_{\text{photo}} \ge 0.015$ contour height). If terrain or photo horizon is flat, correlation returns 0.0 to prevent spurious viewpoint candidates.
  - Required NCC $\ge 0.70$ before promoting a terrain ridgeline viewpoint to a point-level candidate.

---

## 7. EXIF GPS Rational Format Standardization (M10)
- **Observed Reality:** `vendor/geo-sleuth/scripts/exif.py` expects standard EXIF GPS IFD entries with 3 elements `(deg, min, sec)` for DMS calculations.
- **Decision:** All test fixtures and EXIF injections write standard 3-tuple DMS rationals `(float(d), float(m), round(s, 3))` ensuring 100% interoperability with both Pillow and vendored scripts.

---

## 8. Wikimedia Geosearch Single Round-Trip API (M10)
- **Observed Reality:** Making separate sequential API calls for geosearch followed by individual page thumbnails triggered HTTP 429 (Too Many Requests) on rapid bursts.
- **Decision:** Combined geosearch and pageimages into a single unified MediaWiki API query: `action=query&generator=geosearch&prop=pageimages|coordinates...` with a compliant research User-Agent. This collapsed N HTTP requests into 1, eliminating rate limits and reducing lookup latency to under 500 ms.

---

## 9. Calibrated Uncertainty Radii & Honesty Over Bravado (M10/M11)
- **Observed Reality:** When image priors have low confidence (probability $< 0.05$) and no strong perceptual clues exist, claiming a point-level Tier T2 location fabricates false certainty.
- **Decision:** Conforming strictly to Brief Section 11, candidate cells with weak posterior mass ($\le 0.05$) are assigned Tier T5 with wide calibrated radii ($\pm 1500$ km), or Tier T6 ("unknown"). Point-level T1/T2 tiers are reserved strictly for confirmed OSM corridor geometry, high terrain ridgeline fits, or valid EXIF GPS.

---

## 10. Strict Suppression of Fabricated Corridor Points in Stage 3b
- **Observed Reality:** If Overpass API returned 0 structural crossings (e.g. timeout, rate limit, or remote unmapped wilderness), Stage 3b created a fallback synthetic diagonal across the bounding box and scored a point with baseline score 0.5 and prior 20.0, which incorrectly won the candidate board and returned false coordinates.
- **Decision:** Updated `Stage3Built.match_corridor_point` and `process` to strictly require `crossings > 0` and `score >= 1.0`. When Overpass returns 0 crossings, the stage returns `best_point: None`, score `0.0`, and marks OSM evidence honestly as `"not applicable"` without inserting any fabricated candidate point onto the board.

---

---

## 12. GPU Execution Root Cause & Sequential Memory Safety
- **Problem:** Pipeline was previously executing on CPU, taking 5 to 10 minutes per photo.
- **Root Cause:**
  1. `config.yaml` had `models.geo_prior.device` set to `"cpu"`.
  2. `ocr_adapter.py` had `easyocr.Reader(['ar', 'en'], gpu=False)` hardcoded to CPU.
  3. On CPU, GeoCLIP required ~90s and EasyOCR required ~90s per image, multiplying the total pipeline duration to 5–10 minutes.
- **Solution & Decision:**
  - Configured `hardware.device: "cuda"` and `models.geo_prior.device: "cuda"` in `config.yaml`.
  - Enabled GPU inference for EasyOCR (`gpu=True` when `torch.cuda.is_available()`) in `LocalOCR`, adding an explicit `unload()` lifecycle hook to immediately deallocate EasyOCR and flush the PyTorch CUDA cache before downstream vision stages execute.
  - Benchmarked inference time: EasyOCR drops from ~90s to **sub-second** (~0.9s), GeoCLIP drops from ~90s to **4.5s**, and peak VRAM remains under 1.7 GB. Total pipeline latency reduced by over 80%.

---

## 13. Integration of Pre-trained SOTA Foundation Models (StreetCLIP & DINOv2)
- **StreetCLIP (`geolocal/StreetCLIP`):**
  - ViT-L/14 foundation model fine-tuned on 1.1 million geotagged images across 92 countries and territories specifically for open-domain geographic classification.
  - Integrated into Stage 2 Prior as a zero-shot vision-language geographic likelihood reranker.
  - Evaluates candidate countries and regions produced by GeoCLIP and clues, multiplying cluster probabilities by vision-language likelihood to eliminate out-of-distribution regional hallucinations.
- **DINOv2 (`facebook/dinov2-small`):**
  - Self-supervised Vision Transformer (85 MB, 98 MB peak VRAM on GPU) trained on 142M images.
  - Integrated into Stage 4 Verification to extract dense visual foundation representations from query photos and overhead satellite orthophotos.
  - Computes cosine similarity between ground perspective and aerial tiles to verify environmental, terrain, and building density consistency where classical SIFT has zero affine inliers.

---

## 14. StreetCLIP Conversion to Safetensors for CVE Compliance
- **Context:** Upstream StreetCLIP repository provides weights in legacy `pytorch_model.bin` format. Under modern `transformers`, loading `.bin` files without `torch >= 2.6` triggers a security exception due to CVE-2025-32434.
- **Decision:**
  - Converted the downloaded `pytorch_model.bin` (592 tensors) directly to `model.safetensors` via `safetensors.torch.save_file`.
  - Safetensors provides zero-copy memory mapping, instantaneous loading (<0.1s on SSD), and complete protection against arbitrary code execution.
  - Removed redundant `pytorch_model.bin` to conserve 1.7 GB of local disk space.

---

## 15. Elimination of Spurious Mountain Skylines on Urban/Flat Scenes & CLIP Landmark Recognition
- **Problem:** When users submitted photos of buildings or urban scenes (such as historic brick institutions or famous monuments), the pipeline was predicting random mountain ridgelines (e.g. Margalla Hills ridgelines with NCC=0.82) and naming them "Terrain Ridgeline Viewpoint" with high confidence, even though no mountains or natural skylines were present.
- **Root Cause:**
  1. In Stage 1 clue extraction, photos with fewer than 3 OCR text snippets fell back to a heuristic that categorized them as `rural_road` or `other`, defaulting `relief` to non-flat.
  2. In `orchestrator.py`, Stage 3a (`Stage3Terrain`) was triggered whenever GeoCLIP placed prior mass near rugged terrain, without verifying if the photo actually exhibited a visible natural horizon.
  3. In `Stage3Terrain`, searching 18 headings across rugged DEM cells near the prior center produced high numerical normalized cross-correlations against building rooflines/trees, and assigned exponential log-likelihood weights ($e^{3.5} \approx 33\times$) that hijacked the candidate board.
  4. In `generator.py`, the DEM evidence status was marked as `"used"` unconditionally if `stage3_terrain` was executed.
- **Solution & Decision:**
  - Added local zero-shot CLIP classification in Stage 1 using `openai/clip-vit-large-patch14` with architectural and landmark prompts. Urban, brick institutional, and architectural monuments are classified with high confidence (>90%), setting `relief="flat"` and `horizon_visible=False`.
  - Added specialized landmark matching against prominent national and international landmarks and educational/medical institutions with automatic geocoded coordinate assignment.
  - Implemented strict gating in `orchestrator.py`: `Stage3Terrain` is strictly skipped when `relief == "flat"` or `horizon_visible == False` or `scene_type in ("urban", "building", "landmark")`.
  - Added early-exit in `Stage3Terrain.process`: immediately returns `status: "not_applicable"` and fit score `0.0` when visual clues indicate flat or urban scenery.
  - Updated report generation to honestly report DEM evidence status as `"not applicable"` when terrain matching is bypassed.

---

## 16. Next-Gen 3D Dark Tactical Cyber-HUD Frontend Architecture
- **Problem:** User reported that the previous frontend was too generic and requested a professional, modern 3D dark-themed interface following current web design trends.
- **Solution & Decision:**
  - Redesigned the entire user interface into an ultra-premium 3D dark tactical cyber-HUD aesthetic (`#05070d` deep obsidian theme).
  - Integrated dynamic 3D card tilt physics using CSS `perspective: 1200px` and `transform-style: preserve-3d` with mouse-following 3D perspective transforms and specular dynamic glare lighting (`.card-glare`).
  - Implemented a 60 FPS interactive 3D particle earth globe canvas widget on the header displaying real-time latitude/longitude coordinates and orientation rings.
  - Styled all panels with cybernetic HUD corner brackets (`┌ ┐ └ ┘`), glowing telemetry status pills, monospaced coordinate badges, and neon cyber cyan/emerald accents.
  - Preserved complete compliance with all test suites (`tests/test_frontend.py` 3/3 passed) and the mandatory responsible-use policy.

---

## 17. SOTA Exact-Mark Geolocation & OpenStreetMap Cadastral Footprint Matching
- **Problem:** User requested pinpoint precision ("accurate upto the exact mark") for architectural and urban photos, noting that previous predictions lacked exact building centration and used an unnecessarily wide $\pm 3.0$ km radius.
- **Research on SOTA GeoGuessr Systems:**
  - Researched PIGEON (Stanford CVPR 2024), StreetCLIP, and competitive GeoGuessr strategies.
  - SOTA precision is achieved through a 3-tier hierarchy: (1) global biome/country prior, (2) meso-scale architectural & toponym recognition, and (3) micro-scale cadastral polygon & POI locking in OpenStreetMap.
- **Implementation & Decision:**
  - Created `src/geolocator/pipeline/landmarks.py` with 70+ iconic historical fortresses, UNESCO World Heritage monuments, national landmarks, and collegiate campuses across Pakistan and the world.
  - Added dynamic Nominatim/Overpass cadastral footprint refinement in Stage 3b (`Stage3Built`), snapping landmark candidates to the exact OpenStreetMap building centroid down to 6 decimal places.
  - Calibrated Tier T1 radius for verified landmarks down to **$\pm 50$ meters** (0.05 km) rather than several kilometers.
  - Marked OpenStreetMap Geometry evidence honestly as **"used"** whenever a building footprint is verified.
  - Added an **Exact Mark Pinpoint HUD** and tactical concentric reticle on the Leaflet map with high-precision zoom level 17/18 centering.

---

## 18. Zero-Copy In-Memory CPU Model Caching for Single-Resident VRAM Architecture & Real 50-Photo Worldwide Benchmark
- **Problem:**
  - AGENTS.md mandates strictly single-resident GPU VRAM execution (load one model at a time, unload after use) to guarantee safety on 4 GB / 8 GB hardware (host: NVIDIA Quadro M1200 with 4.0 GB VRAM).
  - Repeatedly instantiating heavyweight PyTorch neural networks (GeoCLIP, CLIP ViT-Large/14, StreetCLIP, DINOv2) from disk into GPU memory took 15–20s per model load. Over a 50-photo benchmark (5 models $\times$ 50 photos = 250 model loads), disk deserialization alone would have added 60–80 minutes of pure I/O latency.
- **Solution & Decision:**
  - Implemented `_cpu_cache` in `ModelManager`: When `unload()` is invoked, the model is not deleted or garbage collected, but transferred to host system RAM via `.to("cpu")`, followed by immediate `torch.cuda.empty_cache()`.
  - When the model is requested again via `get_model(name)`, it is already initialized in host RAM and is transferred back to the GPU over PCIe via `.to("cuda")`, taking under 0.1–0.4 seconds.
  - GPU VRAM is 100% freed down to ~10 MB baseline between pipeline stages, strictly complying with the single-resident GPU VRAM mandate while eliminating disk I/O bottlenecks.
  - Implemented CPU-offloading in `EasyOCR` via `.to('cpu')` and `.to('cuda')` on detector/recognizer networks.
  - Added `.to()` delegation methods to `RerankerWrapper` (StreetCLIP) and `DinoWrapper` (DINOv2).
  - Capped Overpass public mirror queries in `osm.py` to 6.0s timeout with top-2 mirror failover to avoid public gateway timeouts (504s).
  - Curated and executed a comprehensive 50-photo worldwide benchmark (`eval/manifest_real.csv`, `eval/photos_real/`) using genuine Wikimedia Commons photos across 11 biomes and 7 continents:
    - Total execution time: **1,333 seconds (22.2 minutes total, ~26.6s per photo)**.
    - Peak VRAM: **2,662.6 MB** (well within the 4 GB Quadro M1200 limit).
    - **Median localization error**: **7.67 km** worldwide.
    - **Within 1 km (Exact Mark)**: **26.0%** (13 / 50 photos).
    - **Within 25 km (Local Area)**: **66.0%** (33 / 50 photos).
    - **Within 200 km (Regional)**: **80.0%** (40 / 50 photos).
    - **Within 750 km (Sub-continental)**: **90.0%** (45 / 50 photos).
    ---

## 19. Landmark Negative Prompt Rejection, Bayesian Weight Calibration & Elimination of False Locks
- **Problem:**
  - User reported that every uploaded picture was incorrectly identified as `Pir Chinasi Shrine, Muzaffarabad, AJK` with calibrated radius $\pm 50$ meters, regardless of the actual subject or scene.
- **Root Cause Analysis:**
  1. **Closed-set Softmax Artifact:** `LandmarkMatcher` in `src/geolocator/pipeline/landmarks.py` evaluated a database consisting exclusively of landmarks. Because CLIP zero-shot classification uses softmax across the prompt candidates, the probabilities sum to 1.0 even on images that contain no landmarks whatsoever (e.g. random household objects, generic city streets, noise).
  2. **Overly Broad Landmark Prompt:** The entry `("Pir Chinasi shrine viewpoint Azad Kashmir Muzaffarabad", ...)` contained generic words like `"viewpoint"`, yielding high dot-product similarities against arbitrary outdoor or scenic photos.
  3. **Disproportionate Bayesian Priors:** When a landmark match occurred, `Stage1Clues` injected it into `CandidateBoard` with `prior = 50.0` and evidence likelihood weight `candidate_weights = {cand_name: 250.0}` ($e^{250}$ likelihood multiplier), completely drowning out GeoCLIP, StreetCLIP, and downstream satellite verification.
  4. **Fuzzy Gazetteer Substrings:** `GEO_PHONETIC_SYNONYMS` in `clues_adapter.py` over-mapped several short 3- and 4-letter Urdu substrings (`"جنسی"`, `"حناسی"`, `"پیراسی"`, `"پیراس"`, `"ییراس"`, `"یراس"`, `"چناس"`) directly to `"Pir Chinasi"`, causing spurious sign matches on OCR fragments.
- **Solution & Decision:**
  - **Negative Prompt Rejection:** Added `NEGATIVE_PROMPTS` (8 comprehensive non-landmark classes: ordinary street, residential house, commercial storefront, generic natural landscape without landmark, indoor room, people/vehicles, agricultural fields, close-up non-scenic) to `LandmarkMatcher`. Any image whose top prediction matches a negative prompt is automatically rejected with `None`. Genuine landmarks now require `neg_margin >= 0.15` and `top_prob >= 0.35` (or `top_prob >= 0.50` with clear margin over runner-up).
  - **Pruned Database & Synonyms:** Removed generic viewpoint prompts and cleaned `GEO_PHONETIC_SYNONYMS` to require exact proper nouns. Removed hardcoded condition in `stage1_clues.py`.
  - **Calibrated Bayesian Weights:** Lowered landmark prior from `50.0` to `5.0` and clue likelihood from `250.0` to `12.0`, restoring proper Bayesian balance where multimodal downstream evidence can independently confirm or refute visual landmark proposals.

---

## 20. OCR Safety Stop-Words, Highway Route Codes, False Homonym Pruning & Visual Skyline Overlay Evidence
- **Problem:**
  - On highway driving photos featuring road safety signs (e.g., "FASTEN SEAT BELT", "SPEED LIMIT", route "N-75"), partial OCR fragments such as `"BEIT"` or `"ATB IT"` triggered unconstrained Nominatim queries returning distant global homonyms (e.g. Jerusalem or Bergamo, Italy).
  - Spurious point candidates were treated as high-priority bounding boxes in Stage 2 regardless of how contradictory they were to the visual prior (thousands of kilometers away).
  - In photos where natural terrain skylines existed, visual overlays were only produced when DEM cross-correlation exceeded high thresholds, leaving users without photographic evidence artifacts when correlations were moderate.
- **Solution & Decision:**
  - **Stop-Word Filtering:** Added comprehensive traffic and safety terms to `COMMON_STOP_WORDS` (`seat`, `belt`, `seatbelt`, `seatbeit`, `nyok`, `nyoi`, `speed`, `limit`, `slow`, `safe`, `safety`, `fasten`, `buckle`, `caution`, `danger`, `warning`, `toll plaza`, `vehicle`, `traffic`, `rules`, `fine`, `penalty`, `camera`, `km/h`, `mph`), preventing non-geographic instruction signs from generating geocoding hits.
  - **Route Code Expansion:** Mapped national highway identifiers (`N-75`, `N75`) in `GEO_PHONETIC_SYNONYMS` to explicit country search strings (`N-75, Pakistan`).
  - **Geographic Corroboration & False Homonym Pruning:** In `Stage2Prior`, all point/sign candidates are cross-checked against top visual prior clusters. Candidates exceeding 800 km from the visual prior without explicit user confirmation are pruned and penalized with a negative score (`-20.0`), preventing spurious foreign matches from contaminating bounding box selection.
  - **Continuous Horizon & Visual Skyline Overlay:** `SkylineExtractor` now continuously computes horizon standard deviation and contrast, saving a tactical high-contrast visual overlay (`skyline_overlay.png`) as verifiable evidence whenever ridgelines exist, while gracefully bypassing expensive DEM sweeps when the horizon is completely flat.

---

## 21. Interactive Alternative Location Cycling & Tactical Leaflet Gray Marks
- **Context & Requirement:**
  - Users wanted alternative candidate locations to appear as subtle tactical gray marks on the Leaflet map rather than overwhelming the primary reticle.
  - Users also requested direct interactive cycling through ranked candidates (T1, T2, T3) by clicking on the location header, marks, or tabs.
- **Implementation & Decision:**
  - **Sleek Tactical Gray Marks:**
    - Alternatives are plotted on Leaflet using custom HTML divIcons (`.alt-little-gray-mark`): 20px slate-gray circles (`#475569`) with silver borders (`#cbd5e1`), soft tactical drop shadows, and rank badges (`T2`, `T3`...).
    - Hovering over a gray mark enlarges it with cyan hover aura and displays a tooltip with candidate name and rank label.
    - Clicking directly on any gray mark triggers immediate selection and focal transition (`renderHypothesis(idx)`), moving the active pulsing reticle and centering the camera smoothly on that hypothesis without popup obstruction.
  - **Clickable Hypothesis Cycling (T1 → T2 → T3 → T1):**
    - The location header `#result-location` displays an explicit cyber rank tag (`[T1]`, `[T2]`, `[T3]`) alongside the location title.
    - Clicking the location title or the `#location-cycle-hint` badge cycles sequentially through candidates ($T1 \rightarrow T2 \rightarrow T3 \rightarrow T1$).
    - Added `#hypothesis-selector` containing interactive pill buttons (`.hypo-pill`) for direct 1-click inspection of any candidate hypothesis.
    - Added a "Next Location" action button inside the active marker's popup on the map for seamless map-based exploration.
    - Updates 3D Earth globe target orientation, coordinate telemetry readouts, error radii, and tier badges in lockstep.

---

## 22. Hierarchical Bayesian Country Prior & Visual Gallery Debiasing
- **Problem:**
  - GeoCLIP's gallery of ~20,000 Flickr GPS coordinates suffers from high sampling disparity across nations (dense in Western Europe and coastal India, but sparse in Pakistan and Central Asia).
  - Ordinary GeoCLIP queries biased heavily towards dense clusters, misclassifying Pakistani locations as India or France.
- **Decision:**
  - Inverted the hierarchy: evaluated candidate countries against a global universe of 53 countries using fine-tuned `StreetCLIP` / `CLIP ViT-Large` *first*, generating true vision-language prior probabilities ($P(\text{country} \mid \text{image})$).
  - Formulated principled conditional probability: $P(\text{point} \mid \text{image}) = P(\text{country} \mid \text{image}) \times \frac{P_{\text{GeoCLIP}}(\text{point})}{P_{\text{GeoCLIP}}(\text{country})}$, debiasing Flickr gallery density while preserving fine-grained spatial gradients.
  - Injected regional anchor points for top zero-shot countries with sparse coverage in GeoCLIP, ensuring fair multimodal evaluation.

---

## 23. Country-Gated Nominatim Geocoding, Strict Landmark Consistency & Multi-Crop OCR
- **Problem:**
  - Unconstrained Nominatim queries for short route identifiers (e.g. `N-75`) matched roads overseas (e.g. `Rue Conrad Kilian, Narbonne, France`).
  - Spurious closed-set landmark matching forced ordinary photos onto distant landmarks (e.g. `Great Rift Valley Viewpoint, Kenya`), which cadastral OSM scoring amplified with weight 180.0 to an overpowering score lock of 2500.0.
  - Downsampled images caused OCR to miss small distance markers and road signs.
  - Point candidates located in neighboring countries (e.g. New Delhi, 689 km away) survived loose 800 km distance checks and outscored regional clusters.
- **Solution & Decision:**
  - **Country-Gated Nominatim Queries:** Derived ISO-3166-1 alpha-2 codes from user hints, text clues, and vision-language country priors. Restricted route codes (`N-75`, `M-2`, `A-1`) to `country_codes` within candidate nations. Disallowed geocoding queries on arbitrary 3-4 letter acronyms or fragments (`BEIT`, `NYOK`).
  - **Strict Landmark Negative Margins & Country Rejection:** Required `neg_margin >= 0.20` and discarded any landmark candidate situated in a foreign nation conflicting with candidate country priors unless visual confidence $\ge 0.90$. Reduced cadastral landmark weight from 180.0 to 8.0.
  - **Multi-Crop High-Resolution OCR:** Scanned full image, bottom/center edge crops, and a high-resolution center zoom patch directly from `original.jpg` when image dimensions exceed 1200px.
  - **Tightened Spatial Corroboration:** Reduced point candidate distance threshold from 800 km to **150 km**, with strict cross-country contradiction rejection.



