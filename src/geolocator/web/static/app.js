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
  let allHypotheses = [];
  let currentHypothesisIndex = 0;

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
    L.control.layers(baseLayers, null, { position: 'bottomleft' }).addTo(map);

    mapLayers = L.layerGroup().addTo(map);
  }

  function ensureMap() {
    if (!map) {
      initMap();
    }
    if (map && !mapLayers) {
      mapLayers = L.layerGroup().addTo(map);
    }
    return map && mapLayers;
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

  // --- Tactical Co-Pilot Terrain Pill Toggles ---
  document.querySelectorAll('.copilot-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('.copilot-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
    });
  });

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

    const copilotExclude = document.getElementById('copilot-exclude');
    if (copilotExclude && copilotExclude.value.trim()) {
      formData.append('excluded_countries', copilotExclude.value.trim());
    }

    const activePill = document.querySelector('.copilot-pill.active');
    if (activePill && activePill.dataset.terrain) {
      formData.append('terrain_filter', activePill.dataset.terrain);
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

  // Global hook for popup clicks
  window.__selectHypothesis = function(idx) {
    renderHypothesis(idx);
  };

  function displayReport(report, jobId) {
    currentReportData = report;
    resultsCard.style.display = 'block';

    // 1. Compile all hypotheses list: T1 (Top), T2, T3...
    allHypotheses = [];
    const top = report.top_hypothesis || report.best_location || {};
    let topLat = null;
    let topLon = null;
    if (top.coordinates) {
      if (Array.isArray(top.coordinates) && top.coordinates.length >= 2) {
        topLat = Number(top.coordinates[0]);
        topLon = Number(top.coordinates[1]);
      } else if (top.coordinates.latitude !== undefined) {
        topLat = Number(top.coordinates.latitude);
        topLon = Number(top.coordinates.longitude);
      }
    } else if (report.best_location && Array.isArray(report.best_location.coordinates)) {
      topLat = Number(report.best_location.coordinates[0]);
      topLon = Number(report.best_location.coordinates[1]);
    }

    const topTier = top.confidence_tier || (report.best_location && report.best_location.confidence_tier) || 'T6';
    const topRadiusM = top.error_radius_m || 
      (top.calibrated_radius_km ? top.calibrated_radius_km * 1000 : null) || 
      (report.best_location && report.best_location.calibrated_radius_km ? report.best_location.calibrated_radius_km * 1000 : null) || 
      500000;
    const topHeading = top.heading_deg !== undefined ? top.heading_deg : 
      (top.camera_heading_deg !== undefined ? top.camera_heading_deg : 
      (report.best_location && report.best_location.camera_heading_deg !== undefined ? report.best_location.camera_heading_deg : null));

    if (topLat !== null && topLon !== null && !isNaN(topLat) && !isNaN(topLon)) {
      allHypotheses.push({
        rank: 1,
        rankLabel: 'T1',
        isTop: true,
        name: report.location_name || top.name || `${topLat.toFixed(5)}, ${topLon.toFixed(5)}`,
        lat: topLat,
        lon: topLon,
        tier: topTier,
        radiusM: topRadiusM,
        heading: topHeading,
        rationale: top.rationale || report.summary || 'Top determined location from multimodal pipeline.',
        isExactMark: (topTier === 'T1' && topRadiusM <= 150),
        score: (report.best_location && report.best_location.score) !== undefined ? report.best_location.score : (top.score || 10.0)
      });
    }

    // Process alternatives: T2, T3, T4...
    const alternatives = report.top_alternatives || report.alternatives || [];
    if (Array.isArray(alternatives)) {
      alternatives.forEach((alt) => {
        let altLat = null;
        let altLon = null;
        if (Array.isArray(alt.coordinates) && alt.coordinates.length >= 2) {
          altLat = Number(alt.coordinates[0]);
          altLon = Number(alt.coordinates[1]);
        } else if (alt.coordinates && alt.coordinates.latitude !== undefined) {
          altLat = Number(alt.coordinates.latitude);
          altLon = Number(alt.coordinates.longitude);
        } else if (alt.lat !== undefined && alt.lon !== undefined) {
          altLat = Number(alt.lat);
          altLon = Number(alt.lon);
        }

        if (altLat !== null && altLon !== null && !isNaN(altLat) && !isNaN(altLon)) {
          // Avoid duplicate coordinates of existing hypotheses
          const isDup = allHypotheses.some(h => Math.abs(h.lat - altLat) < 0.0001 && Math.abs(h.lon - altLon) < 0.0001);
          if (!isDup) {
            const altRank = allHypotheses.length + 1;
            const altLabel = `T${altRank}`;
            const altTier = alt.confidence_tier || (alt.score && alt.score > 3.0 ? 'T2' : (alt.score && alt.score > 0 ? 'T3' : 'T4'));
            const altRadM = alt.error_radius_m || (alt.calibrated_radius_km ? alt.calibrated_radius_km * 1000 : (altTier === 'T2' ? 3000 : (altTier === 'T3' ? 15000 : 45000)));
            const altHeading = alt.heading_deg !== undefined ? alt.heading_deg : null;

            allHypotheses.push({
              rank: altRank,
              rankLabel: altLabel,
              isTop: false,
              name: alt.name || `Alternative ${altLabel}`,
              lat: altLat,
              lon: altLon,
              tier: altTier,
              radiusM: altRadM,
              heading: altHeading,
              rationale: alt.rationale || `Alternative candidate ${altLabel}: ${alt.name || 'Candidate'} (Score: ${alt.score !== undefined ? alt.score.toFixed(2) : 'N/A'})`,
              isExactMark: (altTier === 'T1' && altRadM <= 150),
              score: alt.score !== undefined ? alt.score : 0.0
            });
          }
        }
      });
    }

    // Setup action bar download / export links
    openReportHtmlBtn.href = appendPassphraseParam(`/api/jobs/${jobId}/report.html`);
    downloadJsonBtn.href = appendPassphraseParam(`/api/jobs/${jobId}/report`);
    downloadGeojsonBtn.href = appendPassphraseParam(`/api/jobs/${jobId}/report.geojson`);

    copyCoordsBtn.onclick = () => {
      const activeHypo = allHypotheses[currentHypothesisIndex];
      if (activeHypo) {
        navigator.clipboard.writeText(`${activeHypo.lat.toFixed(6)}, ${activeHypo.lon.toFixed(6)}`);
        copyCoordsBtn.textContent = '✅ Copied!';
        setTimeout(() => copyCoordsBtn.textContent = '📋 Copy Coords', 2000);
      }
    };

    // Attach click listener so clicking the location title cycles T1 -> T2 -> T3
    resultLocation.onclick = () => {
      if (allHypotheses.length > 1) {
        const nextIdx = (currentHypothesisIndex + 1) % allHypotheses.length;
        renderHypothesis(nextIdx);
      }
    };

    const cycleHint = document.getElementById('location-cycle-hint');
    if (cycleHint) {
      cycleHint.onclick = (e) => {
        e.stopPropagation();
        if (allHypotheses.length > 1) {
          const nextIdx = (currentHypothesisIndex + 1) % allHypotheses.length;
          renderHypothesis(nextIdx);
        }
      };
    }

    // Render initial hypothesis: T1
    currentHypothesisIndex = 0;
    renderHypothesis(0);

    // Populate 4 Evidence Cards
    try {
      populateEvidenceCards(report.evidence || {}, jobId);
    } catch (err) {
      console.error('Failed to populate evidence cards:', err);
    }
  }

  function renderHypothesis(index) {
    if (!allHypotheses || allHypotheses.length === 0) return;
    currentHypothesisIndex = ((index % allHypotheses.length) + allHypotheses.length) % allHypotheses.length;
    const hypo = allHypotheses[currentHypothesisIndex];

    // Location name with explicit rank badge (T1, T2, T3)
    resultLocation.innerHTML = '';
    const rankBadge = document.createElement('span');
    rankBadge.className = `location-rank-badge ${hypo.rankLabel.toLowerCase()}`;
    rankBadge.textContent = hypo.rankLabel;
    const nameSpan = document.createElement('span');
    nameSpan.className = 'location-name-text';
    nameSpan.textContent = hypo.name;
    resultLocation.appendChild(rankBadge);
    resultLocation.appendChild(nameSpan);

    resultLocation.title = allHypotheses.length > 1 
      ? `Viewing ${hypo.rankLabel}. Click location to view ${allHypotheses[(currentHypothesisIndex + 1) % allHypotheses.length].rankLabel} (${currentHypothesisIndex + 1}/${allHypotheses.length})` 
      : hypo.name;

    // Cycle hint text
    const cycleHint = document.getElementById('location-cycle-hint');
    if (cycleHint) {
      if (allHypotheses.length > 1) {
        const nextIdx = (currentHypothesisIndex + 1) % allHypotheses.length;
        const nextLabel = allHypotheses[nextIdx].rankLabel;
        cycleHint.style.display = 'inline-flex';
        cycleHint.innerHTML = `<span class="cycle-icon">↻</span> Viewing <b>${hypo.rankLabel}</b> • Click location to view <b>${nextLabel}</b> (${currentHypothesisIndex + 1}/${allHypotheses.length})`;
      } else {
        cycleHint.style.display = 'none';
      }
    }

    // Tier badge color & text
    tierBadge.textContent = `Tier ${hypo.tier}`;
    const tierColors = {
      'T1': '#10b981', // green
      'T2': '#3b82f6', // blue
      'T3': '#8b5cf6', // purple
      'T4': '#f59e0b', // amber
      'T5': '#ef4444', // red
      'T6': '#64748b'  // gray
    };
    tierBadge.style.backgroundColor = tierColors[hypo.tier] || '#3b82f6';

    // Statistics readout
    statLat.textContent = hypo.lat.toFixed(5);
    statLon.textContent = hypo.lon.toFixed(5);
    statRadius.textContent = hypo.radiusM < 1000 ? `±${hypo.radiusM.toFixed(0)} m` : `±${(hypo.radiusM / 1000).toFixed(1)} km`;
    statHeading.textContent = (hypo.heading !== null && !isNaN(hypo.heading)) ? `${hypo.heading.toFixed(0)}°` : 'N/A';
    resultRationale.textContent = hypo.rationale;

    // Exact Mark HUD
    const exactMarkHud = document.getElementById('exact-mark-hud');
    const exactMetricPrec = document.getElementById('exact-metric-precision');
    if (exactMarkHud) {
      if (hypo.isExactMark) {
        exactMarkHud.style.display = 'flex';
        if (exactMetricPrec) {
          exactMetricPrec.textContent = `PRECISION: ±${Math.round(hypo.radiusM)}m (EXACT MARK)`;
        }
      } else {
        exactMarkHud.style.display = 'none';
      }
    }

    // Update 3D Tactical Globe Target
    setGlobeTarget(hypo.lat, hypo.lon);
    const latStr = `${Math.abs(hypo.lat).toFixed(2)}°${hypo.lat >= 0 ? 'N' : 'S'}`;
    const lonStr = `${Math.abs(hypo.lon).toFixed(2)}°${hypo.lon >= 0 ? 'E' : 'W'}`;
    const globeCoordsEl = document.getElementById('header-globe-coords');
    if (globeCoordsEl) globeCoordsEl.textContent = `${latStr}, ${lonStr}`;

    // Update Hypothesis Switcher Pills
    const selectorEl = document.getElementById('hypothesis-selector');
    if (selectorEl) {
      if (allHypotheses.length > 1) {
        selectorEl.style.display = 'flex';
        selectorEl.innerHTML = '';
        allHypotheses.forEach((h, i) => {
          const pill = document.createElement('button');
          pill.type = 'button';
          pill.className = `hypo-pill ${i === currentHypothesisIndex ? 'active' : ''}`;
          pill.innerHTML = `<span>${i === 0 ? '🎯' : '📍'}</span> ${h.rankLabel} <span style="opacity:0.75;font-size:0.68rem;">(${h.tier})</span>`;
          pill.title = `${h.rankLabel}: ${h.name} • Click to inspect`;
          pill.onclick = (e) => {
            e.stopPropagation();
            renderHypothesis(i);
          };
          selectorEl.appendChild(pill);
        });
      } else {
        selectorEl.style.display = 'none';
      }
    }

    // Render Map with selected active marker and little gray marks for alternatives
    try {
      renderMapSolution(currentHypothesisIndex);
    } catch (err) {
      console.error('Failed to render map solution:', err);
    }
  }

  function renderMapSolution(selectedIndex) {
    ensureMap();
    if (!mapLayers || !map || !allHypotheses || allHypotheses.length === 0) return;
    mapLayers.clearLayers();

    const activeHypo = allHypotheses[selectedIndex];
    const isExactMark = activeHypo.isExactMark;
    const lat = activeHypo.lat;
    const lon = activeHypo.lon;
    const radiusM = activeHypo.radiusM;
    const heading = activeHypo.heading;
    const tier = activeHypo.tier;

    // 1. Error Circle & Concentric Tactical Rings for Active Hypothesis
    let activeCircle = null;
    if (isExactMark) {
      activeCircle = L.circle([lat, lon], {
        radius: radiusM,
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.15,
        weight: 2,
        dashArray: '4, 4'
      }).addTo(mapLayers);

      L.circle([lat, lon], {
        radius: Math.max(15, radiusM * 0.5),
        color: '#00f0ff',
        fillColor: '#00f0ff',
        fillOpacity: 0.25,
        weight: 1.5
      }).addTo(mapLayers);
    } else {
      activeCircle = L.circle([lat, lon], {
        radius: radiusM,
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.18,
        weight: 2
      }).addTo(mapLayers);
    }

    // 2. Active Pulsing Pin or Tactical Reticle Marker
    let pinHtml = '';
    let iconSize = [18, 18];
    let iconAnchor = [9, 9];

    if (isExactMark) {
      pinHtml = `<div class="tactical-reticle-ping"></div>`;
      iconSize = [28, 28];
      iconAnchor = [14, 14];
    } else {
      pinHtml = `
        <div style="
          width: 18px;
          height: 18px;
          background: #3b82f6;
          border: 3px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 12px rgba(59, 130, 246, 0.95);
        "></div>
      `;
    }

    const pinIcon = L.divIcon({
      html: pinHtml,
      className: 'camera-pin',
      iconSize: iconSize,
      iconAnchor: iconAnchor
    });

    const activeMarker = L.marker([lat, lon], { icon: pinIcon, zIndexOffset: 1000 }).addTo(mapLayers);
    let popupContentHtml = isExactMark 
      ? `<b>🎯 EXACT MARK PINPOINT (${activeHypo.rankLabel})</b><br>${activeHypo.name}<br>Lat: ${lat.toFixed(6)}<br>Lon: ${lon.toFixed(6)}<br>Precision: ±${Math.round(radiusM)} m`
      : `<b>${activeHypo.rankLabel}: ${activeHypo.name}</b><br>Lat: ${lat.toFixed(5)}<br>Lon: ${lon.toFixed(5)}<br>Tier: ${tier}<br>Radius: ±${(radiusM/1000).toFixed(1)} km`;
    
    if (allHypotheses.length > 1) {
      const nextIdx = (selectedIndex + 1) % allHypotheses.length;
      const nextLabel = allHypotheses[nextIdx].rankLabel;
      popupContentHtml += `<div style="margin-top: 8px;"><button type="button" class="btn-secondary" style="width: 100%; padding: 4px 8px; font-size: 11px; justify-content: center; cursor: pointer;" onclick="window.__cycleNextHypothesis()">↻ Next Location (${nextLabel})</button></div>`;
    }
    activeMarker.bindPopup(popupContentHtml);

    // 3. Camera Heading Ray if available
    if (heading !== null && heading !== undefined && !isNaN(heading)) {
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

    // 4. Little Gray Marks on Map for all other alternative locations
    allHypotheses.forEach((h, idx) => {
      if (idx === selectedIndex) return; // Skip active hypothesis

      const grayIconHtml = `
        <div class="alt-little-gray-mark" title="${h.rankLabel}: ${h.name} (Click to switch to this location)">
          <span class="gray-mark-badge">${h.rankLabel}</span>
        </div>
      `;

      const grayIcon = L.divIcon({
        html: grayIconHtml,
        className: 'alt-gray-marker-icon',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });

      const grayMarker = L.marker([h.lat, h.lon], { icon: grayIcon, zIndexOffset: 500 }).addTo(mapLayers);

      // Tooltip on hover
      grayMarker.bindTooltip(`<b>${h.rankLabel}:</b> ${h.name} <span style="color:#94a3b8;font-size:10px;">(Click to view)</span>`, { direction: 'top', offset: [0, -10] });

      // Direct activation on click: switches immediately to this candidate!
      grayMarker.on('click', (e) => {
        if (e && e.originalEvent) {
          e.originalEvent.stopPropagation();
        }
        renderHypothesis(idx);
      });
    });

    // Zoom and center map smoothly
    if (isExactMark) {
      map.setView([lat, lon], 17, { animate: true });
    } else if (activeCircle) {
      map.fitBounds(activeCircle.getBounds(), { padding: [40, 40], maxZoom: 14 });
    } else {
      map.setView([lat, lon], 12, { animate: true });
    }

    mapBadgeText.textContent = `${activeHypo.rankLabel} • ${tier} • ±${(radiusM / 1000).toFixed(1)} km`;
  }

  // Global helpers for hypothesis cycling from map popups or buttons
  window.__cycleNextHypothesis = () => {
    if (allHypotheses && allHypotheses.length > 1) {
      const nextIdx = (currentHypothesisIndex + 1) % allHypotheses.length;
      renderHypothesis(nextIdx);
    }
  };

  window.__selectHypothesis = (idx) => {
    renderHypothesis(idx);
  };

  function populateEvidenceCards(evidence = {}, jobId) {
    const report = currentReportData || {};
    const top = report.top_hypothesis || report.best_location || {};
    let lat = null;
    let lon = null;
    if (top.coordinates) {
      if (Array.isArray(top.coordinates) && top.coordinates.length >= 2) {
        lat = Number(top.coordinates[0]);
        lon = Number(top.coordinates[1]);
      } else if (top.coordinates.latitude !== undefined) {
        lat = Number(top.coordinates.latitude);
        lon = Number(top.coordinates.longitude);
      }
    } else if (report.best_location && Array.isArray(report.best_location.coordinates)) {
      lat = Number(report.best_location.coordinates[0]);
      lon = Number(report.best_location.coordinates[1]);
    }

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
    
    let crossingDisplay = (osm.status === 'used' ? 'Verified Corridors' : '0 crossings');
    if (osm.findings) {
      const matchParen = osm.findings.match(/\((\d+)\s+crossing/i);
      const matchWord = osm.findings.match(/(\d+)\s+crossings?/i);
      if (matchParen) {
        crossingDisplay = `${matchParen[1]} crossings`;
      } else if (matchWord) {
        crossingDisplay = `${matchWord[1]} crossings`;
      }
    }
    detailCrossingsOsm.textContent = crossingDisplay;
    detailScoreOsm.textContent = osm.status === 'used' ? 'Verified Corridor Pattern' : (osm.status === 'not_applicable' ? 'Not Applicable (0 crossings)' : 'Evaluation completed');
    if (lat !== null && lon !== null && !isNaN(lat) && !isNaN(lon)) {
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
    if (lat !== null && lon !== null && !isNaN(lat) && !isNaN(lon)) {
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
      const top = currentReportData.top_hypothesis || currentReportData.best_location || {};
      let lat = null, lon = null;
      if (Array.isArray(top.coordinates) && top.coordinates.length >= 2) {
        lat = Number(top.coordinates[0]); lon = Number(top.coordinates[1]);
      } else if (top.coordinates && top.coordinates.latitude !== undefined) {
        lat = Number(top.coordinates.latitude); lon = Number(top.coordinates.longitude);
      }
      if (lat !== null && lon !== null && !isNaN(lat) && !isNaN(lon) && map) {
        map.setView([lat, lon], 16);
        const mapEl = document.getElementById('map');
        if (mapEl) mapEl.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  btnDemFocusMap.addEventListener('click', () => {
    if (currentReportData) {
      const top = currentReportData.top_hypothesis || currentReportData.best_location || {};
      let lat = null, lon = null;
      if (Array.isArray(top.coordinates) && top.coordinates.length >= 2) {
        lat = Number(top.coordinates[0]); lon = Number(top.coordinates[1]);
      } else if (top.coordinates && top.coordinates.latitude !== undefined) {
        lat = Number(top.coordinates.latitude); lon = Number(top.coordinates.longitude);
      }
      if (lat !== null && lon !== null && !isNaN(lat) && !isNaN(lon) && map) {
        map.setView([lat, lon], 14);
        const mapEl = document.getElementById('map');
        if (mapEl) mapEl.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  // --- 3D Tactical Particle Globe Engine ---
  let globeTargetLat = null;
  let globeTargetLon = null;
  let globeCurrentRotY = 0;
  let globeCurrentRotX = 0.2;

  function setGlobeTarget(lat, lon) {
    globeTargetLat = lat;
    globeTargetLon = lon;
  }

  function initGlobeCanvas() {
    const canvas = document.getElementById('header-globe-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const radius = width * 0.42;
    const cx = width / 2;
    const cy = height / 2;

    // Generate fixed 3D sphere points (parallels & meridians)
    const points = [];
    for (let lat = -60; lat <= 60; lat += 30) {
      const phi = (lat * Math.PI) / 180;
      const cosPhi = Math.cos(phi);
      const sinPhi = Math.sin(phi);
      for (let lon = 0; lon < 360; lon += 24) {
        const theta = (lon * Math.PI) / 180;
        points.push({
          x: radius * cosPhi * Math.cos(theta),
          y: radius * sinPhi,
          z: radius * cosPhi * Math.sin(theta)
        });
      }
    }

    function animateGlobe() {
      ctx.clearRect(0, 0, width, height);

      // Rotate continuously or smoothly steer toward target coordinates
      if (globeTargetLon !== null && globeTargetLat !== null) {
        const targetRotY = - (globeTargetLon * Math.PI) / 180 + Math.PI / 2;
        globeCurrentRotY += (targetRotY - globeCurrentRotY) * 0.05;
        const targetRotX = (globeTargetLat * Math.PI) / 180 * 0.4;
        globeCurrentRotX += (targetRotX - globeCurrentRotX) * 0.05;
      } else {
        globeCurrentRotY += 0.015;
      }

      const cosY = Math.cos(globeCurrentRotY);
      const sinY = Math.sin(globeCurrentRotY);
      const cosX = Math.cos(globeCurrentRotX);
      const sinX = Math.sin(globeCurrentRotX);

      // Outer atmosphere rim
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.25)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Render 3D points
      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        const x1 = p.x * cosY - p.z * sinY;
        const z1 = p.x * sinY + p.z * cosY;
        const y2 = p.y * cosX - z1 * sinX;
        const z2 = p.y * sinX + z1 * cosX;

        if (z2 > -12) {
          const depthAlpha = Math.max(0.15, (z2 + radius) / (2 * radius));
          const screenX = cx + x1;
          const screenY = cy - y2;

          ctx.fillStyle = `rgba(0, 240, 255, ${depthAlpha * 0.75})`;
          ctx.beginPath();
          ctx.arc(screenX, screenY, depthAlpha > 0.65 ? 1.2 : 0.8, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // If target locked, draw pulsing beacon reticle
      if (globeTargetLat !== null && globeTargetLon !== null) {
        const phi = (globeTargetLat * Math.PI) / 180;
        const theta = (globeTargetLon * Math.PI) / 180;
        const tx = radius * Math.cos(phi) * Math.cos(theta);
        const ty = radius * Math.sin(phi);
        const tz = radius * Math.cos(phi) * Math.sin(theta);

        const x1 = tx * cosY - tz * sinY;
        const z1 = tx * sinY + tz * cosY;
        const y2 = ty * cosX - z1 * sinX;
        const z2 = ty * sinX + z1 * cosX;

        if (z2 > 0) {
          const screenX = cx + x1;
          const screenY = cy - y2;
          ctx.beginPath();
          ctx.arc(screenX, screenY, 3, 0, Math.PI * 2);
          ctx.fillStyle = '#00f0ff';
          ctx.shadowColor = '#00f0ff';
          ctx.shadowBlur = 10;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }

      requestAnimationFrame(animateGlobe);
    }

    animateGlobe();
  }

  // --- 3D Card Hover Physics ---
  function initCardTilt3D() {
    const cards = document.querySelectorAll('.card-3d');
    cards.forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        const tiltX = (y - 0.5) * -10;
        const tiltY = (x - 0.5) * 10;
        card.style.transform = `perspective(1000px) rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg) translateY(-2px)`;
        card.style.setProperty('--mouse-x', `${(x * 100).toFixed(1)}%`);
        card.style.setProperty('--mouse-y', `${(y * 100).toFixed(1)}%`);
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
      });
    });
  }

  // --- Initial Launch ---
  window.addEventListener('DOMContentLoaded', () => {
    initMap();
    checkHealth();
    initGlobeCanvas();
    initCardTilt3D();
  });
})();

