# Contributing to EarthTrace

Thank you for your interest in contributing to EarthTrace!

## Code of Conduct & Responsible Use
EarthTrace is built strictly for defensive research, humanitarian relief, environmental monitoring, open-source journalism, and academic study. Contributions designed to facilitate unauthorized surveillance, doxing, or stalking will be rejected.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AshadAbbasi212/EarthTrace.git
   cd EarthTrace
   ```

2. **Set up virtual environment & install dependencies:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e ".[dev]"
   ```

3. **Run the test suite:**
   ```powershell
   pytest tests/ -v
   ```

## Code Guidelines
- **Zero API Keys Rule:** Do not add requirements for paid cloud APIs, tokens, or subscription keys.
- **Local Neural Inference:** Machine learning models must run on local consumer GPUs/CPUs.
- **Calibration & Honesty:** Never report artificial point precision when evidence only supports regional bounds. Always assign a calibrated confidence tier (T1–T6).
- **Vendored Code:** Do not modify `vendor/geo-sleuth/` in place. Use adapter wrappers in `src/geolocator/adapters/`.
