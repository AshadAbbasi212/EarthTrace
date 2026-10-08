# Keyless Data Sources Specification (docs/DATA_SOURCES.md)

All data sources utilized in this project are strictly keyless, open, and free of authentication tokens, API keys, or accounts. Every source listed below has been tested and verified without credentials during Milestone 0.

---

## Verified Data Sources

| Purpose | Source & Endpoint | Authentication | Tested Status | License / Policy | Caching & Rate Limiting |
|---|---|---|---|---|---|
| **Vector Map Data** | OpenStreetMap Overpass API<br>- Primary: `https://overpass-api.de/api/interpreter`<br>- Mirror: `https://overpass.private.coffee/api/interpreter`<br>- Mirror: `https://maps.mail.ru/osm/tools/overpass/api/interpreter` | None (Anonymous) | **PASS** (HTTP 200, 0.61s) | ODbL (Open Database License). Respect Overpass fair use: small bounding boxes, polite retries. | Disk cache keyed by SHA-1 of Overpass QL query in `.geo-cache/osm/`. Exponential backoff across mirrors. |
| **Reverse Geocoding / POI** | OpenStreetMap Nominatim<br>`https://nominatim.openstreetmap.org/search` | None (Anonymous) | **PASS** (HTTP 200, 0.82s) | ODbL. Strict usage policy: <= 1 req/sec, descriptive custom `User-Agent`. | Disk cache in `.geo-cache/nominatim/`. Rate limiter enforces 1 req/sec globally. |
| **China POI / Compounds** | 360 Maps REST API<br>`https://restapi.map.so.com/newapi` | None (Anonymous) | **PASS** (HTTP 200) | Public map search API. | Cached in `.geo-cache/poi_so/`. |
| **Global Elevation (DEM)** | AWS Open Data Terrain Tiles (Terrarium encoding)<br>`https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png` | None (Anonymous) | **PASS** (HTTP 200, 0.84s) | Open Data on AWS (Mapzen/SRTM/3DEP). ~30m global resolution. Free anonymous S3 access. | Cached per tile `(z, x, y)` in `.geo-cache/dem/`. |
| **Satellite Imagery (High Res)** | Google Satellite Tiles<br>`https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}` | None (Anonymous) | **PASS** (HTTP 200, 0.32s) | Public tile server. Used for visual confirmation and evidence overlay. | Disk cache in `.geo-cache/tiles/google/`. Low volume, bounded zoom levels. |
| **Satellite Imagery (Open WMTS)** | EOX Sentinel-2 Cloudless<br>`https://tiles.maps.eox.at/wmts/` | None (Anonymous) | **PASS** (HTTP 200, 1.19s) | CC BY 4.0. Keyless global cloudless Sentinel-2 composite. | Cached per tile in `.geo-cache/tiles/sentinel/`. |
| **Satellite Imagery (Coarse Earth)** | NASA GIBS (Global Imagery Browse Services)<br>`https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/` | None (Anonymous) | **PASS** (HTTP 200, 8.70s) | Open access (NASA Earth Science data). | Cached in `.geo-cache/tiles/nasa/`. |
| **Ground Photos / Geosearch** | Wikipedia & Wikimedia Geosearch<br>- Query: `https://en.wikipedia.org/w/api.php?action=query&list=geosearch`<br>- Thumbnails: `https://thumb.wikimedia.org/` | None (Anonymous) | **PASS** (HTTP 200, 0.5s) | CC BY-SA / Public Domain. Keyless Wikimedia API. | Cached in `.geo-cache/geophotos/`. |
| **Solar & Astronomical Math** | Local NOAA Meeus Solar Calculation Engine (`sun.py`) | None (Local computation) | **PASS** (Offline) | Public Domain / NOAA algorithm. Zero network calls. | N/A (Fully offline). |
| **Photogrammetry & Resection** | Local Levenberg-Marquardt Solver (`pose.py`, `geo.py`) | None (Local computation) | **PASS** (Offline) | Open source (Pure NumPy/SciPy math). Zero network calls. | N/A (Fully offline). |
| **Tabular Admin / Telecom Data** | Pinned local datasets in `vendor/geo-sleuth/skills/geo-sleuth/data/`<br>(License plates, area codes, calling codes, driving sides, overseas territories, admin hierarchy) | None (Local JSON) | **PASS** (All 6 tables validated) | Open data (Wikipedia compilations). | Loaded directly from local JSON files. |

---

## Disallowed / Incompatible Sources & Replacements

| Source | Reason for Exclusion | Status | Replacement / Handling |
|---|---|---|---|
| **Google Street View API** | Requires Google Cloud API key and billing. Forbidden by project brief. | **UNUSED** (`gsv.py` left vendored but disabled) | Use Wikipedia/Wikimedia geotagged ground photos and DEM skyline overlays. Where no ground coverage exists, report "not available". |
| **Baidu Panoramas API** | Proprietary Baidu API. Gated/restricted endpoints. | **UNUSED** (`baidu_pano.py` left vendored but disabled) | Replaced with open geometry and DEM horizon matching. |
| **KartaView (`api.openstreetcam.org`)** | Probe returned HTTP 400 with `"Restricted access!"`. Anonymous access is blocked. | **DISABLED** | Use Wikipedia/Wikimedia geotagged photos; report "not available" when coverage is absent. |
| **Mapillary API** | Requires OAuth2 client token and registered account. Forbidden by brief. | **DISABLED** | Use open geotagged photos and satellite imagery. |
| **Web Reverse Image Search (`revimg.py`)** | Uploads user photos to Baidu/Yandex third-party engines. Violates user privacy rules. | **DISABLED** | Image features are matched locally using open CLIP/DINOv2 embeddings and local OCR. |
| **Gated Hugging Face Models** | Models requiring user login tokens or agreements. | **EXCLUDED** | Only ungated open repos used (e.g. `openai/clip-vit-base-patch32`, `facebook/dinov2-small`). |

---

## Client Request Etiquette & Resilience Rules

1. **User-Agent:** All outgoing HTTP requests include an explicit descriptive header:
   `User-Agent: GlobalPhotoGeolocator/1.0 (Open-Source Research; contact: local-deploy)`
2. **Rate Limiting:**
   - Overpass queries are serialized with a minimum 1.5s delay between requests.
   - Nominatim requests are rate-limited to <= 1 request per second.
3. **Timeouts & Retries:** Every request has an explicit socket timeout (15–30s) and exponential backoff retry logic (up to 3 attempts).
4. **Offline Mode:** The application supports an `--offline` configuration flag that skips all remote network lookups and relies entirely on cached tiles, local rasters, and offline computation.
