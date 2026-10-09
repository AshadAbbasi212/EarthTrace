"""Download StreetCLIP weights with resume support and progress logging."""
import os
import sys
import time
import urllib.request
from pathlib import Path

DEST_DIR = Path(r"C:\Users\David\.cache\huggingface\hub\models--geolocal--StreetCLIP\snapshots\e3561ba2ad9bf14c9efd6b0092607b8497efbfea")
DEST_FILE = DEST_DIR / "pytorch_model.bin"
URL = "https://huggingface.co/geolocal/StreetCLIP/resolve/main/pytorch_model.bin"
TEMP_FILE = DEST_DIR / "pytorch_model.bin.part"

DEST_DIR.mkdir(parents=True, exist_ok=True)

if DEST_FILE.exists() and DEST_FILE.stat().st_size > 1700000000:
    print(f"StreetCLIP already downloaded: {DEST_FILE} ({DEST_FILE.stat().st_size} bytes)")
    sys.exit(0)

existing_size = TEMP_FILE.stat().st_size if TEMP_FILE.exists() else 0

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
if existing_size > 0:
    req.add_header("Range", f"bytes={existing_size}-")
    print(f"Resuming download from byte {existing_size} ({existing_size / (1024*1024):.1f} MB)...")
else:
    print("Starting download of StreetCLIP weights (1.71 GB)...")

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        total_size = existing_size + int(resp.headers.get("Content-Length", 0))
        mode = "ab" if existing_size > 0 else "wb"
        downloaded = existing_size
        t0 = time.time()
        last_log = t0
        
        with open(TEMP_FILE, mode) as f:
            while True:
                chunk = resp.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_log >= 10.0:  # Log every 10 seconds
                    pct = (downloaded / total_size) * 100 if total_size > 0 else 0
                    speed = (downloaded - existing_size) / (1024 * 1024 * max(1, now - t0))
                    print(f"Progress: {downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB ({pct:.1f}%) at {speed:.2f} MB/s", flush=True)
                    last_log = now

    # Rename when complete
    if TEMP_FILE.exists() and TEMP_FILE.stat().st_size > 1700000000:
        if DEST_FILE.exists():
            DEST_FILE.unlink()
        TEMP_FILE.rename(DEST_FILE)
        print(f"StreetCLIP download complete! Saved to {DEST_FILE}", flush=True)
    else:
        print(f"Download finished with unexpected size: {TEMP_FILE.stat().st_size}", flush=True)

except Exception as e:
    print(f"Download error: {e}", flush=True)
    sys.exit(1)
