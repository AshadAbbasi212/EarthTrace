"""SQLite Job Store and 24-hour Retention Manager."""
from __future__ import annotations

import json
import logging
import sqlite3
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("geolocator.app.database")


class JobDatabase:
    """Manages SQLite job history and automated disk retention cleanup."""

    def __init__(self, db_path: str | Path = "data/jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    photo_filename TEXT,
                    photo_sha256 TEXT,
                    user_hint TEXT,
                    progress_pct INTEGER DEFAULT 0,
                    current_step TEXT DEFAULT 'Created',
                    error_message TEXT,
                    summary_json TEXT,
                    job_dir TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_job(
        self,
        job_id: str,
        photo_filename: str,
        job_dir: str | Path,
        user_hint: Optional[str] = None,
        photo_sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (id, created_at, updated_at, status, photo_filename, photo_sha256, user_hint, progress_pct, current_step, job_dir)
                VALUES (?, ?, ?, 'pending', ?, ?, ?, 0, 'Queued', ?)
            """, (job_id, now, now, photo_filename, photo_sha256, user_hint, str(job_dir)))
            conn.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cur.fetchone()
            if row is None:
                return None
            res = dict(row)
            if res.get("summary_json"):
                try:
                    res["summary"] = json.loads(res["summary_json"])
                except Exception:
                    res["summary"] = None
            return res

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
            jobs = []
            for row in cur.fetchall():
                item = dict(row)
                if item.get("summary_json"):
                    try:
                        item["summary"] = json.loads(item["summary_json"])
                    except Exception:
                        item["summary"] = None
                jobs.append(item)
            return jobs

    def update_progress(self, job_id: str, status: str, step: str, pct: int, error: Optional[str] = None, summary: Optional[Dict[str, Any]] = None) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        summary_str = json.dumps(summary) if summary else None
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs 
                SET status = ?, current_step = ?, progress_pct = ?, error_message = ?, summary_json = COALESCE(?, summary_json), updated_at = ?
                WHERE id = ?
            """, (status, step, pct, error, summary_str, now, job_id))
            conn.commit()

    def cancel_job(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,))
            row = cur.fetchone()
            if not row:
                return False
            status = row["status"]
            if status in ("complete", "failed", "cancelled"):
                return False
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("UPDATE jobs SET status = 'cancelled', updated_at = ? WHERE id = ?", (now, job_id))
            conn.commit()
            return True

    def delete_expired_jobs(self, retention_hours: int = 24) -> int:
        """Purge jobs and disk artifacts older than retention_hours."""
        cutoff = (datetime.utcnow() - timedelta(hours=retention_hours)).isoformat() + "Z"
        deleted_count = 0
        with self._get_connection() as conn:
            cur = conn.execute("SELECT id, job_dir FROM jobs WHERE created_at < ?", (cutoff,))
            expired = cur.fetchall()
            for row in expired:
                j_id = row["id"]
                j_dir = Path(row["job_dir"])
                if j_dir.exists():
                    try:
                        shutil.rmtree(j_dir, ignore_errors=True)
                    except Exception as e:
                        logger.warning("Failed to delete expired job dir %s: %s", j_dir, e)
                conn.execute("DELETE FROM jobs WHERE id = ?", (j_id,))
                deleted_count += 1
            conn.commit()
        if deleted_count > 0:
            logger.info("Purged %d expired jobs older than %d hours", deleted_count, retention_hours)
        return deleted_count

    def clear_all_jobs(self, jobs_dir: str | Path = "jobs") -> int:
        """Purge all jobs from database and delete all job directories."""
        deleted_count = 0
        with self._get_connection() as conn:
            cur = conn.execute("SELECT id, job_dir FROM jobs")
            rows = cur.fetchall()
            for row in rows:
                j_dir = Path(row["job_dir"])
                if j_dir.exists():
                    try:
                        shutil.rmtree(j_dir, ignore_errors=True)
                    except Exception as e:
                        logger.warning("Failed to delete job dir %s: %s", j_dir, e)
                deleted_count += 1
            conn.execute("DELETE FROM jobs")
            conn.commit()

        # Clean any leftover or untracked directories in jobs_dir
        j_base = Path(jobs_dir)
        if j_base.exists():
            for item in j_base.iterdir():
                if item.is_dir():
                    try:
                        shutil.rmtree(item, ignore_errors=True)
                    except Exception as e:
                        logger.warning("Failed to remove directory %s: %s", item, e)
                elif item.is_file() and item.name != ".gitkeep":
                    try:
                        item.unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning("Failed to remove file %s: %s", item, e)

        logger.info("Purged all jobs (%d records) and cleared jobs directory", deleted_count)
        return deleted_count

