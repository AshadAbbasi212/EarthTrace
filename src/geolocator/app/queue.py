"""Sequential Job Queue Worker with live SSE streaming."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from geolocator.app.database import JobDatabase
from geolocator.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger("geolocator.app.queue")


class JobQueueManager:
    """Sequential queue manager ensuring single-job concurrency and live SSE event broadcasting."""

    def __init__(self, db: JobDatabase, orchestrator: Optional[PipelineOrchestrator] = None):
        self.db = db
        self.orchestrator = orchestrator or PipelineOrchestrator()
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.subscribers: Dict[str, List[asyncio.Queue[Dict[str, Any]]]] = {}
        self.running_job_id: Optional[str] = None
        self._stopped = False

    def start_worker(self) -> None:
        if self.worker_task is None or self.worker_task.done():
            self._stopped = False
            self.worker_task = asyncio.create_task(self._process_queue())
            logger.info("JobQueueManager background worker started.")

    async def stop_worker(self) -> None:
        self._stopped = True
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            self.worker_task = None

    async def enqueue(self, job_id: str, photo_path: Path, user_hint: Optional[str] = None) -> None:
        """Add job to sequential queue."""
        await self.queue.put({
            "job_id": job_id,
            "photo_path": photo_path,
            "user_hint": user_hint,
        })
        self.start_worker()

    def subscribe(self, job_id: str) -> asyncio.Queue[Dict[str, Any]]:
        """Subscribe to live SSE event updates for job_id."""
        sub_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        if job_id not in self.subscribers:
            self.subscribers[job_id] = []
        self.subscribers[job_id].append(sub_queue)
        return sub_queue

    def unsubscribe(self, job_id: str, sub_queue: asyncio.Queue[Dict[str, Any]]) -> None:
        if job_id in self.subscribers and sub_queue in self.subscribers[job_id]:
            self.subscribers[job_id].remove(sub_queue)
            if not self.subscribers[job_id]:
                del self.subscribers[job_id]

    async def broadcast(self, job_id: str, event_data: Dict[str, Any]) -> None:
        """Send event to all active SSE subscribers of job_id."""
        if job_id in self.subscribers:
            for q in list(self.subscribers[job_id]):
                try:
                    await q.put(event_data)
                except Exception:
                    pass

    async def _process_queue(self) -> None:
        while not self._stopped:
            try:
                item = await self.queue.get()
            except asyncio.CancelledError:
                break

            job_id = item["job_id"]
            photo_path = item["photo_path"]
            user_hint = item["user_hint"]

            # Check if job was cancelled while waiting in queue
            job_rec = self.db.get_job(job_id)
            if job_rec and job_rec["status"] == "cancelled":
                logger.info("Job %s was cancelled before execution. Skipping.", job_id)
                self.queue.task_done()
                continue

            self.running_job_id = job_id
            self.db.update_progress(job_id, status="running", step="Starting Pipeline", pct=5)
            await self.broadcast(job_id, {"status": "running", "step": "Starting Pipeline", "pct": 5})

            loop = asyncio.get_running_loop()

            def progress_hook(step_name: str, pct: int):
                self.db.update_progress(job_id, status="running", step=step_name, pct=pct)
                # Dispatch async broadcast to event loop
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(job_id, {"status": "running", "step": step_name, "pct": pct}),
                    loop,
                )

            try:
                job_dir = Path(job_rec["job_dir"]) if job_rec else photo_path.parent
                # Run synchronous pipeline in thread pool to keep asyncio event loop responsive
                report_data = await loop.run_in_executor(
                    None,
                    self.orchestrator.run,
                    photo_path,
                    job_dir,
                    user_hint,
                    progress_hook,
                )

                self.db.update_progress(
                    job_id,
                    status="complete",
                    step="Completed",
                    pct=100,
                    summary=report_data.get("best_location"),
                )
                await self.broadcast(job_id, {
                    "status": "complete",
                    "step": "Completed",
                    "pct": 100,
                    "report": report_data,
                })
                logger.info("Job %s completed successfully.", job_id)
            except Exception as e:
                logger.error("Job %s failed with error: %s", job_id, e, exc_info=True)
                self.db.update_progress(job_id, status="failed", step="Error", pct=100, error=str(e))
                await self.broadcast(job_id, {
                    "status": "failed",
                    "step": "Error",
                    "pct": 100,
                    "error": str(e),
                })
            finally:
                self.running_job_id = None
                self.queue.task_done()
