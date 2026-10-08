"""Street-level and ground-level keyless photo provider using Wikimedia/Wikipedia geosearch."""
from __future__ import annotations

import io
import logging
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.street_image")


class StreetImageProvider(BaseProvider):
    """Provides keyless ground-level photos around candidate coordinates.
    
    Uses Wikipedia Geosearch API and Wikimedia thumbnail delivery.
    Reports 'not available' where no coverage exists.
    """

    def __init__(
        self,
        api_endpoint: str = "https://en.wikipedia.org/w/api.php",
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
        timeout: float = 20.0,
        user_agent: str = "GlobalPhotoGeolocator/1.0 (Photo geolocation research tool)",
    ):
        super().__init__(name="street_image", cache_dir=cache_dir, offline_mode=offline_mode, timeout=timeout, user_agent=user_agent)
        self.api_endpoint = api_endpoint

    def search_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: int = 3000,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Search geotagged articles and extract lead images near coordinates."""
        params = {
            "action": "query",
            "generator": "geosearch",
            "ggscoord": f"{lat:.6f}|{lon:.6f}",
            "ggsradius": str(min(radius_m, 10000)),
            "ggslimit": str(limit),
            "prop": "pageimages|coordinates",
            "piprop": "thumbnail",
            "pithumbsize": "640",
            "format": "json",
        }
        cache_key = self._hash_key(f"geosearch_{lat:.4f}_{lon:.4f}_{radius_m}")
        cached = self.read_cached_json(cache_key)
        if cached is not None:
            return cached

        if self.offline_mode:
            return []

        url = f"{self.api_endpoint}?{urllib.parse.urlencode(params)}"
        try:
            data = self.fetch_json(url, cache_key=cache_key)
            pages = data.get("query", {}).get("pages", {})
            results = []

            for page_id, p_info in pages.items():
                title = p_info.get("title", "")
                thumb = p_info.get("thumbnail")
                coords = p_info.get("coordinates", [{}])[0]
                item_lat = coords.get("lat", lat)
                item_lon = coords.get("lon", lon)

                if thumb and thumb.get("source"):
                    results.append({
                        "id": str(page_id),
                        "title": title,
                        "lat": item_lat,
                        "lon": item_lon,
                        "image_url": thumb["source"],
                        "width": thumb.get("width"),
                        "height": thumb.get("height"),
                        "source": "Wikimedia/Wikipedia",
                    })

            self.write_cached_json(cache_key, results)
            return results
        except Exception as e:
            logger.warning("[street_image] Nearby photo search failed for (%s, %s): %s", lat, lon, e)
            return []

    def _fetch_page_image(self, title: str, page_id: int) -> Optional[Dict[str, Any]]:
        """Fetch lead thumbnail for a Wikipedia page."""
        params = {
            "action": "query",
            "prop": "pageimages",
            "pageids": str(page_id),
            "pithumbsize": "640",
            "format": "json",
        }
        cache_key = f"page_img_{page_id}"
        cached = self.read_cached_json(cache_key)
        if cached is not None:
            return cached

        if self.offline_mode:
            return None

        url = f"{self.api_endpoint}?{urllib.parse.urlencode(params)}"
        try:
            data = self.fetch_json(url, cache_key=cache_key)
            page_data = data.get("query", {}).get("pages", {}).get(str(page_id), {})
            thumb = page_data.get("thumbnail")
            if thumb:
                self.write_cached_json(cache_key, thumb)
                return thumb
        except Exception as e:
            logger.debug("[street_image] Failed thumbnail query for page %s: %s", page_id, e)
        return None

    def fetch_image(self, image_url: str) -> Optional[Image.Image]:
        """Fetch image file bytes and return PIL Image."""
        cache_key = self._hash_key(image_url)
        try:
            raw_bytes = self.fetch_bytes(image_url, cache_key=cache_key, ext=".jpg")
            return Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        except Exception as e:
            logger.warning("[street_image] Failed to download image %s: %s", image_url, e)
            return None

    def find_nearby_images(self, lat: float, lon: float, radius_m: int = 3000, limit: int = 8) -> List[Dict[str, Any]]:
        """Alias for search_nearby."""
        return self.search_nearby(lat=lat, lon=lon, radius_m=radius_m, limit=limit)
