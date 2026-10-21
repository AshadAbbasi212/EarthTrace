# EarthTrace Technical Architecture & Multimodal Pipeline

This document details the internal architecture, mathematical formulations, and multimodal evidence solvers that power EarthTrace.

---

## Pipeline Execution Stages

```mermaid
flowchart TD
    Photo[Input Photograph] --> S0[Stage 0: Intake & EXIF Parsing]
    S0 -->|EXIF GPS Found| FastPath[Fast-Path Verification]
    S0 -->|No EXIF GPS| S1[Stage 1: Clue Extraction & RapidOCR]
    
    S1 --> S2[Stage 2: Global Prior & Biome Filtering]
    subgraph S2_Group [Stage 2: Candidate Formation]
        S2 --> GeoCLIP[GeoCLIP Vision Prior]
        S2 --> Climate[Köppen-Geiger Classification]
        S2 --> LandCover[ESA WorldCover Filtering]
        S2 --> SpatialClustering[Spatial Coordinate Clustering]
    end
    
    SpatialClustering --> S3[Stage 3: Specialized Solvers]
    subgraph S3_Group [Stage 3: Spatial Solvers]
        S3 -->|Terrain / Mountains| S3a[Stage 3a: 3D DEM Skyline NCC Sweeper]
        S3 -->|Roads / Rail / Rivers| S3b[Stage 3b: OSM Infrastructure Corridors]
        S3 -->|Architectural Landmarks| S3c[Stage 3c: Cadastral Footprint Matcher]
    end
    
    S3a --> S4[Stage 4: Multimodal Verification]
    S3b --> S4
    S3c --> S4
    FastPath --> S4
    
    subgraph S4_Group [Stage 4: Verification & Resection]
        S4 --> SatCheck[Satellite Orthophoto SIFT Homography]
        S4 --> StreetCheck[Keyless Street Imagery Geosearch]
        S4 --> PoseSolver[3D Camera Exterior Orientation]
    end
    
    S4 --> S5[Stage 5: Decision Engine & Multi-Format Report]
    S5 --> OutJSON[report.json]
    S5 --> OutHTML[report.html]
    S5 --> OutGeoJSON[report.geojson]
    S5 --> WebUI[Web Interface]
```

---

## The 5 Multimodal Evidence Pillars

### 1. Linear Infrastructure Corridors (OpenStreetMap)
Extracts linear vector ways (highways, railways, bridges, river corridors, and canals) within the candidate search radius using Overpass. Computes polyline heading signatures and junction topologies.

### 2. 3D Elevation Skylines (30m Terrarium DEM)
Fetches ~30m Digital Elevation Model tiles. Simulates physical raycasts from candidate observer positions, factoring in:
- **True Earth Curvature:** $R = 6371\text{ km}$
- **Atmospheric Refraction:** Terrestrial coefficient $k = 0.13$
- **Normalized Cross-Correlation (NCC):** Sweeps horizon silhouettes across $360^\circ$ azimuth to locate peak correlation with photographic skylines.

### 3. Satellite Orthophoto Homography
Fetches keyless overhead imagery for candidate coordinates. Computes SIFT keypoint descriptors and FLANN matching to estimate homography matrix $H$ and verify surface features.

### 4. Ground-Level Geotagged Imagery
Queries keyless geotagged image repositories (Wikimedia Commons) within candidate bounds. When remote or wilderness locations have no street imagery, the system explicitly reports `"status": "not available"`.

### 5. Cadastral Building Facades & Footprints
Detects architectural contours and building facades using adaptive contour extraction. Matches polygonal aspect ratios, area footprints, and orientation angles directly against OpenStreetMap building polygon geometries.

---

## Memory & Resource Management

EarthTrace enforces a strict **Single-Resident ModelManager** architecture:
- Deep learning models (GeoCLIP, RapidOCR) are loaded sequentially into GPU memory.
- Inference is performed in thread-safe batches.
- PyTorch CUDA memory caches are purged (`torch.cuda.empty_cache()`) immediately after inference.
- Guaranteed to operate within a **4 GB VRAM** envelope on consumer GPUs.
