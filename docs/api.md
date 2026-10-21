# EarthTrace REST API Reference

EarthTrace provides a local asynchronous REST API powered by FastAPI on port 8080.

## Base URL
```
http://127.0.0.1:8080
```

---

## Endpoints

### 1. Submit Image for Geolocation
`POST /api/jobs`

Submits an image to the pipeline.

**Request:** `multipart/form-data`
- `file`: Image file (`.jpg`, `.png`, `.webp`, `.heic`, `.tiff`)
- `hint`: (Optional) Free-text context or constraints (e.g., `"mountains in central asia"`, `"southern hemisphere"`)

**Response:** `200 OK`
```json
{
  "job_id": "job_20261020_143022_a1b2c3",
  "status": "pending",
  "created_at": "2026-10-20T14:30:22.000Z"
}
```

---

### 2. Check Job Status
`GET /api/jobs/{id}`

Returns current processing progress, pipeline stage, and execution state.

**Response:** `200 OK`
```json
{
  "job_id": "job_20261020_143022_a1b2c3",
  "status": "completed",
  "progress": 1.0,
  "stage": "Stage 5: Decision Engine",
  "error": null
}
```

---

### 3. Real-Time Event Stream (SSE)
`GET /api/jobs/{id}/events`

Server-Sent Events (SSE) channel streaming stage transitions and log outputs in real time.

---

### 4. Retrieve Machine-Readable Decision Report
`GET /api/jobs/{id}/report`

Returns the full JSON decision report containing predicted coordinates, confidence tier, calibrated uncertainty radius, and cited evidence artifacts.

**Response:** `200 OK`
```json
{
  "job_id": "job_20261020_143022_a1b2c3",
  "prediction": {
    "lat": 35.6895,
    "lon": 139.6917,
    "confidence_tier": "T3",
    "uncertainty_radius_km": 15.0,
    "place_name": "Tokyo Metropolis, Japan"
  },
  "evidence": {
    "osm_geometry": "used",
    "elevation_skyline": "not applicable",
    "satellite_imagery": "used",
    "street_imagery": "used",
    "building_facade": "used"
  }
}
```

---

### 5. Export Standalone Formats
- `GET /api/jobs/{id}/report.html`: Self-contained interactive HTML forensic report.
- `GET /api/jobs/{id}/report.geojson`: GIS-compatible GeoJSON FeatureCollection with point coordinates, polygon bounding box, and heading vector.
- `GET /api/jobs/{id}/artifacts/{filename}`: Raw visual debug artifacts (e.g., `skyline_overlay.png`, `satellite_evidence.png`).
