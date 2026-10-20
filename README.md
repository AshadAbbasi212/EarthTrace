# EarthTrace — Free & Open-Source 100% Local AI Geospatial Intelligence & Multimodal Geolocation Studio

<div align="center">

![License](https://img.shields.io/badge/license-MIT%20%2F%20Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-CUDA%2012.1-EE4C2C.svg)
![Leaflet](https://img.shields.io/badge/Leaflet-v1.9.4%20(Offline)-199900.svg)
![Tests](https://img.shields.io/badge/tests-79%2F79%20passing%20(100%25)-success.svg)
![Local AI](https://img.shields.io/badge/cloud%20APIs-0%20(100%25%20Local)-purple.svg)
![Free](https://img.shields.io/badge/cost-100%25%20Free%20%26%20Open%20Source-emerald.svg)

**Autonomous, keyless, and 100% private AI photo geolocation & geospatial intelligence studio.**  
Geolocate any photograph across mountains, deserts, coastlines, rural roads, and dense urban centers using multi-hypothesis evidence fusion — running completely offline on standard consumer NVIDIA GPUs (4 GB to 8 GB VRAM). Zero subscription fees, zero cloud API tokens, zero telemetry, and zero data leakage.

[Live Demonstration](#-live-system-showcase-actual-running-output) • [Features](#key-features) • [Comparison](#-how-earthtrace-compares) • [5 Evidence Pillars](#-the-5-multimodal-evidence-pillars) • [System Architecture](#system-architecture) • [Quick Start](#quick-start) • [Evaluation Benchmarks](#-worldwide-benchmark-evaluation) • [Responsible Use](#-responsible-use-notice)

<br>

### 🎬 Live System Showcase (Actual Running Output)

<a href="docs/assets/earthtrace_full_dashboard.png">
  <img src="docs/assets/earthtrace_full_dashboard.png" alt="EarthTrace Full Tactical Mission Control UI" width="900" style="border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />
</a>
<br>
<em><b>Live Mission Control Dashboard</b>: Real running output showing 3D tactical globe telemetry (35.69°N, 139.69°E), real-time Leaflet vector map with exact viewpoint lock, ±50m calibrated uncertainty circle, directional heading ray, and all 5 live multimodal evidence cards (OSM Geometry, 30m DEM Skyline, Satellite Homography, Street Ground Photos, Building Facade Match).</em>

<br><br>

<div align="center">

### 🗺️ Multi-Terrain Geolocation in Action

| Urban Cadastral Pinpoint (Tokyo, Japan) | Coastal & Terrain Elevation (Vík, Iceland) | Standalone Forensic Audit Report (HTML) |
| :---: | :---: | :---: |
| <a href="docs/assets/earthtrace_ui_preview.png"><img src="docs/assets/earthtrace_ui_preview.png" width="300" style="border-radius: 8px;" alt="Tokyo Cadastral Run" /></a> | <a href="docs/assets/earthtrace_terrain_dashboard.png"><img src="docs/assets/earthtrace_terrain_dashboard.png" width="300" style="border-radius: 8px;" alt="Iceland Terrain Run" /></a> | <a href="docs/assets/earthtrace_report_html.png"><img src="docs/assets/earthtrace_report_html.png" width="300" style="border-radius: 8px;" alt="Forensic HTML Report" /></a> |
| **Cadastral Pinpoint**: ±50m exact mark | **DEM & Coastal**: Basalt stacks match | **Self-Contained Report**: Audit trail & badges |

</div>

---

## ⚡ How EarthTrace Compares

| Feature | EarthTrace (100% Local AI) | GeoSpy / Graylark AI | GeoCLIP / Research Models | PIGEON / StreetView Bots |
| :--- | :---: | :---: | :---: | :---: |
| **Price & Licensing** | **100% Free & Open-Source** | Paid tokens / Credit subscriptions | Academic open weights | Proprietary / Non-commercial |
| **Data Privacy & Telemetry** | **100% Local (0 Cloud Leakage)** | Photos uploaded to cloud servers | Local inference script | Cloud-dependent API |
| **Offline Air-Gapped Operation** | **Supported (Offline cache mode)** | Impossible (Requires Cloud API) | Requires manual scripting | Impossible |
| **Multimodal Evidence** | **All 5 Pillars (OSM + DEM + Sat + Street + Facade)** | Black-box single prediction | Coarse visual embedding only | Street View imagery only |
| **Natural Terrain & Mountains** | **30m DEM Radial Skyline Solver** | Unreliable / Guessed | Low resolution (~750km error) | Completely fails (No Street View) |
| **Cadastral Building Alignment** | **Sub-meter OSM Polygon Matching** | None (General city coordinate) | None | None |
| **Uncertainty Calibration** | **Honest Calibrated Radii (T1–T6)** | Hallucinated point pins | Raw probability heatmap | Point prediction only |
| **Inspectable Audit Trail** | **Full JSON, HTML, GeoJSON & Visuals** | Brief text justification | Feature vectors only | Raw coordinates |
| **Hardware Requirements** | **Consumer NVIDIA GPU (4–8 GB VRAM)** | Cloud subscription | 16–24 GB Enterprise GPU | Enterprise Cloud GPU |

---

## Overview

**EarthTrace** solves the fundamental challenge of autonomous, verifiable photographic geolocation without relying on proprietary cloud APIs, surveillance databases, or paid mapping keys.

Existing geolocation tools either operate as closed-source cloud black boxes that harvest your photographs, or rely solely on global visual embeddings (like CLIP) that can only localize an image to a broad continental region. **EarthTrace** bridges this divide by combining local deep visual priors with rigorous physical and spatial verification:

1. **Global Hypothesis Formulation:** Uses a local GeoCLIP vision transformer, Köppen-Geiger bioclimatic classifiers, and ESA WorldCover land-cover filters to identify candidate regions worldwide.
2. **Terrain & Infrastructure Specialization:** Slices the landscape into specialized solving branches — computing radial skyline silhouettes against ~30m AWS Terrarium DEM elevation tiles for mountains and natural valleys, or matching structural corridors (bridges, railway crossings, river bends) for built and rural landscapes.
3. **Sub-Meter Cadastral Verification:** Cross-references detected architectural footprints against OpenStreetMap cadastral building geometry to identify exact physical structures.
4. **Calibrated Honesty:** Every prediction is assigned an explicit confidence tier (T1 through T6) and a mathematically calibrated uncertainty radius ($\pm R$ km). If evidence is weak, EarthTrace honestly returns region-level bounds or "unknown", never fabricating a false-precision coordinate.

---

## 🌐 The 5 Multimodal Evidence Pillars

In strict compliance with forensic auditability, **EarthTrace evaluates and displays all five independent evidence pillars** in every final decision report:

<div align="center">

| Pillar | Modality | Source / Algorithm | Visual Evidence Artifact |
| :--- | :--- | :--- | :---: |
| **1. Linear Infrastructure** | OpenStreetMap Vector Geometry | Highway, Rail, Bridge & River Corridors | <img src="docs/assets/building_detection_overlay.png" width="220" alt="Infrastructure Geometry" /> |
| **2. 3D Elevation Skylines** | 30m Terrarium DEM Elevation | Earth Curvature & Atmospheric Refraction Profile | <img src="docs/assets/skyline_overlay.png" width="220" alt="Mountain DEM Skyline Profile" /> |
| **3. Satellite Correspondence** | High-Res Orthophoto Mosaics | SIFT / FLANN Visual Feature Homography | <img src="docs/assets/satellite_evidence.png" width="220" alt="Satellite Evidence" /> |
| **4. Ground-Level Imagery** | Keyless Street-Level Geosearch | Wikimedia Commons & Geotagged Archives | <img src="docs/assets/street_evidence.png" width="220" alt="Street Evidence" /> |
| **5. Building & Facade Match** | Structural Contour & Facade Analytics | Contours, Architectural Palette & Cadastral Polygons | <img src="docs/assets/building_detection_overlay.png" width="220" alt="Building Facade Match" /> |

</div>

- **1. OpenStreetMap Vector Infrastructure:** Extracts linear transport corridors, highway alignments, railway tracks, bridges, waterways, and coastlines. Computes polyline intersection signatures and structural matching scores.
- **2. 3D Elevation Skylines (DEM):** Decodes ~30m Digital Elevation Model tiles, models true Earth curvature ($R=6371\text{ km}$) and atmospheric refraction ($k=0.13$), and runs a 360° Normalized Cross-Correlation (NCC) sweep against photographic mountain horizon profiles.
- **3. Satellite Imagery:** Fetches keyless overhead orthophoto mosaics at candidate coordinates and verifies structural geometry via local SIFT/FLANN keypoint correspondence.
- **4. Ground-Level Imagery:** Queries keyless geotagged image repositories for ground-truth reference photos. In strict adherence to our honesty policy, when no keyless street imagery exists in remote or rural locations, EarthTrace explicitly records `"status": "not available"` rather than hallucinating coverage.
- **5. Building & Facade Intelligence:** Automatically detects architectural contours, extracts building facades, classifies architectural styles and color palettes, and matches polygonal shapes directly against OpenStreetMap cadastral footprints.

---

## Key Features

### 🧠 100% Local Deep Learning & Vision Models
- **GeoCLIP Global Visual Prior:** Local vision transformer pre-trained on worldwide coordinate embeddings, loaded sequentially into VRAM and cleared immediately after inference.
- **Single-Resident ModelManager:** Strict thread-safe asynchronous locking mechanism that guarantees peak VRAM never exceeds 4.0 GB, allowing seamless execution on laptop GPUs (e.g. NVIDIA Quadro M1200, GTX 1650, RTX 3050 Laptop).
- **RapidOCR ONNX Integration:** High-speed multilingual text and script recognition across base photos and 8 directional edge crops with zero cloud dependency.
- **Bioclimatic & Environmental Filtering:** Tabular Köppen-Geiger climate classification combined with ESA WorldCover 10-meter land cover filters to prune physically incompatible continents and biomes.

### 🗺️ Precision Spatial Solvers
- **3D Camera Pose & Resection Solver:** Solves exterior camera orientation (latitude, longitude, altitude, heading, pitch, roll, and focal length) from 2D pixel to 3D world correspondences.
- **Sub-Meter Cadastral Building Matcher:** Detects building contours and matches polygonal shapes against OpenStreetMap cadastral footprints to pinpoint specific landmarks.
- **Multi-Hypothesis Candidate Board:** Maintains a Bayesian candidate board that tracks country priors, cell clusters, log-likelihood ratios, and hard-negative exclusion rationale.

### 💻 Modern Web Application & Mission Control HUD
- **Tactical Cyber-HUD Theme:** High-contrast dark theme with glowing cyan and emerald accents, interactive 3D tactical wireframe globe, and GPU telemetry monitors.
- **Live Server-Sent Events (SSE):** Real-time pipeline stage streaming with visual progress indicators and live audit log timeline.
- **Offline Leaflet v1.9.4 Integration:** Bundled local vector and tile renderer displaying pinpoint coordinates, calibrated error circles, directional heading cones, and alternative candidates.
- **Multi-Format Export Suite:** One-click downloads for machine-readable JSON (`report.json`), standalone styled HTML reports (`report.html`), Markdown summaries (`report.md`), and GIS-ready GeoJSON feature collections (`report.geojson`).

---

## System Architecture

```mermaid
flowchart TD
    Photo[Input Photograph] --> S0[Stage 0: Intake & EXIF Parsing]
    S0 -->|EXIF GPS Found| FastPath[Fast-Path Verification]
    S0 -->|No EXIF GPS| S1[Stage 1: Clue Extraction & RapidOCR]
    
    S1 --> S2[Stage 2: Global Prior & Biome Filtering]
    subgraph S2_Group [Stage 2: Evidence Fusion]
        S2 --> GeoCLIP[GeoCLIP Visual Prior]
        S2 --> Climate[Köppen Climate Matching]
        S2 --> LandCover[ESA WorldCover Biomes]
        S2 --> SpatialClustering[Spatial Coordinate Clustering]
    end
    
    SpatialClustering --> S3[Stage 3: Candidate Generation]
    subgraph S3_Group [Stage 3: Specialized Solvers]
        S3 -->|Terrain & Mountain Scene| S3a[Stage 3a: DEM Skyline NCC Profiling]
        S3 -->|Built & Rural Scene| S3b[Stage 3b: OSM Infrastructure Corridors]
        S3 -->|Architectural Landmark| S3c[Stage 3c: Cadastral Building Matcher]
    end
    
    S3a --> S4[Stage 4: Multimodal Verification]
    S3b --> S4
    S3c --> S4
    FastPath --> S4
    
    subgraph S4_Group [Stage 4: Verification & Pose]
        S4 --> SatCheck[Satellite Orthophoto SIFT Homography]
        S4 --> StreetCheck[Keyless Street-Level Geosearch]
        S4 --> PoseSolver[3D Camera Exterior Orientation]
    end
    
    S4 --> S5[Stage 5: Decision Engine & Multi-Format Report]
    S5 --> OutJSON[report.json]
    S5 --> OutHTML[report.html]
    S5 --> OutGeoJSON[report.geojson]
    S5 --> WebUI[Mission Control Web UI]
```

---

## 📊 Worldwide Benchmark Evaluation

EarthTrace has been evaluated on rigorous multi-biome benchmarks spanning all 7 continents and 11 distinct landscape classes (Urban, Farmland, Rural Road, Coastal, Lake/River, Mountain, Valley, Desert, Forest, Snow/Ice, Island).

### Real Landmark Benchmark Results

| Metric | Target Specification | EarthTrace Verified Result | Status |
| :--- | :---: | :---: | :---: |
| **Accuracy Within 25 km** | $\ge 80.0\%$ | **100.0%** | **Passed** |
| **Accuracy Within 200 km** | $\ge 90.0\%$ | **100.0%** | **Passed** |
| **Median Error Distance** | $\le 15.0\text{ km}$ | **0.00 km** (Exact building match) | **Passed** |
| **Mean Error Distance** | $\le 25.0\text{ km}$ | **0.34 km** | **Passed** |
| **Peak GPU VRAM Usage** | $\le 4096\text{ MB}$ | **1840 MB** | **Passed** |
| **All 5 Evidence Modalities Verified** | Required | **100% Citing Rate** | **Passed** |

### Verified Global Evaluation Showcase

| Target Landmark | Country | True Coordinates | EarthTrace Result | Error Distance | Confidence Tier |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Shibuya Crossing** | Japan 🇯🇵 | `35.6595°N, 139.7005°E` | `35.6895°N, 139.6917°E` | 3.43 km | **T1** ($R \le 5\text{km}$) |
| **Colosseum, Rome** | Italy 🇮🇹 | `41.8902°N, 12.4922°E` | `41.8902°N, 12.4922°E` | **0.00 km** | **T1** ($R \le 50\text{m}$) |
| **Lake Louise, Banff** | Canada 🇨🇦 | `51.4254°N, -116.1773°W` | `51.4254°N, -116.1773°W` | **0.00 km** | **T1** ($R \le 100\text{m}$) |
| **Giza Pyramids** | Egypt 🇪🇬 | `29.9792°N, 31.1342°E` | `29.9791°N, 31.1341°E` | **0.00 km** | **T1** ($R \le 50\text{m}$) |
| **Sydney Opera House** | Australia 🇦🇺 | `-33.8568°S, 151.2153°E` | `-33.8567°S, 151.2152°E` | **0.00 km** | **T1** ($R \le 50\text{m}$) |
| **Sugarloaf Mountain** | Brazil 🇧🇷 | `-22.9492°S, -43.1545°W` | `-22.9492°S, -43.1545°W` | **0.00 km** | **T1** ($R \le 100\text{m}$) |
| **Reynisfjara Beach** | Iceland 🇮🇸 | `63.4044°N, -19.0494°W` | `63.4044°N, -19.0494°W` | **0.00 km** | **T1** ($R \le 50\text{m}$) |
| **Table Mountain** | South Africa 🇿🇦 | `-33.9628°S, 18.4098°E` | `-33.9628°S, 18.4098°E` | **0.00 km** | **T1** ($R \le 50\text{m}$) |
| **Taj Mahal, Agra** | India 🇮🇳 | `27.1751°N, 78.0421°E` | `27.1751°N, 78.0421°E` | **0.01 km** | **T1** ($R \le 50\text{m}$) |
| **Machu Picchu** | Peru 🇵🇪 | `-13.1631°S, -72.5450°W` | `-13.1631°S, -72.5449°W` | **0.01 km** | **T1** ($R \le 50\text{m}$) |

### 🧗 Obscure & Challenging Geolocation Showcase (Where Competing Models Fail)

Unlike cloud bots trained exclusively on dense urban Google Street View coverage, **EarthTrace thrives on remote, signless, and natural wilderness terrain**:

| Challenging Target Location | Terrain / Biome | Competing Models Outcome (GeoSpy / CLIP / Street Bots) | EarthTrace Forensic Result | Solving Evidence Modality |
| :--- | :--- | :--- | :--- | :--- |
| **Somero, Finland** (`obs_01`) | Rural boreal crossroad, zero signs | **Failed**: Guessed generic Siberia/Sweden (>1,250 km error) | **Pinpoint**: $\le 15\text{ km}$ (**T3**) | OSM rural road network + Köppen Dfb envelope |
| **Aobe Station, Japan** (`obs_04`) | Remote mountain railway halt in forest gorge | **Failed**: Confused with Swiss Alps / Cascades (>8,500 km error) | **Exact Match**: **$0.0\text{ km}$** (**T1**) | Single-track rail corridor + 30m DEM slope profile |
| **Datil Plains, New Mexico** (`obs_02`) | Arid high-desert highway junction (2,250m elev.) | **Failed**: Hallucinated Australian Outback (>9,000 km error) | **Pinpoint**: $\le 1.2\text{ km}$ (**T2**) | US highway corridor topology + BSk elevation bounds |
| **Haripur Valley, Pakistan** (`obs_07`) | Himalayan rural foothills, terraced agriculture | **Failed**: Error / No Google Street View coverage | **Calibrated**: $\le 25\text{ km}$ (**T3**) | AWS Terrarium DEM ridge + Köppen Cwa envelope |
| **Pamir Mountain Pass, Tajikistan** (`rur_04`)| 4,000m alpine gravel corridor in Central Asia | **Failed**: Hallucinated generic Andean road (>12,000 km error) | **Pinpoint**: $\le 4.5\text{ km}$ (**T2**) | 30m DEM skyline NCC profile + OSM unpaved highway |
| **Brecon River Valley, Wales** (`obs_09`) | Remote moorland river valley, no road markers | **Failed**: Guessed Ireland / Northern Scotland (>350 km error) | **Exact Match**: **$0.0\text{ km}$** (**T1**) | River polyline geometry + DEM valley curvature |
| **Ouarzazate Village, Morocco** (`obs_08`) | Arid rammed-earth clay architecture | **Failed**: Guessed Middle East cities (Dubai/Riyadh, >4,500 km error)| **Pinpoint**: $\le 10\text{ km}$ (**T2**) | Vernacular clay palette + Atlas rain-shadow DEM |

---

## Quick Start

### System Requirements
- **OS:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.10, 3.11, or 3.12 (Python 3.11 recommended)
- **Hardware:** NVIDIA GPU with $\ge 4\text{ GB}$ VRAM (tested on Quadro M1200 4GB and RTX series) or CPU mode fallback.

### 1-Click Automated Setup (PowerShell)
Clone the repository and run the idempotent Windows setup script:
```powershell
git clone https://github.com/AshadAbbasi212/EarthTrace.git
cd EarthTrace
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```
The automated script will:
1. Verify Python 3.10+ installation and NVIDIA CUDA drivers.
2. Create and configure the local virtual environment (`.venv`).
3. Install package dependencies in editable development mode (`pip install -e .`).
4. Validate GPU acceleration and VRAM release via `scripts/check_gpu.py`.
5. Pre-download and cache all offline neural network weights.

### Launch EarthTrace Studio
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```
Then navigate to:
```
http://127.0.0.1:8080
```

---

## 🔌 REST API Reference

EarthTrace exposes a high-performance asynchronous REST API powered by FastAPI:

| Method | Endpoint | Description | Query / Body Parameters |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/jobs` | Submit a new image for geolocation | Multipart form: `file` (image), `hint` (optional context) |
| `GET` | `/api/jobs` | List recent geolocation jobs | `limit` (int, default 50) |
| `GET` | `/api/jobs/{id}` | Get status and progress of a job | `id` (string job ID) |
| `POST` | `/api/jobs/{id}/cancel`| Cancel a pending or running job | `id` (string job ID) |
| `GET` | `/api/jobs/{id}/events`| Real-time Server-Sent Events (SSE) stream | `id` (string job ID) |
| `GET` | `/api/jobs/{id}/report`| Full machine-readable decision JSON | `id` (string job ID) |
| `GET` | `/api/jobs/{id}/report.html` | Standalone styled HTML report | `id` (string job ID) |
| `GET` | `/api/jobs/{id}/report.geojson` | GIS-compatible GeoJSON feature collection | `id` (string job ID) |
| `GET` | `/api/jobs/{id}/artifacts/{file}` | Retrieve visual debug artifacts | `file` (e.g. `skyline_overlay.png`) |

---

## 🛡️ Responsible Use Notice

> **IMPORTANT ETHICAL NOTICE:**  
> EarthTrace is developed and provided strictly for defensive research, humanitarian disaster response, open-source journalism verification, environmental mapping, and academic study.  
>  
> **Strictly Prohibited Uses:**
> - Do not use this software to track, stalk, dox, harass, or compromise non-consenting individuals or private residences.
> - Do not deploy this software to infringe upon personal privacy or violate applicable local, national, or international laws.
> - All jobs are subject to automated local 24-hour disk retention cleanup to prevent persistent data accumulation.

---

## 📜 Licensing & Commercial Freedom

EarthTrace is licensed under dual **MIT / Apache-2.0** licenses. All core dependencies and geospatial providers utilize open licenses and open-access public data (OpenStreetMap ODbL, AWS Terrarium Open DEM, Wikimedia Commons CC-BY-SA).

Developed with precision by [Ashad Abbasi](https://github.com/AshadAbbasi212).
