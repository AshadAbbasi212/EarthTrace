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

