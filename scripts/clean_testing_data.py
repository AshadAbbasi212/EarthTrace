"""Utility script to clean all previous testing data, job outputs, and reset SQLite database."""
import shutil
import sqlite3
from pathlib import Path

def clean_data():
    workspace = Path(__file__).resolve().parent.parent

    # 1. Clean jobs/ directory
    jobs_dir = workspace / "jobs"
    if jobs_dir.exists():
        print(f"Cleaning {jobs_dir}...")
        for item in jobs_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                print(f"  Deleted job folder: {item.name}")
            elif item.is_file():
                item.unlink(missing_ok=True)
                print(f"  Deleted file: {item.name}")
    jobs_dir.mkdir(parents=True, exist_ok=True)
    print("[OK] jobs/ directory is now completely clean and empty.")

    # 2. Reset SQLite database data/jobs.db
    db_file = workspace / "data" / "jobs.db"
    if db_file.exists():
        db_file.unlink(missing_ok=True)
        print("[OK] data/jobs.db removed.")
    
    # Re-initialize clean SQLite schema
    conn = sqlite3.connect(str(db_file))
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
    conn.close()
    print("[OK] data/jobs.db re-initialized with fresh empty schema.")

    # 3. Clean eval/results/ if present
    eval_results = workspace / "eval" / "results"
    if eval_results.exists():
        print(f"Cleaning {eval_results}...")
        for item in eval_results.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                print(f"  Deleted eval result: {item.name}")
            elif item.is_file():
                item.unlink(missing_ok=True)
                print(f"  Deleted eval file: {item.name}")
        eval_results.mkdir(parents=True, exist_ok=True)
        print("[OK] eval/results/ is now completely clean.")

    print("\nAll previous testing data has been wiped clean. Ready to test from scratch!")

if __name__ == "__main__":
    clean_data()
