"""Test suite for Milestone 9 Web UI: Static assets, Index HTML, Offline Leaflet, and API mounting."""
import pytest
from fastapi.testclient import TestClient

from geolocator.config import AppConfig, ServerConfig, StorageConfig, HardwareConfig
from geolocator.app.api import create_app


@pytest.fixture
def client(tmp_path):
    test_db = tmp_path / "test_web.db"
    test_jobs = tmp_path / "test_jobs"
    test_jobs.mkdir()

    config = AppConfig(
        server=ServerConfig(port=8000, passphrase_enabled=False),
        storage=StorageConfig(jobs_dir=str(test_jobs), data_dir=str(tmp_path)),
        hardware=HardwareConfig(device="cpu"),
    )
    app = create_app(config=config)
    with TestClient(app) as test_client:
        yield test_client


def test_index_html_served(client):
    """Verify root / serves index.html with dark theme UI, cards, and Responsible Use notice."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    # Title & Branding
    assert "Global Photo Geolocator" in html
    assert "GLOBAL PHOTO GEOLOCATOR" in html

    # Mandatory Responsible Use Notice
    assert "Responsible Use Notice" in html
    assert "Do not use this system to locate or track non-consenting individuals" in html

    # Core UI Elements
    assert 'id="dropzone"' in html
    assert 'id="map"' in html
    assert 'id="progress-card"' in html
    assert 'id="results-card"' in html

    # All 4 Mandatory Evidence Pillars
    assert "OSM Geometry" in html
    assert "Elevation Skyline" in html
    assert "Satellite Imagery" in html
    assert "Street Imagery" in html


def test_static_assets_and_vendor_leaflet(client):
    """Verify local offline static files (CSS, JS, Leaflet vendor bundle) are served with HTTP 200."""
    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    assert "Modern Ultra-Premium Dark Theme" in css_res.text or "var(--bg-primary)" in css_res.text

    js_res = client.get("/app.js")
    assert js_res.status_code == 200
    assert "Global Photo Geolocator - Frontend Application" in js_res.text

    leaflet_css = client.get("/vendor/leaflet/leaflet.css")
    assert leaflet_css.status_code == 200
    assert "leaflet" in leaflet_css.text.lower()

    leaflet_js = client.get("/vendor/leaflet/leaflet.js")
    assert leaflet_js.status_code == 200
    assert len(leaflet_js.content) > 50000  # Full bundled Leaflet library

    layers_png = client.get("/vendor/leaflet/images/layers.png")
    assert layers_png.status_code == 200
    assert len(layers_png.content) > 0

    layers_2x_png = client.get("/vendor/leaflet/images/layers-2x.png")
    assert layers_2x_png.status_code == 200
    assert len(layers_2x_png.content) > 0


def test_health_api(client):
    """Verify /api/health endpoint functions seamlessly alongside web UI."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["gpu_device"] == "cpu"
    assert data["passphrase_required"] is False
