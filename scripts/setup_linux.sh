#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "  EarthTrace — Linux / macOS Automated Setup"
echo "============================================================"

# Check Python version
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed. Please install Python 3.11 or 3.12."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python: ${PY_VER}"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"

echo "Checking GPU / CPU device configuration..."
python3 scripts/check_gpu.py || true

echo "Pre-caching neural network weights..."
python3 scripts/download_weights.py || true

echo "============================================================"
echo "  Setup Complete! Start EarthTrace with:"
echo "    source .venv/bin/activate"
echo "    uvicorn geolocator.app.api:app --host 127.0.0.1 --port 8080"
echo "============================================================"
