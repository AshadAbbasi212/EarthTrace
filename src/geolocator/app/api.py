"""FastAPI Application providing REST endpoints, SSE timeline streaming, and passphrase authentication."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from geolocator.config import AppConfig, get_config
from geolocator.app.database import JobDatabase
from geolocator.app.queue import JobQueueManager

logger = logging.getLogger("geolocator.app.api")


def create_app(config: Optional[AppConfig] = None) -> FastAPI:
    cfg = config or get_config()
    db_path = getattr(cfg, "storage", None) and (Path(cfg.storage.data_dir) / "jobs.db") or "data/jobs.db"
    db = JobDatabase(db_path=db_path)
    queue_mgr = JobQueueManager(db=db)

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        queue_mgr.start_worker()
        if cfg.storage.auto_delete_expired:
            db.delete_expired_jobs(retention_hours=cfg.storage.retention_hours)
        yield
        await queue_mgr.stop_worker()

    app = FastAPI(
        title="Self-Hosted Global Photo Geolocator",
        description="Autonomous keyless photo geolocation API with local models and open data",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.config = cfg
    app.state.db = db
    app.state.queue = queue_mgr

    # Optional Passphrase Protection
    async def verify_passphrase(
        request: Request,
        x_passphrase: Optional[str] = Header(None, alias="X-Passphrase"),
        passphrase_param: Optional[str] = Query(None, alias="passphrase"),
    ):
        if cfg.server.passphrase_enabled and cfg.server.passphrase:
            token = x_passphrase or passphrase_param or request.cookies.get("passphrase")
            if token != cfg.server.passphrase:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing passphrase")
        return True

    # -------------------------------------------------------------
    # API Endpoints
    # -------------------------------------------------------------

    @app.get("/health")
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "offline_mode": cfg.offline_mode,
            "gpu_device": cfg.hardware.device,
            "passphrase_required": cfg.server.passphrase_enabled,
        }

    @app.post("/api/jobs", dependencies=[Depends(verify_passphrase)])
    async def submit_job(
        photo: UploadFile = File(...),
        hints: Optional[str] = Form(None),
        excluded_countries: Optional[str] = Form(None),
        terrain_filter: Optional[str] = Form(None),
        api_key: Optional[str] = Form(None),
    ):
        """Upload photo and optional user hints/co-pilot constraints, enqueueing job for processing."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        jobs_dir = Path(cfg.storage.jobs_dir) / job_id
        jobs_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded photo to job directory
        filename = photo.filename or "input.jpg"
        photo_path = jobs_dir / filename
        content = await photo.read()

        if len(content) > 30 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Photo file size exceeds 30 MB limit")

        photo_path.write_bytes(content)

        # Compose co-pilot hint string
        hint_parts = []
        if hints and hints.strip():
            hint_parts.append(hints.strip())
        if excluded_countries and excluded_countries.strip():
            for ec in excluded_countries.split(","):
                ec_clean = ec.strip()
                if ec_clean:
                    hint_parts.append(f"exclude {ec_clean}")
        if terrain_filter and terrain_filter.strip():
            hint_parts.append(terrain_filter.strip())
        combined_hints = " ".join(hint_parts) if hint_parts else None

        # Create record in DB
        db.create_job(
            job_id=job_id,
            photo_filename=filename,
            job_dir=jobs_dir,
            user_hint=combined_hints,
        )

        # Enqueue for sequential processing
        await queue_mgr.enqueue(
            job_id=job_id,
            photo_path=photo_path,
            user_hint=combined_hints,
            api_key=api_key,
        )

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Job queued successfully",
        }

    @app.get("/api/jobs", dependencies=[Depends(verify_passphrase)])
    async def list_jobs(limit: int = 50):
        """List recent jobs."""
        return {"jobs": db.list_jobs(limit=limit)}

    @app.get("/api/jobs/{job_id}", dependencies=[Depends(verify_passphrase)])
    async def get_job_status(job_id: str):
        """Get job execution status and progress."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    @app.post("/api/jobs/{job_id}/cancel", dependencies=[Depends(verify_passphrase)])
    @app.delete("/api/jobs/{job_id}", dependencies=[Depends(verify_passphrase)])
    async def cancel_job(job_id: str):
        """Cancel a pending or running job."""
        cancelled = db.cancel_job(job_id)
        if not cancelled:
            job = db.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            return {"job_id": job_id, "status": job["status"], "message": "Job already concluded"}
        return {"job_id": job_id, "status": "cancelled", "message": "Job cancelled"}

    @app.get("/api/jobs/{job_id}/events", dependencies=[Depends(verify_passphrase)])
    async def stream_job_events(job_id: str):
        """Server-Sent Events (SSE) live timeline stream for job progress."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        async def event_generator():
            # Send initial state
            initial_event = {
                "status": job["status"],
                "step": job["current_step"],
                "pct": job["progress_pct"],
            }
            yield f"data: {json.dumps(initial_event)}\n\n"

            if job["status"] in ("complete", "failed", "cancelled"):
                return

            sub_queue = queue_mgr.subscribe(job_id)
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(sub_queue.get(), timeout=30.0)
                        yield f"data: {json.dumps(event)}\n\n"
                        if event.get("status") in ("complete", "failed", "cancelled"):
                            break
                    except asyncio.TimeoutError:
                        # Keep-alive heartbeat
                        yield ": keepalive\n\n"
            finally:
                queue_mgr.unsubscribe(job_id, sub_queue)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/api/jobs/{job_id}/report", dependencies=[Depends(verify_passphrase)])
    async def get_report_json(job_id: str):
        """Retrieve full machine-readable report.json."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        report_file = Path(job["job_dir"]) / "report.json"
        if not report_file.exists():
            raise HTTPException(status_code=404, detail="Report not generated yet")
        return json.loads(report_file.read_text(encoding="utf-8"))

    @app.get("/api/jobs/{job_id}/report.html", dependencies=[Depends(verify_passphrase)])
    async def get_report_html(job_id: str):
        """Retrieve standalone styled report.html."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        html_file = Path(job["job_dir"]) / "report.html"
        if not html_file.exists():
            raise HTTPException(status_code=404, detail="HTML report not generated yet")
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

    @app.get("/api/jobs/{job_id}/report.geojson", dependencies=[Depends(verify_passphrase)])
    async def get_report_geojson(job_id: str):
        """Retrieve map-ready report.geojson."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        geojson_file = Path(job["job_dir"]) / "report.geojson"
        if not geojson_file.exists():
            raise HTTPException(status_code=404, detail="GeoJSON report not generated yet")
        return JSONResponse(content=json.loads(geojson_file.read_text(encoding="utf-8")))

    @app.get("/api/jobs/{job_id}/artifacts/{filename:path}", dependencies=[Depends(verify_passphrase)])
    async def get_artifact(job_id: str, filename: str):
        """Serve specific evidence artifact image or JSON file."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        artifact_path = (Path(job["job_dir"]) / filename).resolve()
        # Security: prevent path traversal outside job directory
        if not str(artifact_path).startswith(str(Path(job["job_dir"]).resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        if not artifact_path.exists():
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(str(artifact_path))

    @app.post("/api/maintenance/cleanup", dependencies=[Depends(verify_passphrase)])
    async def trigger_cleanup():
        """Manually trigger retention cleanup."""
        deleted = db.delete_expired_jobs(retention_hours=cfg.storage.retention_hours)
        return {"deleted_jobs_count": deleted}

    # Static Web UI mounting if available
    web_dir = Path(__file__).resolve().parent.parent / "web" / "static"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")

    return app


# Default ASGI application instance
app = create_app()
