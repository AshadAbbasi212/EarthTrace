# Third-Party Notices & Attribution

EarthTrace incorporates, wraps, or queries several open-source libraries and open-access geospatial data providers. This document provides formal attribution and licensing notices in compliance with each upstream project's terms.

---

## 1. Vendored Libraries

### geo-sleuth
- **Path:** `vendor/geo-sleuth/`
- **Copyright:** (c) 2026 Oldcircle
- **License:** MIT License
- **Usage:** Wrapped via adapter modules in `src/geolocator/adapters/` without in-place modification. Original license and copyright preserved in `vendor/geo-sleuth/LICENSE`.

---

## 2. Open Geospatial Data Providers

### OpenStreetMap (OSM)
- **Data Source:** Overpass API / Nominatim
- **License:** Open Database License (ODbL) 1.0
- **Attribution:** "© OpenStreetMap contributors" (https://www.openstreetmap.org/copyright).
- **Compliance:** Requests include customized descriptive `User-Agent` headers and abide by public rate limits (<1 request/sec). Cached locally to `.geo-cache/` to eliminate redundant queries.

### AWS Terrarium Digital Elevation Model (DEM)
- **Data Source:** Mapzen / Nextzen Open Data on AWS S3 (`s3://elevation-tiles-prod/terrarium/`)
- **License:** Open Data / Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Attribution:** Elevation data derived from USGS, SRTM, ETOPO1, and open regional LIDAR surveys.

### Wikimedia Commons
- **Data Source:** Keyless Wikimedia Commons API for ground-truth reference imagery.
- **License:** Various open licenses (primarily CC-BY-SA 3.0, CC-BY-SA 4.0, and Public Domain).
- **Attribution:** Individual photographer names and direct source URLs are recorded in the manifest and report artifacts (`report.json`).

### ESA WorldCover 10m 2021
- **Data Source:** European Space Agency WorldCover project.
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Attribution:** "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium."

---

## 3. Machine Learning Models & Core Packages

### GeoCLIP
- **License:** MIT License
- **Authors:** Vicente Vivanco, et al.
- **Weights:** Downloaded from open Hugging Face repository during initial setup; executed locally.

### RapidOCR (ONNX Runtime)
- **License:** Apache License 2.0
- **Authors:** RapidAI Contributors

### Leaflet (v1.9.4)
- **License:** 2-Clause BSD License
- **Copyright:** (c) 2010-2023, Vladimir Agafonkin; (c) 2010-2011, CloudMade
- **Path:** Bundled locally in `src/geolocator/web/static/vendor/leaflet/` for offline mapping.
