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


def test_alternative_hypotheses_and_map_marks(client):
    """Verify frontend assets include hypothesis switcher and map gray marks."""
    # HTML contains cycle hint, clickable location title, and hypothesis selector
    html_res = client.get("/")
    assert html_res.status_code == 200
    assert 'id="location-cycle-hint"' in html_res.text
    assert 'clickable-location-title' in html_res.text
    assert 'id="hypothesis-selector"' in html_res.text

    # CSS contains styles for gray marks and hypothesis pills
    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    assert ".alt-little-gray-mark" in css_res.text
    assert ".hypo-pill" in css_res.text
    assert ".location-rank-badge" in css_res.text

    # JS contains hypothesis cycling and gray marks logic
    js_res = client.get("/app.js")
    assert js_res.status_code == 200
    assert "renderHypothesis" in js_res.text
    assert "alt-little-gray-mark" in js_res.text
    assert "__cycleNextHypothesis" in js_res.text
    assert "allHypotheses" in js_res.text


def test_five_pillars_tab_sliding_and_building_panel(client):
    """Verify 5th evidence pillar tab, independent #panel-bldg, and smooth horizontal sliding."""
    html_res = client.get("/")
    assert html_res.status_code == 200
    html = html_res.text

    # 5 Pillars tab buttons exist
    assert 'id="tab-btn-bldg"' in html
    assert "5. Building Match" in html
    assert "5 Pillars" in html
    assert 'id="panel-bldg"' in html

    # Crucial layout guarantee: #panel-bldg must be an independent sibling, NOT nested inside #panel-street
    street_panel_start = html.find('id="panel-street"')
    assert street_panel_start != -1
    bldg_panel_start = html.find('id="panel-bldg"')
    assert bldg_panel_start != -1
    assert bldg_panel_start > street_panel_start

    # Confirm there is a closing </div> between panel-street and panel-bldg
    intermediate_html = html[street_panel_start:bldg_panel_start]
    assert "</div>" in intermediate_html

    # CSS sliding animations & horizontal bar scrolling
    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    css = css_res.text
    assert "overflow-x: auto" in css
    assert "scroll-behavior: smooth" in css
    assert "tabSlideIn" in css

    # JS sliding interaction
    js_res = client.get("/app.js")
    assert js_res.status_code == 200
    js = js_res.text
    assert "scrollIntoView" in js
    assert "detailBadgeBldg" in js
    assert "detailFindingsBldg" in js


