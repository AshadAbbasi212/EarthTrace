"""OpenStreetMap Nominatim geocoding and reverse geocoding provider with polite rate limiting."""
from __future__ import annotations

import logging
import threading
import time
import urllib.parse
from typing import Any, Dict, List, Optional
from pathlib import Path

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.nominatim")


class NominatimProvider(BaseProvider):
    """Provides keyless geocoding and reverse geocoding via OpenStreetMap Nominatim."""

    _last_request_time = 0.0
    _lock = threading.Lock()

    def __init__(
        self,
        endpoint: str = "https://nominatim.openstreetmap.org/search",
        reverse_endpoint: str = "https://nominatim.openstreetmap.org/reverse",
        rate_limit_sec: float = 1.1,
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
        timeout: float = 20.0,
        user_agent: str = "GlobalPhotoGeolocator/1.0 (Photo geolocation research tool)",
    ):
        super().__init__(name="nominatim", cache_dir=cache_dir, offline_mode=offline_mode, timeout=timeout, user_agent=user_agent)
        self.endpoint = endpoint
        self.reverse_endpoint = reverse_endpoint
        self.rate_limit_sec = rate_limit_sec

    def _wait_for_rate_limit(self) -> None:
        """Enforce Nominatim fair usage policy (<= 1 request per second)."""
        with self._lock:
            now = time.time()
            elapsed = now - self.__class__._last_request_time
            if elapsed < self.rate_limit_sec:
                time.sleep(self.rate_limit_sec - elapsed)
            self.__class__._last_request_time = time.time()

    def search(self, query: str, country_codes: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search places by text query, checking offline gazetteer first."""
        # 1. Fast-path: Check local offline SQLite gazetteer for instant match
        try:
            from geolocator.data.gazetteer import query_offline_gazetteer
            first_cc = country_codes.split(",")[0].strip() if country_codes else None
            offline_hits = query_offline_gazetteer(query, country_iso=first_cc)
            if offline_hits:
                logger.info("[nominatim] Resolved '%s' via offline local gazetteer (%d hits)", query, len(offline_hits))
                return offline_hits[:limit]
        except Exception as e:
            logger.debug("[nominatim] Offline gazetteer check bypass: %s", e)

        params = {
            "q": query,
            "format": "jsonv2",
            "limit": str(limit),
            "addressdetails": "1",
        }
        if country_codes:
            params["countrycodes"] = country_codes.lower()

        cache_key = self._hash_key(params)
        cached = self.read_cached_json(cache_key)
        if cached is not None:
            return cached

        if self.offline_mode:
            raise FileNotFoundError(f"[nominatim] Query '{query}' not in cache and running offline")

        self._wait_for_rate_limit()
        url = f"{self.endpoint}?{urllib.parse.urlencode(params)}"
        data = self.fetch_json(url, cache_key=cache_key)
        return data if isinstance(data, list) else []

    def reverse(self, lat: float, lon: float, zoom: int = 14) -> Optional[Dict[str, Any]]:
        """Reverse geocode coordinates to location name and admin details."""
        params = {
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "zoom": str(zoom),
            "format": "jsonv2",
            "addressdetails": "1",
        }
        cache_key = self._hash_key(params)
        cached = self.read_cached_json(cache_key)
        if cached is not None:
            return cached

        if self.offline_mode:
            raise FileNotFoundError(f"[nominatim] Reverse geocode ({lat}, {lon}) not cached and offline")

        self._wait_for_rate_limit()
        url = f"{self.reverse_endpoint}?{urllib.parse.urlencode(params)}"
        try:
            data = self.fetch_json(url, cache_key=cache_key)
            return data if isinstance(data, dict) else None
        except Exception as e:
            logger.warning("[nominatim] Reverse geocoding failed for (%s, %s): %s", lat, lon, e)
            return None
