"""Unit and integration tests for Backend API, Queue, SQLite, and Concurrency."""
import asyncio
import io
import json
import time
import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from geolocator.config import AppConfig
from geolocator.app.database import JobDatabase
from geolocator.app.queue import JobQueueManager
from geolocator.app.api import create_app


def test_sqlite_job_database_lifecycle_and_retention(tmp_path):
    db_file = tmp_path / "test_jobs.db"
    db = JobDatabase(db_path=db_file)

    job_dir = tmp_path / "job_001"
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "sample.txt").write_text("artifact", encoding="utf-8")

    # 1. Create job
    j = db.create_job(job_id="job_001", photo_filename="photo.jpg", job_dir=job_dir, user_hint="France")
    assert j["id"] == "job_001"
    assert j["status"] == "pending"

    # 2. Update progress
    db.update_progress("job_001", status="running", step="Stage 2", pct=40)
    j_up = db.get_job("job_001")
    assert j_up["status"] == "running"
    assert j_up["progress_pct"] == 40

    # 3. List jobs
    jobs = db.list_jobs()
    assert len(jobs) == 1

    # 4. Cancel
    cancelled = db.cancel_job("job_001")
    assert cancelled is True
    assert db.get_job("job_001")["status"] == "cancelled"

    # 5. Retention cleanup with retention_hours=0 (immediately expired)
    deleted = db.delete_expired_jobs(retention_hours=0)
    assert deleted == 1
    assert db.get_job("job_001") is None
    assert not job_dir.exists()


def test_fastapi_endpoints_and_passphrase(tmp_path):
    cfg = AppConfig()
    cfg.storage.jobs_dir = str(tmp_path / "jobs")
    cfg.storage.data_dir = str(tmp_path / "data")
    cfg.server.passphrase_enabled = True
    cfg.server.passphrase = "secret123"

    app = create_app(config=cfg)
    client = TestClient(app)

    # 1. Health check is public
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["passphrase_required"] is True

    # 2. Protected endpoint without passphrase -> 401
    res_unauth = client.get("/api/jobs")
    assert res_unauth.status_code == 401

    # 3. Protected endpoint with passphrase header -> 200
    res_auth = client.get("/api/jobs", headers={"X-Passphrase": "secret123"})
    assert res_auth.status_code == 200
    assert "jobs" in res_auth.json()

    # 4. Upload photo with passphrase
    img_bytes = io.BytesIO()
    Image.new("RGB", (100, 100), (120, 80, 50)).save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    upload_res = client.post(
        "/api/jobs",
        headers={"X-Passphrase": "secret123"},
        files={"photo": ("test.jpg", img_bytes.getvalue(), "image/jpeg")},
        data={"hints": "Near Lake Geneva"},
    )
    assert upload_res.status_code == 200
    j_id = upload_res.json()["job_id"]
    assert upload_res.json()["status"] == "pending"

    # 5. Query job status
    status_res = client.get(f"/api/jobs/{j_id}", headers={"X-Passphrase": "secret123"})
    assert status_res.status_code == 200
    assert status_res.json()["id"] == j_id

    # 6. Cancel job
    cancel_res = client.post(f"/api/jobs/{j_id}/cancel", headers={"X-Passphrase": "secret123"})
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_job_queue_concurrency_polite_queuing(tmp_path):
    """Concurrency test: second upload queues politely behind the first and executes sequentially."""
    db_file = tmp_path / "queue_test.db"
    db = JobDatabase(db_path=db_file)

    # Create mock orchestrator with observable execution order
    class MockOrchestrator:
        def __init__(self):
            self.execution_order = []

        def run(self, photo_path, job_dir, hint, progress_cb):
            job_name = Path(photo_path).stem
            self.execution_order.append(f"start_{job_name}")
            # Simulate pipeline running
            time.sleep(0.15)
            self.execution_order.append(f"finish_{job_name}")
            return {"best_location": {"name": f"Location of {job_name}"}}

    mock_orch = MockOrchestrator()
    qm = JobQueueManager(db=db, orchestrator=mock_orch)

    # Prepare 2 jobs
    p1 = tmp_path / "photo_alpha.jpg"
    p2 = tmp_path / "photo_beta.jpg"
    p1.touch()
    p2.touch()

    db.create_job("job_1", "photo_alpha.jpg", tmp_path / "j1")
    db.create_job("job_2", "photo_beta.jpg", tmp_path / "j2")

    # Enqueue both jobs rapidly
    await qm.enqueue("job_1", p1)
    await qm.enqueue("job_2", p2)

    # Wait for queue to process both
    max_wait = 2.0
    start_t = time.time()
    while time.time() - start_t < max_wait:
        j1 = db.get_job("job_1")
        j2 = db.get_job("job_2")
        if j1["status"] == "complete" and j2["status"] == "complete":
            break
        await asyncio.sleep(0.05)

    await qm.stop_worker()

    assert db.get_job("job_1")["status"] == "complete"
    assert db.get_job("job_2")["status"] == "complete"

    # Verify sequential execution: Job 1 finishes before Job 2 starts!
    expected_sequence = ["start_photo_alpha", "finish_photo_alpha", "start_photo_beta", "finish_photo_beta"]
    assert mock_orch.execution_order == expected_sequence, f"Expected sequential execution, got {mock_orch.execution_order}"
