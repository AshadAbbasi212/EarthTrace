# EarthTrace: Local AI Geospatial Intelligence & Photo Geolocator
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TRANSFORMERS_OFFLINE=0

WORKDIR /app

# Install system dependencies for OpenCV and geographic processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging specifications
COPY pyproject.toml requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application source and configurations
COPY src/ /app/src/
COPY data/ /app/data/
COPY config.yaml /app/config.yaml

EXPOSE 8080

CMD ["uvicorn", "geolocator.app.api:app", "--host", "0.0.0.0", "--port", "8080"]
