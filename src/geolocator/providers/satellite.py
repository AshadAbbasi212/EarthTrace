"""Satellite imagery provider supporting keyless Google, Esri and Sentinel-2 mosaics."""
from __future__ import annotations

import io
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.satellite")

TILE_SOURCES = {
    "google": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "esri": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "sentinel": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
}


class SatelliteProvider(BaseProvider):
    """Provides keyless satellite imagery tiles and mosaic compositing."""

    def __init__(
        self,
        default_source: str = "google",
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
        timeout: float = 25.0,
    ):
        super().__init__(name="satellite", cache_dir=cache_dir, offline_mode=offline_mode, timeout=timeout)
        self.default_source = default_source

    @staticmethod
    def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert latitude and longitude to tile (x, y) coordinates."""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x_tile, y_tile

    @staticmethod
    def tile_to_lat_lon(x: int, y: int, zoom: int) -> Tuple[float, float]:
        """Convert tile (x, y) coordinates to top-left latitude and longitude."""
        n = 2.0 ** zoom
        lon = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat = math.degrees(lat_rad)
        return lat, lon

    @staticmethod
    def meters_per_pixel(lat: float, zoom: int) -> float:
        """Calculate ground resolution (meters per pixel) at given latitude and zoom."""
        return 156543.03392 * math.cos(math.radians(lat)) / (2.0 ** zoom)

    def get_tile(self, zoom: int, x: int, y: int, source: Optional[str] = None) -> Image.Image:
        """Fetch a single satellite tile as a PIL Image."""
        src = source or self.default_source
        url_template = TILE_SOURCES.get(src, TILE_SOURCES["google"])
        url = url_template.format(z=zoom, x=x, y=y)
        cache_key = f"{src}_{zoom}_{x}_{y}.jpg"

        try:
            raw_bytes = self.fetch_bytes(url, cache_key=cache_key, ext=".jpg")
            return Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        except Exception as e:
            logger.warning("[satellite] Tile fetch failed (%s, z=%d, x=%d, y=%d): %s", src, zoom, x, y, e)
            return Image.new("RGB", (256, 256), (40, 40, 40))

    def fetch_satellite_image(self, lat: float, lon: float, zoom: int = 16) -> Image.Image:
        """Fetch satellite tile centered at GPS coordinates."""
        tx, ty = self.lat_lon_to_tile(lat, lon, zoom)
        return self.get_tile(zoom, tx, ty)

    def fetch_mosaic(
        self,
        lat: float,
        lon: float,
        zoom: int = 17,
        radius_tiles: int = 1,
        source: Optional[str] = None,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """Fetch and stitch a grid of (2*radius + 1)^2 tiles around coordinates.
        
        Returns the stitched PIL image and geospatial metadata dictionary.
        """
        center_x, center_y = self.lat_lon_to_tile(lat, lon, zoom)
        xs = range(center_x - radius_tiles, center_x + radius_tiles + 1)
        ys = range(center_y - radius_tiles, center_y + radius_tiles + 1)

        width_px = len(xs) * 256
        height_px = len(ys) * 256
        mosaic_im = Image.new("RGB", (width_px, height_px), "black")

        for col_idx, x in enumerate(xs):
            for row_idx, y in enumerate(ys):
                tile = self.get_tile(zoom, x, y, source=source)
                mosaic_im.paste(tile, (col_idx * 256, row_idx * 256))

        nw_lat, nw_lon = self.tile_to_lat_lon(xs[0], ys[0], zoom)
        se_lat, se_lon = self.tile_to_lat_lon(xs[-1] + 1, ys[-1] + 1, zoom)

        metadata = {
            "center": [lat, lon],
            "zoom": zoom,
            "origin_tile": [xs[0], ys[0]],
            "tile_count": [len(xs), len(ys)],
            "size_px": [width_px, height_px],
            "bounds": {"north": nw_lat, "west": nw_lon, "south": se_lat, "east": se_lon},
            "meters_per_px": self.meters_per_pixel(lat, zoom),
            "source": source or self.default_source,
        }
        return mosaic_im, metadata
