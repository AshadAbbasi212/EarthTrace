"""Geographic utilities: Haversine distance, country bounding boxes, offline point-in-region."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth mean radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


# Curated table of major country and region bounding boxes [min_lat, min_lon, max_lat, max_lon]
COUNTRY_BBOXES: Dict[str, Tuple[float, float, float, float]] = {
    # Specific sub-continental and regional countries checked first
    "pakistan": (23.6, 60.8, 37.1, 77.8),
    "nepal": (26.3, 80.0, 30.5, 88.2),
    "bangladesh": (20.5, 88.0, 26.7, 92.7),
    "sri lanka": (5.9, 79.6, 9.9, 81.9),
    "afghanistan": (29.3, 60.5, 38.5, 74.9),
    "iran": (25.0, 44.0, 39.8, 63.4),
    "iraq": (29.0, 38.7, 37.4, 48.6),
    "united kingdom": (49.8, -8.6, 60.9, 1.8),
    "ireland": (51.4, -10.5, 55.4, -5.9),
    "france": (41.3, -5.1, 51.1, 9.6),
    "germany": (47.2, 5.8, 55.1, 15.0),
    "italy": (35.5, 6.6, 47.1, 18.6),
    "spain": (35.9, -9.3, 43.8, 3.3),
    "portugal": (36.9, -9.5, 42.2, -6.1),
    "norway": (57.9, 4.5, 71.2, 31.1),
    "sweden": (55.3, 11.0, 69.1, 24.2),
    "finland": (59.8, 20.5, 70.1, 31.6),
    "denmark": (54.5, 8.0, 57.8, 12.7),
    "netherlands": (50.7, 3.3, 53.6, 7.2),
    "belgium": (49.5, 2.5, 51.5, 6.4),
    "switzerland": (45.8, 5.9, 47.8, 10.5),
    "austria": (46.3, 9.5, 49.0, 17.2),
    "poland": (49.0, 14.1, 54.8, 24.2),
    "greece": (34.8, 19.3, 41.8, 28.3),
    "turkey": (35.8, 25.6, 42.1, 44.8),
    "egypt": (22.0, 24.7, 31.7, 36.9),
    "morocco": (21.4, -17.1, 35.9, -1.0),
    "algeria": (18.9, -8.7, 37.1, 12.0),
    "tunisia": (30.2, 7.5, 37.6, 11.6),
    "libya": (19.5, 9.3, 33.2, 25.2),
    "saudi arabia": (16.3, 34.5, 32.2, 55.7),
    "united arab emirates": (22.6, 51.5, 26.1, 56.4),
    "japan": (24.0, 122.9, 45.6, 153.0),
    "south korea": (33.1, 124.6, 38.6, 131.9),
    "thailand": (5.6, 97.3, 20.5, 105.7),
    "vietnam": (8.5, 102.1, 23.4, 109.5),
    "indonesia": (-11.0, 95.0, 6.0, 141.0),
    "malaysia": (1.0, 99.6, 7.4, 119.3),
    "philippines": (4.6, 116.9, 21.3, 126.6),
    "india": (6.7, 68.1, 35.5, 97.4),
    "china": (18.0, 75.0, 53.6, 135.1),
    "australia": (-43.7, 112.9, -10.0, 153.7),
    "new zealand": (-47.3, 166.4, -34.4, 178.6),
    "united states": (24.5, -124.8, 49.4, -66.9),
    "canada": (41.7, -141.0, 83.1, -52.6),
    "mexico": (14.5, -118.4, 32.7, -86.7),
    "brazil": (-33.8, -73.9, 5.3, -34.8),
    "argentina": (-55.1, -73.6, -21.8, -53.6),
    "chile": (-55.9, -75.7, -17.5, -66.9),
    "south africa": (-34.8, 16.4, -22.1, 32.9),
    "kenya": (-4.7, 33.9, 4.6, 41.9),
    "russia": (41.2, 19.6, 81.9, 180.0),
}

REGION_BOUNDS: Dict[str, Tuple[float, float, float, float]] = {
    "scandinavia": (54.5, 4.5, 71.2, 31.6),       # Norway, Sweden, Finland, Denmark
    "sahara": (15.0, -17.0, 34.0, 35.0),           # North Africa hyper-arid zone
    "middle_east": (12.0, 34.0, 42.0, 63.0),       # Arabian peninsula, Levant, Mesopotamia, Iran
    "western_europe": (36.0, -10.0, 60.0, 20.0),   # Iberia, France, UK, Benelux, Germany, Italy
    "central_asia": (35.0, 50.0, 55.0, 88.0),      # Kazakhstan, Uzbekistan, etc.
    "southeast_asia": (-11.0, 92.0, 28.0, 141.0),  # ASEAN nations
    "amazon_basin": (-18.0, -78.0, 5.0, -48.0),    # Tropical South America
}


def point_in_bbox(lat: float, lon: float, bbox: Tuple[float, float, float, float]) -> bool:
    """Check if (lat, lon) is inside bounding box [min_lat, min_lon, max_lat, max_lon]."""
    min_lat, min_lon, max_lat, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def is_in_region(lat: float, lon: float, region_name: str) -> bool:
    """Check if point falls within named broad region."""
    reg = region_name.strip().lower()
    if reg in REGION_BOUNDS:
        return point_in_bbox(lat, lon, REGION_BOUNDS[reg])
    return False


def get_country_candidate(lat: float, lon: float) -> Optional[str]:
    """Find matching country based on bounding box lookup."""
    for country, bbox in COUNTRY_BBOXES.items():
        if point_in_bbox(lat, lon, bbox):
            return country.title()
    return None


def cluster_points(
    points: List[Dict[str, float]],
    radius_km: float = 75.0,
    max_clusters: int = 20,
) -> List[Dict[str, Any]]:
    """Cluster GPS points using a greedy nearest-neighbor clustering within radius_km."""
    if not points:
        return []

    # Sort points descending by score/probability
    sorted_pts = sorted(points, key=lambda p: p.get("score", p.get("prob", 0.0)), reverse=True)
    clusters: List[Dict[str, Any]] = []

    for pt in sorted_pts:
        lat = pt["lat"]
        lon = pt["lon"]
        score = pt.get("score", pt.get("prob", 0.0))

        # Check if point belongs to an existing cluster
        assigned = False
        for c in clusters:
            dist = haversine_distance_km(lat, lon, c["center_lat"], c["center_lon"])
            if dist <= radius_km:
                c["points"].append(pt)
                c["total_score"] += score
                # Update bbox
                c["min_lat"] = min(c["min_lat"], lat)
                c["max_lat"] = max(c["max_lat"], lat)
                c["min_lon"] = min(c["min_lon"], lon)
                c["max_lon"] = max(c["max_lon"], lon)
                assigned = True
                break

        if not assigned:
            # Create a new cluster
            # Expand bbox by buffer (~25 km ~ 0.25 deg)
            buf = radius_km / 111.0
            clusters.append({
                "cluster_id": f"cell_{len(clusters) + 1}",
                "center_lat": lat,
                "center_lon": lon,
                "min_lat": lat - buf,
                "max_lat": lat + buf,
                "min_lon": lon - buf,
                "max_lon": lon + buf,
                "points": [pt],
                "total_score": score,
                "best_score": score,
                "country": pt.get("country", get_country_candidate(lat, lon)),
            })

    # Sort clusters by best score
    clusters.sort(key=lambda c: c["best_score"], reverse=True)
    return clusters[:max_clusters]
