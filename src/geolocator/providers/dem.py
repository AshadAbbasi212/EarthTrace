"""Global elevation provider using Terrarium DEM tiles on open cloud storage."""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.dem")

# Terrarium URL pattern
TERRARIUM_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
R_EARTH = 6371008.8
K_REFRACTION = 0.13  # Standard terrestrial refraction coefficient


class DEMProvider(BaseProvider):
    """Provides keyless digital elevation models and skyline extraction worldwide."""

    def __init__(
        self,
        tile_url: str = TERRARIUM_URL,
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
        timeout: float = 30.0,
    ):
        super().__init__(name="dem", cache_dir=cache_dir, offline_mode=offline_mode, timeout=timeout)
        self.tile_url = tile_url
        self._tile_cache: Dict[Tuple[int, int, int], np.ndarray] = {}

    @staticmethod
    def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int, float, float]:
        """Convert lat/lon to Web Mercator tile x, y, and intra-tile pixel offsets (0-256)."""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_val = (lon + 180.0) / 360.0 * n
        y_val = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

        tile_x = int(math.floor(x_val))
        tile_y = int(math.floor(y_val))
        px_x = (x_val - tile_x) * 256.0
        px_y = (y_val - tile_y) * 256.0
        return tile_x, tile_y, px_x, px_y

    def get_tile(self, zoom: int, tile_x: int, tile_y: int) -> np.ndarray:
        """Fetch and decode a Terrarium DEM tile into elevation array in meters."""
        key = (zoom, tile_x, tile_y)
        if key in self._tile_cache:
            return self._tile_cache[key]

        cache_filename = f"terrarium_{zoom}_{tile_x}_{tile_y}.png"
        url = self.tile_url.format(z=zoom, x=tile_x, y=tile_y)

        if self.is_cached(cache_filename, ext=".png"):
            raw_bytes = self.read_cached_bytes(cache_filename, ext=".png")
            if not raw_bytes:  # Empty marker for missing/ocean tile
                zeros = np.zeros((256, 256), dtype=np.float32)
                self._tile_cache[key] = zeros
                return zeros

        try:
            raw_bytes = self.fetch_bytes(url, cache_key=cache_filename, ext=".png")
            import io
            im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            arr = np.asarray(im, dtype=np.float32)
            # Terrarium decode: (R * 256 + G + B / 256) - 32768
            elev = arr[..., 0] * 256.0 + arr[..., 1] + arr[..., 2] / 256.0 - 32768.0
            self._tile_cache[key] = elev
            return elev
        except Exception as e:
            logger.warning("[dem] Failed to fetch DEM tile (%d, %d, %d): %s", zoom, tile_x, tile_y, e)
            zeros = np.zeros((256, 256), dtype=np.float32)
            self._tile_cache[key] = zeros
            try:
                self.write_cached_bytes(cache_filename, b"", ext=".png")
            except Exception:
                pass
            return zeros

    def get_elevation(self, lat: float, lon: float, zoom: int = 12) -> float:
        """Query spot elevation at latitude and longitude in meters."""
        tx, ty, px, py = self.lat_lon_to_tile(lat, lon, zoom)
        tile = self.get_tile(zoom, tx, ty)
        ix = min(max(0, int(px)), 255)
        iy = min(max(0, int(py)), 255)
        return float(tile[iy, ix])

    def compute_skyline_profile(
        self,
        lat: float,
        lon: float,
        heading: float,
        hfov: float = 60.0,
        range_m: float = 25000.0,
        samples: int = 24,
        camera_height_m: float = 2.0,
        zoom: int = 12,
    ) -> Dict[str, Any]:
        """Compute visual skyline profile from a candidate viewpoint.
        
        Returns bearings, elevation angles (degrees), distances to skyline peaks,
        accounting for Earth curvature and refraction.
        """
        samples = min(max(int(samples), 16), 80)
        cam_elev = self.get_elevation(lat, lon, zoom=zoom) + camera_height_m
        bearings = np.linspace(heading - hfov / 2.0, heading + hfov / 2.0, samples)
        distances = np.linspace(500.0, range_m, 35)  # High-fidelity radial distance rings

        skyline_elev_angles = np.full(samples, -90.0, dtype=np.float32)
        skyline_distances = np.zeros(samples, dtype=np.float32)

        lat_rad0 = math.radians(lat)
        meters_per_deg_lat = 111320.0
        meters_per_deg_lon = 111320.0 * math.cos(lat_rad0)

        for i, b in enumerate(bearings):
            b_rad = math.radians(b)
            sin_b = math.sin(b_rad)
            cos_b = math.cos(b_rad)

            for d in distances:
                d_lat = (d * cos_b) / meters_per_deg_lat
                d_lon = (d * sin_b) / meters_per_deg_lon
                sample_lat = lat + d_lat
                sample_lon = lon + d_lon

                ground_elev = self.get_elevation(sample_lat, sample_lon, zoom=zoom)
                
                # Curvature and refraction drop: drop = (1 - k) * d^2 / (2 * R)
                curvature_drop = (1.0 - K_REFRACTION) * (d ** 2) / (2.0 * R_EARTH)
                apparent_elev = ground_elev - curvature_drop
                
                # Elevation angle: arctan((apparent - cam) / distance)
                angle_deg = math.degrees(math.atan2(apparent_elev - cam_elev, d))
                if angle_deg > skyline_elev_angles[i]:
                    skyline_elev_angles[i] = angle_deg
                    skyline_distances[i] = d

        return {
            "center": [lat, lon],
            "camera_elevation_m": round(cam_elev, 1),
            "heading": heading,
            "hfov": hfov,
            "bearings": [round(float(b), 2) for b in bearings],
            "skyline_angles": [round(float(a), 3) for a in skyline_elev_angles],
            "skyline_distances_m": [round(float(d), 1) for d in skyline_distances],
        }
