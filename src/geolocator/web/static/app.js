/**
 * Global Photo Geolocator - Frontend Application
 * Keyless, Local Inference, SSE Live Streaming & Leaflet Visualization
 */

(function () {
  'use strict';

  // --- State Variables ---
  let selectedFile = null;
  let activeJobId = null;
  let eventSource = null;
  let map = null;
  let mapLayers = null;

  // --- DOM Elements ---
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const previewContainer = document.getElementById('preview-container');
  const previewImg = document.getElementById('preview-img');
  const removeBtn = document.getElementById('remove-btn');
  const hintInput = document.getElementById('hint-input');
  const passphraseInput = document.getElementById('passphrase-input');
  const passphraseGroup = document.getElementById('passphrase-group');
  const locateBtn = document.getElementById('locate-btn');
  const cancelBtn = document.getElementById('cancel-btn');

  const progressCard = document.getElementById('progress-card');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const progressPct = document.getElementById('progress-pct');
  const progressStepLabel = document.getElementById('progress-step-label');
  const pipelineStatusTitle = document.getElementById('pipeline-status-title');
  const timelineList = document.getElementById('timeline-list');

  const resultsCard = document.getElementById('results-card');
  const resultLocation = document.getElementById('result-location');
  const tierBadge = document.getElementById('tier-badge');
  const statLat = document.getElementById('stat-lat');
  const statLon = document.getElementById('stat-lon');
  const statRadius = document.getElementById('stat-radius');
  const statHeading = document.getElementById('stat-heading');
  const resultRationale = document.getElementById('result-rationale');
  const copyCoordsBtn = document.getElementById('copy-coords-btn');
  const openReportHtmlBtn = document.getElementById('open-report-html-btn');
  const downloadJsonBtn = document.getElementById('download-json-btn');
  const downloadGeojsonBtn = document.getElementById('download-geojson-btn');
  const mapBadgeText = document.getElementById('map-badge-text');

  const systemStatusDot = document.getElementById('system-status-dot');
  const systemStatusText = document.getElementById('system-status-text');
  const gpuInfo = document.getElementById('gpu-info');

  // Overview Evidence elements
  const badgeOsm = document.getElementById('badge-osm');
  const descOsm = document.getElementById('desc-osm');
  const thumbOsm = document.getElementById('thumb-container-osm');

  const badgeDem = document.getElementById('badge-dem');
  const descDem = document.getElementById('desc-dem');
  const thumbDem = document.getElementById('thumb-container-dem');

  const badgeSat = document.getElementById('badge-sat');
  const descSat = document.getElementById('desc-sat');
  const thumbSat = document.getElementById('thumb-container-sat');

  const badgeStreet = document.getElementById('badge-street');
  const descStreet = document.getElementById('desc-street');
  const thumbStreet = document.getElementById('thumb-container-street');

  // Detail Panel elements
  const detailBadgeOsm = document.getElementById('detail-badge-osm');
  const detailFindingsOsm = document.getElementById('detail-findings-osm');
  const detailCrossingsOsm = document.getElementById('detail-crossings-osm');
  const detailScoreOsm = document.getElementById('detail-score-osm');
  const btnOsmFocusMap = document.getElementById('btn-osm-focus-map');
  const btnOsmOpenExternal = document.getElementById('btn-osm-open-external');

  const detailBadgeDem = document.getElementById('detail-badge-dem');
  const detailFindingsDem = document.getElementById('detail-findings-dem');
  const detailDemImg = document.getElementById('detail-dem-img');
  const detailDemEmptyNote = document.getElementById('detail-dem-empty-note');
  const detailScoreDem = document.getElementById('detail-score-dem');
  const detailStatusDem = document.getElementById('detail-status-dem');
  const btnDemLightbox = document.getElementById('btn-dem-lightbox');
  const btnDemFocusMap = document.getElementById('btn-dem-focus-map');

  const detailBadgeSat = document.getElementById('detail-badge-sat');
  const detailFindingsSat = document.getElementById('detail-findings-sat');
  const detailSatImg = document.getElementById('detail-sat-img');
  const detailSatEmptyNote = document.getElementById('detail-sat-empty-note');
  const detailScoreSat = document.getElementById('detail-score-sat');
  const btnSatSwitchMap = document.getElementById('btn-sat-switch-map');
  const btnSatLightbox = document.getElementById('btn-sat-lightbox');

  const detailBadgeStreet = document.getElementById('detail-badge-street');
  const detailFindingsStreet = document.getElementById('detail-findings-street');
  const detailStreetImg = document.getElementById('detail-street-img');
  const detailStreetEmptyNote = document.getElementById('detail-street-empty-note');
  const btnStreetSearchWikimedia = document.getElementById('btn-street-search-wikimedia');

  // Lightbox elements
  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxBackdrop = document.getElementById('lightbox-backdrop');
  const lightboxClose = document.getElementById('lightbox-close');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxTitle = document.getElementById('lightbox-title');
  const lightboxDesc = document.getElementById('lightbox-desc');
  const lightboxDownloadBtn = document.getElementById('lightbox-download-btn');

  let currentReportData = null;
  let baseLayers = {};

  // --- Initialize Map ---
  function initMap() {
    map = L.map('map', {
      center: [20.0, 0.0],
      zoom: 2,
      zoomControl: true,
      attributionControl: true
    });

    // 100% keyless basemap layers with zero watermarks
    const esriDark = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri, HERE, Garmin, OpenStreetMap contributors',
      maxZoom: 16
    });

    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri, Maxar, Earthstar Geographics, CNES/Airbus, USGS',
      maxZoom: 19
    });

    const osmStandard = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    });

    // Default to clean, unwatermarked Esri Dark Gray canvas
    esriDark.addTo(map);

    // Layer switcher for easy user toggling
    baseLayers = {
      'Dark Canvas': esriDark,
      'Satellite': satellite,
      'OpenStreetMap': osmStandard
    };
    L.control.layers(baseMaps = baseLayers, null, { position: 'bottomleft' }).addTo(map);

    mapLayers = L.layerGroup().addTo(map);
  }

  function switchBasemap(name) {
    if (!map || !baseLayers[name]) return;
    Object.values(baseLayers).forEach(layer => {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    });
    baseLayers[name].addTo(map);
  }

  // --- Auth Helpers ---
  function getPassphrase() {
    return passphraseInput.value.trim() || localStorage.getItem('geo_passphrase') || '';
  }

  function getHeaders() {
    const headers = {};
    const pass = getPassphrase();
    if (pass) {
      headers['X-Passphrase'] = pass;
    }
    return headers;
  }

  function appendPassphraseParam(url) {
    const pass = getPassphrase();
    if (!pass) return url;
    const delim = url.includes('?') ? '&' : '?';
    return `${url}${delim}passphrase=${encodeURIComponent(pass)}`;
  }

  // --- Health Check ---
  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        systemStatusDot.style.backgroundColor = '#10b981';
        systemStatusDot.style.boxShadow = '0 0 8px #10b981';
        systemStatusText.textContent = data.offline_mode ? 'System Ready (Offline)' : 'System Ready (Live)';
        gpuInfo.textContent = data.gpu_device ? `GPU: ${data.gpu_device}` : 'Local GPU';

        if (!data.passphrase_required) {
          passphraseGroup.style.display = 'none';
        }
      }
    } catch (e) {
      systemStatusDot.style.backgroundColor = '#ef4444';
      systemStatusDot.style.boxShadow = '0 0 8px #ef4444';
      systemStatusText.textContent = 'Backend Offline';
    }
  }

  // --- File Dropzone Handlers ---
  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file (JPEG, PNG, WebP).');
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewContainer.style.display = 'block';
      dropzone.style.display = 'none';
      locateBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  removeBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    previewImg.src = '';
    previewContainer.style.display = 'none';
    dropzone.style.display = 'block';
    locateBtn.disabled = true;
  });

  // --- Passphrase Persistence ---
  passphraseInput.addEventListener('input', () => {
    localStorage.setItem('geo_passphrase', passphraseInput.value.trim());
  });
  if (localStorage.getItem('geo_passphrase')) {
    passphraseInput.value = localStorage.getItem('geo_passphrase');
  }

  // --- Add Timeline Item ---
  function addTimelineItem(msg, status = 'info') {
    const item = document.createElement('div');
    item.className = 'timeline-item';
    const time = new Date().toLocaleTimeString();
    
    let color = 'var(--accent-blue)';
    if (status === 'error') color = 'var(--accent-red)';
    if (status === 'complete') color = 'var(--accent-emerald)';
    if (status === 'warning') color = 'var(--accent-amber)';

    item.style.borderLeftColor = color;
    item.innerHTML = `
      <div style="flex: 1;">
        <div style="font-weight: 500;">${msg}</div>
        <div style="font-size: 0.7rem; color: var(--text-muted);">${time}</div>
      </div>
    `;
    timelineList.appendChild(item);
    timelineList.scrollTop = timelineList.scrollHeight;
  }

  // --- Submit Geolocation Job ---
  locateBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    locateBtn.disabled = true;
    progressCard.style.display = 'block';
    resultsCard.style.display = 'none';
    timelineList.innerHTML = '';
    progressBarFill.style.width = '2%';
    progressPct.textContent = '2%';
    progressStepLabel.textContent = 'Submitting photo to pipeline...';
    pipelineStatusTitle.textContent = 'Pipeline Running';

    const formData = new FormData();
    formData.append('photo', selectedFile);
    const hints = hintInput.value.trim();
    if (hints) {
      formData.append('hints', hints);
    }

    try {
      const res = await fetch('/api/jobs', {
        method: 'POST',
        headers: getHeaders(),
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to submit job' }));
        throw new Error(err.detail || 'HTTP ' + res.status);
      }

      const data = await res.json();
      activeJobId = data.job_id;
      addTimelineItem(`Job ${activeJobId} enqueued in GPU worker queue.`);
      connectSSE(activeJobId);
    } catch (err) {
      addTimelineItem(`Submission error: ${err.message}`, 'error');
      progressStepLabel.textContent = 'Error: ' + err.message;
      locateBtn.disabled = false;
    }
  });

  // --- Cancel Job ---
  cancelBtn.addEventListener('click', async () => {
    if (!activeJobId) return;
    try {
      await fetch(`/api/jobs/${activeJobId}/cancel`, {
        method: 'POST',
        headers: getHeaders()
      });
      addTimelineItem('Cancel request sent.', 'warning');
    } catch (e) {
      console.error('Cancel failed', e);
    }
  });

  // --- SSE Event Stream ---
  function connectSSE(jobId) {
    if (eventSource) {
      eventSource.close();
    }

    const sseUrl = appendPassphraseParam(`/api/jobs/${jobId}/events`);
    eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        handleJobEvent(event);
      } catch (err) {
        console.error('Invalid SSE payload', err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('SSE connection interrupted, checking job status via REST polling...', err);
      // Fallback REST status check
      checkJobStatusPoll(jobId);
    };
  }

  async function checkJobStatusPoll(jobId) {
    try {
      const res = await fetch(`/api/jobs/${jobId}`, { headers: getHeaders() });
      if (res.ok) {
        const job = await res.json();
        if (job.status === 'complete' || job.status === 'failed' || job.status === 'cancelled') {
          if (eventSource) eventSource.close();
          handleJobEvent({
            status: job.status,
            pct: job.progress_pct,
            step: job.current_step,
            message: `Job ${job.status}`
          });
        }
      }
    } catch (e) {
      console.error('Polling error', e);
    }
  }

  // --- Handle Timeline Events ---
  function handleJobEvent(event) {
    if (event.pct !== undefined) {
      progressBarFill.style.width = `${event.pct}%`;
      progressPct.textContent = `${event.pct}%`;
    }

    if (event.step) {
      progressStepLabel.textContent = event.step;
    }

    if (event.message) {
      addTimelineItem(event.message, event.status === 'complete' ? 'complete' : 'info');
    }

    if (event.status === 'complete') {
      if (eventSource) eventSource.close();
      pipelineStatusTitle.textContent = 'Geolocation Finished';
      progressBarFill.style.width = '100%';
      progressPct.textContent = '100%';
      locateBtn.disabled = false;
      loadFinalResults(activeJobId);
    } else if (event.status === 'failed' || event.status === 'cancelled') {
      if (eventSource) eventSource.close();
      pipelineStatusTitle.textContent = `Job ${event.status}`;
      locateBtn.disabled = false;
      addTimelineItem(`Pipeline stopped with status: ${event.status}`, 'error');
    }
  }

  // --- Load Final Report and Populate UI ---
  async function loadFinalResults(jobId) {
    try {
      const res = await fetch(`/api/jobs/${jobId}/report`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Report not found');
      const report = await res.json();

      displayReport(report, jobId);
    } catch (err) {
      addTimelineItem(`Could not load report: ${err.message}`, 'error');
    }
  }

  function displayReport(report, jobId) {
    currentReportData = report;
    resultsCard.style.display = 'block';

    const top = report.top_hypothesis || {};
    const coords = top.coordinates || {};
    const lat = coords.latitude !== undefined ? coords.latitude : null;
    const lon = coords.longitude !== undefined ? coords.longitude : null;
    const tier = top.confidence_tier || 'T6';
    const radiusM = top.error_radius_m || 500000;
    const heading = top.heading_deg !== undefined ? top.heading_deg : null;

    // Location name
    resultLocation.textContent = report.location_name || (lat !== null ? `${lat.toFixed(5)}, ${lon.toFixed(5)}` : 'Unknown Region');

    // Tier badge color
    tierBadge.textContent = `Tier ${tier}`;
    const tierColors = {
      'T1': '#10b981', // green
      'T2': '#3b82f6', // blue
      'T3': '#8b5cf6', // purple
      'T4': '#f59e0b', // amber
      'T5': '#ef4444', // red
      'T6': '#64748b'  // gray
    };
    tierBadge.style.backgroundColor = tierColors[tier] || '#3b82f6';

    statLat.textContent = lat !== null ? lat.toFixed(5) : '--';
    statLon.textContent = lon !== null ? lon.toFixed(5) : '--';
    statRadius.textContent = radiusM < 1000 ? `±${radiusM.toFixed(0)} m` : `±${(radiusM / 1000).toFixed(1)} km`;
    statHeading.textContent = heading !== null ? `${heading.toFixed(0)}°` : 'N/A';

    resultRationale.textContent = top.rationale || report.summary || 'Reasoning completed with multimodal evidence.';

    // Setup action bar links
    openReportHtmlBtn.href = appendPassphraseParam(`/api/jobs/${jobId}/report.html`);
    downloadJsonBtn.href = appendPassphraseParam(`/api/jobs/${jobId}/report`);
    downloadGeojsonBtn.href = appendPassphraseParam(`/api/jobs/${jobId}/report.geojson`);

    copyCoordsBtn.onclick = () => {
      if (lat !== null && lon !== null) {
        navigator.clipboard.writeText(`${lat.toFixed(6)}, ${lon.toFixed(6)}`);
        copyCoordsBtn.textContent = '✅ Copied!';
        setTimeout(() => copyCoordsBtn.textContent = '📋 Copy Coords', 2000);
      }
    };

    // Render Map
    if (lat !== null && lon !== null) {
      renderMapSolution(lat, lon, radiusM, heading, tier, report.alternatives);
    }

    // Populate 4 Evidence Cards
    populateEvidenceCards(report.evidence, jobId);
  }

  function renderMapSolution(lat, lon, radiusM, heading, tier, alternatives) {
    mapLayers.clearLayers();

    // 1. Error Circle
    const circle = L.circle([lat, lon], {
      radius: radiusM,
      color: '#3b82f6',
      fillColor: '#3b82f6',
      fillOpacity: 0.18,
      weight: 2
    }).addTo(mapLayers);

    // 2. Custom pulsing pin marker for top solution
    const pinHtml = `
      <div style="
        width: 18px;
        height: 18px;
        background: #3b82f6;
        border: 3px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.9);
      "></div>
    `;
    const pinIcon = L.divIcon({
      html: pinHtml,
      className: 'camera-pin',
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });

    const marker = L.marker([lat, lon], { icon: pinIcon }).addTo(mapLayers);
    marker.bindPopup(`<b>Estimated Position</b><br>Lat: ${lat.toFixed(5)}<br>Lon: ${lon.toFixed(5)}<br>Tier: ${tier}<br>Radius: ±${(radiusM/1000).toFixed(1)} km`);

    // 3. Camera Heading Ray if available
    if (heading !== null && heading !== undefined) {
      const rayLengthKm = Math.min(Math.max(radiusM / 1000, 2.0), 30.0);
      const rad = heading * (Math.PI / 180.0);
      const dLat = (rayLengthKm / 111.0) * Math.cos(rad);
      const dLon = (rayLengthKm / (111.0 * Math.cos(lat * Math.PI / 180.0))) * Math.sin(rad);
      const endLat = lat + dLat;
      const endLon = lon + dLon;

      const rayLine = L.polyline([[lat, lon], [endLat, endLon]], {
        color: '#10b981',
        weight: 3,
        dashArray: '6, 6'
      }).addTo(mapLayers);
      rayLine.bindPopup(`Camera Heading: ${heading.toFixed(0)}°`);
    }

    // 4. Alternative hypotheses markers
    if (Array.isArray(alternatives)) {
      alternatives.slice(0, 5).forEach((alt, idx) => {
        if (alt.coordinates && alt.coordinates.latitude !== undefined) {
          const altLat = alt.coordinates.latitude;
          const altLon = alt.coordinates.longitude;
          const altMarker = L.circleMarker([altLat, altLon], {
            radius: 6,
            color: '#94a3b8',
            fillColor: '#64748b',
            fillOpacity: 0.6,
            weight: 1
          }).addTo(mapLayers);
          altMarker.bindPopup(`<b>Alternative #${idx + 1}</b><br>Score: ${alt.score ? alt.score.toFixed(2) : 'N/A'}`);
        }
      });
    }

    // Fit map bounds
    map.fitBounds(circle.getBounds(), { padding: [40, 40], maxZoom: 16 });
    mapBadgeText.textContent = `${tier} • ±${(radiusM / 1000).toFixed(1)} km`;
  }

  function populateEvidenceCards(evidence = {}, jobId) {
    const report = currentReportData || {};
    const top = report.top_hypothesis || {};
    const coords = top.coordinates || {};
    const lat = coords.latitude !== undefined ? coords.latitude : null;
    const lon = coords.longitude !== undefined ? coords.longitude : null;

    // --- 1. Populate Overview Grid Cards ---
    applyEvidence(
      badgeOsm,
      descOsm,
      thumbOsm,
      evidence.osm_geometry,
      'OSM geometry corridor analysis complete.'
    );

    applyEvidence(
      badgeDem,
      descDem,
      thumbDem,
      evidence.elevation_skyline,
      'DEM skyline horizon profile matched against Terrarium elevation.',
      jobId,
      'skyline_overlay.png'
    );

    applyEvidence(
      badgeSat,
      descSat,
      thumbSat,
      evidence.satellite_imagery,
      'Overhead satellite footprint matched with optical features.',
      jobId,
      'satellite_evidence.png'
    );

    applyEvidence(
      badgeStreet,
      descStreet,
      thumbStreet,
      evidence.street_imagery,
      'Ground-level imagery checked via open repositories.'
    );

    // --- 2. Populate Dedicated Tab 1: OSM Geometry ---
    const osm = evidence.osm_geometry || {};
    applyBadge(detailBadgeOsm, osm.status);
    detailFindingsOsm.textContent = osm.findings || 'Linear corridor & infrastructure matching evaluated via Overpass API.';
    detailCrossingsOsm.textContent = osm.findings && osm.findings.includes('crossings') ? osm.findings.split('(')[1].split(' ')[0] : (osm.status === 'used' ? 'Verified Corridors' : '0 crossings');
    detailScoreOsm.textContent = osm.status === 'used' ? 'Verified Corridor Pattern' : (osm.status === 'not_applicable' ? 'Not Applicable (0 crossings)' : 'Evaluation completed');
    if (lat !== null && lon !== null) {
      btnOsmOpenExternal.href = `https://www.openstreetmap.org/#map=16/${lat.toFixed(5)}/${lon.toFixed(5)}`;
    }

    // --- 3. Populate Dedicated Tab 2: Elevation Skyline ---
    const dem = evidence.elevation_skyline || {};
    applyBadge(detailBadgeDem, dem.status);
    detailFindingsDem.textContent = dem.findings || 'Terrarium DEM horizon profile correlated with photo ridgeline curvature.';
    detailStatusDem.textContent = dem.status === 'used' ? 'Horizon Profile Aligned' : 'Natural flat / urban terrain (not used)';
    const demArtifactUrl = appendPassphraseParam(`/api/jobs/${jobId}/artifacts/skyline_overlay.png`);
    detailDemImg.src = demArtifactUrl;
    detailDemImg.onload = () => {
      detailDemImg.style.display = 'block';
      detailDemEmptyNote.style.display = 'none';
    };
    detailDemImg.onerror = () => {
      detailDemImg.style.display = 'none';
      detailDemEmptyNote.style.display = 'block';
    };

    // --- 4. Populate Dedicated Tab 3: Satellite Imagery ---
    const sat = evidence.satellite_imagery || {};
    applyBadge(detailBadgeSat, sat.status);
    detailFindingsSat.textContent = sat.findings || 'High-resolution overhead satellite visual verification and spatial footprint matching.';
    detailScoreSat.textContent = sat.status === 'used' ? 'Tile Verified' : 'Standard Optical Resolution';
    const satArtifactUrl = appendPassphraseParam(`/api/jobs/${jobId}/artifacts/satellite_evidence.png`);
    detailSatImg.src = satArtifactUrl;
    detailSatImg.onload = () => {
      detailSatImg.style.display = 'block';
      detailSatEmptyNote.style.display = 'none';
    };
    detailSatImg.onerror = () => {
      detailSatImg.style.display = 'none';
      detailSatEmptyNote.style.display = 'block';
    };

    // --- 5. Populate Dedicated Tab 4: Street-Level Imagery ---
    const street = evidence.street_imagery || {};
    applyBadge(detailBadgeStreet, street.status);
    detailFindingsStreet.textContent = street.findings || 'Keyless ground-level imagery check (Wikimedia Commons / KartaView). Honest "not available" when unmapped.';
    if (lat !== null && lon !== null) {
      btnStreetSearchWikimedia.href = `https://commons.wikimedia.org/w/index.php?search=${encodeURIComponent(lat.toFixed(4) + ' ' + lon.toFixed(4))}`;
    }
  }

  function applyBadge(el, status) {
    if (!el) return;
    const st = (status || 'not_applicable').toLowerCase();
    if (st === 'used') {
      el.className = 'badge-tag tag-used';
      el.textContent = 'USED';
    } else if (st === 'not_available' || st === 'unavailable') {
      el.className = 'badge-tag tag-not-available';
      el.textContent = 'NOT AVAILABLE';
    } else {
      el.className = 'badge-tag tag-not-applicable';
      el.textContent = 'NOT APPLICABLE';
    }
  }

  function applyEvidence(badgeEl, descEl, thumbEl, item, fallbackDesc, jobId = null, artifactName = null) {
    if (!item) {
      badgeEl.className = 'badge-tag tag-not-applicable';
      badgeEl.textContent = 'Not Checked';
      descEl.textContent = fallbackDesc;
      if (thumbEl) thumbEl.style.display = 'none';
      return;
    }

    applyBadge(badgeEl, item.status);
    descEl.textContent = item.findings || item.reason || fallbackDesc;

    const st = (item.status || 'not_applicable').toLowerCase();
    if (thumbEl && jobId && artifactName && (item.artifact_file || st === 'used')) {
      const artUrl = appendPassphraseParam(`/api/jobs/${jobId}/artifacts/${artifactName}`);
      thumbEl.innerHTML = `<img src="${artUrl}" class="evidence-thumb" alt="Evidence thumbnail" onerror="this.parentElement.style.display='none'">`;
      thumbEl.style.display = 'block';
      const img = thumbEl.querySelector('img');
      if (img) {
        img.addEventListener('click', (e) => {
          e.stopPropagation(); // prevent opening the tab
          openLightbox(artUrl, `${artifactName}`, descEl.textContent);
        });
      }
    } else if (thumbEl) {
      thumbEl.style.display = 'none';
    }
  }

  // --- Interactive Tabs Switching Logic ---
  function switchEvidenceTab(tabKey) {
    const tabButtons = document.querySelectorAll('.evidence-tab-btn');
    const tabPanels = document.querySelectorAll('.evidence-tab-panel');

    tabButtons.forEach(btn => {
      if (btn.getAttribute('data-tab') === tabKey) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    tabPanels.forEach(panel => {
      if (panel.id === `panel-${tabKey}`) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });
  }

  // Tab button click listeners
  document.querySelectorAll('.evidence-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabKey = btn.getAttribute('data-tab');
      if (tabKey) switchEvidenceTab(tabKey);
    });
  });

  // Overview card click listeners (open specific tab)
  document.querySelectorAll('.clickable-evidence-card').forEach(card => {
    card.addEventListener('click', () => {
      const target = card.getAttribute('data-target-tab');
      if (target) switchEvidenceTab(target);
    });
  });

  // Back button click listeners
  document.querySelectorAll('.tab-back-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchEvidenceTab('overview');
    });
  });

  // --- Lightbox Modal Logic ---
  function openLightbox(src, title = 'Evidence Preview', desc = '') {
    if (!src) return;
    lightboxImg.src = src;
    lightboxTitle.textContent = title;
    lightboxDesc.textContent = desc;
    lightboxDownloadBtn.href = src;
    lightboxModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightboxModal.style.display = 'none';
    lightboxImg.src = '';
    document.body.style.overflow = '';
  }

  lightboxClose.addEventListener('click', closeLightbox);
  lightboxBackdrop.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightboxModal.style.display !== 'none') {
      closeLightbox();
    }
  });

  // Target photo click opens in lightbox
  previewImg.addEventListener('click', () => {
    if (previewImg.src) {
      openLightbox(previewImg.src, 'Target Photo (Uploaded)', 'Input photo submitted for autonomous global geolocation');
    }
  });

  // Evidence tab action buttons
  detailDemImg.addEventListener('click', () => {
    if (detailDemImg.src && detailDemImg.style.display !== 'none') {
      openLightbox(detailDemImg.src, 'Pillar 2: Synthetic vs Photo Ridgeline Alignment', detailFindingsDem.textContent);
    }
  });

  btnDemLightbox.addEventListener('click', () => {
    if (detailDemImg.src && detailDemImg.style.display !== 'none') {
      openLightbox(detailDemImg.src, 'Pillar 2: Synthetic vs Photo Ridgeline Alignment', detailFindingsDem.textContent);
    }
  });

  detailSatImg.addEventListener('click', () => {
    if (detailSatImg.src && detailSatImg.style.display !== 'none') {
      openLightbox(detailSatImg.src, 'Pillar 3: High-Resolution Overhead Satellite Footprint', detailFindingsSat.textContent);
    }
  });

  btnSatLightbox.addEventListener('click', () => {
    if (detailSatImg.src && detailSatImg.style.display !== 'none') {
      openLightbox(detailSatImg.src, 'Pillar 3: High-Resolution Overhead Satellite Footprint', detailFindingsSat.textContent);
    }
  });

  btnSatSwitchMap.addEventListener('click', () => {
    switchBasemap('Satellite');
    const mapEl = document.getElementById('map');
    if (mapEl) mapEl.scrollIntoView({ behavior: 'smooth' });
  });

  btnOsmFocusMap.addEventListener('click', () => {
    if (currentReportData) {
      const top = currentReportData.top_hypothesis || {};
      const coords = top.coordinates || {};
      if (coords.latitude !== undefined && coords.longitude !== undefined) {
        map.setView([coords.latitude, coords.longitude], 16);
        const mapEl = document.getElementById('map');
        if (mapEl) mapEl.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  btnDemFocusMap.addEventListener('click', () => {
    if (currentReportData) {
      const top = currentReportData.top_hypothesis || {};
      const coords = top.coordinates || {};
      if (coords.latitude !== undefined && coords.longitude !== undefined) {
        map.setView([coords.latitude, coords.longitude], 14);
        const mapEl = document.getElementById('map');
        if (mapEl) mapEl.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  // --- Initial Launch ---
  window.addEventListener('DOMContentLoaded', () => {
    initMap();
    checkHealth();
  });
})();
