"""OpenStreetMap Overpass vector data provider with mirror failover and query caching."""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
import urllib.error
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from geolocator.providers.base import BaseProvider

logger = logging.getLogger("geolocator.providers.osm")


class OSMProvider(BaseProvider):
    """Provides keyless vector geospatial data from OpenStreetMap Overpass API."""

    def __init__(
        self,
        endpoints: Optional[List[str]] = None,
        cache_dir: str | Path = ".geo-cache",
        offline_mode: bool = False,
        timeout: float = 45.0,
    ):
        super().__init__(name="osm", cache_dir=cache_dir, offline_mode=offline_mode, timeout=timeout)
        self.endpoints = endpoints or [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
            "https://overpass.private.coffee/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter",
        ]

    def query_ql(self, ql: str, timeout_sec: Optional[int] = None) -> Dict[str, Any]:
        """Execute an Overpass QL query across mirrors with deterministic SHA-1 caching."""
        cache_key = self._hash_key(ql)

        # 1. Check disk cache
        cached = self.read_cached_json(cache_key)
        if cached is not None:
            logger.debug("[osm] Returning cached result for query %s", cache_key)
            return cached

        if self.offline_mode:
            raise FileNotFoundError(f"[osm] Query {cache_key} not in cache and running in offline mode")

        # 2. Try mirrors sequentially
        to = int(timeout_sec or self.timeout)
        encoded_data = urllib.parse.urlencode({"data": ql}).encode("utf-8")
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        last_error = None
        for endpoint in self.endpoints:
            try:
                logger.info("[osm] Querying %s (timeout: %ds)...", endpoint, to)
                req = urllib.request.Request(endpoint, data=encoded_data, headers=headers)
                with urllib.request.urlopen(req, timeout=to + 10) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    if data.get("remark"):
                        logger.warning("[osm] Overpass remark: %s", data["remark"])
                    self.write_cached_json(cache_key, data)
                    return data
            except Exception as e:
                last_error = e
                logger.warning("[osm] Mirror %s failed: %s", endpoint, e)
                time.sleep(1.0)

        raise RuntimeError(f"[osm] All Overpass mirrors failed: {last_error}")

    def find_features(self, south: float, west: float, north: float, east: float, tag_filter: str) -> List[Dict[str, Any]]:
        """Query elements within bounding box matching tag filter."""
        ql = f"""[out:json][timeout:30];
(
  node{tag_filter}({south},{west},{north},{east});
  way{tag_filter}({south},{west},{north},{east});
  relation{tag_filter}({south},{west},{north},{east});
);
out center tags qt;"""
        data = self.query_ql(ql)
        results = []
        for el in data.get("elements", []):
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is not None and lon is not None:
                results.append({
                    "id": el.get("id"),
                    "type": el.get("type"),
                    "lat": float(lat),
                    "lon": float(lon),
                    "tags": el.get("tags", {}),
                })
        return results

    def find_co_occurrences(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        tag_a: str,
        tag_b: str,
        radius_m: int = 500,
    ) -> List[Dict[str, Any]]:
        """Find co-occurrence of features A and B within radius meters."""
        ql = f"""[out:json][timeout:45];
(
  node{tag_a}({south},{west},{north},{east});
  way{tag_a}({south},{west},{north},{east});
)->.a;
(
  node{tag_b}(around.a:{radius_m});
  way{tag_b}(around.a:{radius_m});
)->.b;
.b out center tags qt;"""
        data = self.query_ql(ql)
        results = []
        for el in data.get("elements", []):
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is not None and lon is not None:
                results.append({
                    "id": el.get("id"),
                    "type": el.get("type"),
                    "lat": float(lat),
                    "lon": float(lon),
                    "tags": el.get("tags", {}),
                })
        return results
