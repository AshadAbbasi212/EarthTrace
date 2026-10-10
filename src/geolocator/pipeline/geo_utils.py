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
    # Distinct sub-continental countries with priority checking
    "nepal": (26.3, 80.0, 30.5, 88.2),
    "bangladesh": (20.5, 88.0, 26.7, 92.7),
    "sri lanka": (5.9, 79.6, 9.9, 81.9),
    "pakistan": (23.6, 60.8, 37.1, 75.3),
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

# Curated regional anchors for high-probability country hypothesis candidate synthesis
COUNTRY_ANCHORS: Dict[str, List[Dict[str, Any]]] = {
    "pakistan": [
        {"name": "Islamabad / Rawalpindi", "lat": 33.6844, "lon": 73.0479},
        {"name": "Lahore Urban Center", "lat": 31.5204, "lon": 74.3587},
        {"name": "Karachi Coastal Corridor", "lat": 24.8607, "lon": 67.0011},
        {"name": "Peshawar Khyber Region", "lat": 34.0151, "lon": 71.5249},
        {"name": "Faisalabad Agricultural Hub", "lat": 31.4504, "lon": 73.1350},
        {"name": "Multan Southern Punjab", "lat": 30.1575, "lon": 71.5249},
        {"name": "Quetta Highlands", "lat": 30.1798, "lon": 66.9750},
        {"name": "Murree / Galyat Foothills", "lat": 33.9062, "lon": 73.3903},
    ],
    "india": [
        {"name": "Delhi National Capital Region", "lat": 28.6139, "lon": 77.2090},
        {"name": "Mumbai Western Coast", "lat": 19.0760, "lon": 72.8777},
        {"name": "Bengaluru Southern Hub", "lat": 12.9716, "lon": 77.5946},
        {"name": "Jaipur Rajasthan", "lat": 26.9124, "lon": 75.7873},
        {"name": "Kolkata Eastern Hub", "lat": 22.5726, "lon": 88.3639},
        {"name": "Chandigarh Urban Plain", "lat": 30.7333, "lon": 76.7794},
    ],
    "nepal": [
        {"name": "Kathmandu Valley", "lat": 27.7172, "lon": 85.3240},
        {"name": "Pokhara Valley", "lat": 28.2096, "lon": 83.9856},
    ],
    "bangladesh": [
        {"name": "Dhaka Metropolitan", "lat": 23.8103, "lon": 90.4125},
        {"name": "Chittagong Coastal", "lat": 22.3569, "lon": 91.7832},
    ],
    "afghanistan": [
        {"name": "Kabul Basin", "lat": 34.5553, "lon": 69.2075},
        {"name": "Herat Western Oasis", "lat": 34.3529, "lon": 62.2040},
    ],
    "iran": [
        {"name": "Tehran Foothills", "lat": 35.6892, "lon": 51.3890},
        {"name": "Isfahan Central Plateau", "lat": 32.6546, "lon": 51.6680},
    ],
    "turkey": [
        {"name": "Istanbul Bosporus", "lat": 41.0082, "lon": 28.9784},
        {"name": "Ankara Central Anatolia", "lat": 39.9334, "lon": 32.8597},
        {"name": "Izmir Aegean Coast", "lat": 38.4237, "lon": 27.1428},
    ],
    "saudi arabia": [
        {"name": "Riyadh Central Plateau", "lat": 24.7136, "lon": 46.6753},
        {"name": "Jeddah Red Sea", "lat": 21.5433, "lon": 39.1728},
    ],
    "united arab emirates": [
        {"name": "Dubai Urban Coast", "lat": 25.2048, "lon": 55.2708},
        {"name": "Abu Dhabi Capital", "lat": 24.4539, "lon": 54.3773},
    ],
    "egypt": [
        {"name": "Cairo Nile Delta", "lat": 30.0444, "lon": 31.2357},
        {"name": "Alexandria Mediterranean", "lat": 31.2001, "lon": 29.9187},
    ],
    "morocco": [
        {"name": "Casablanca Atlantic Coast", "lat": 33.5731, "lon": -7.5898},
        {"name": "Marrakech Atlas Foothills", "lat": 31.6295, "lon": -7.9811},
    ],
    "united kingdom": [
        {"name": "London Greater Metropolitan", "lat": 51.5074, "lon": -0.1278},
        {"name": "Manchester Northwest", "lat": 53.4808, "lon": -2.2426},
        {"name": "Edinburgh Scotland", "lat": 55.9533, "lon": -3.1883},
    ],
    "france": [
        {"name": "Paris Île-de-France", "lat": 48.8566, "lon": 2.3522},
        {"name": "Marseille Provence Coast", "lat": 43.2965, "lon": 5.3698},
        {"name": "Lyon Rhône Corridor", "lat": 45.7640, "lon": 4.8357},
    ],
    "germany": [
        {"name": "Berlin Metropolitan", "lat": 52.5200, "lon": 13.4050},
        {"name": "Munich Bavaria", "lat": 48.1351, "lon": 11.5820},
        {"name": "Frankfurt Rhine-Main", "lat": 50.1109, "lon": 8.6821},
    ],
    "italy": [
        {"name": "Rome Central", "lat": 41.9028, "lon": 12.4964},
        {"name": "Milan Lombardy", "lat": 45.4642, "lon": 9.1900},
        {"name": "Naples Bay", "lat": 40.8518, "lon": 14.2681},
    ],
    "spain": [
        {"name": "Madrid Central Meseta", "lat": 40.4168, "lon": -3.7038},
        {"name": "Barcelona Catalonia", "lat": 41.3851, "lon": 2.1734},
    ],
    "united states": [
        {"name": "New York Metropolitan", "lat": 40.7128, "lon": -74.0060},
        {"name": "Los Angeles Coastal Plain", "lat": 34.0522, "lon": -118.2437},
        {"name": "Chicago Great Lakes", "lat": 41.8781, "lon": -87.6298},
        {"name": "Austin Texas Corridor", "lat": 30.2672, "lon": -97.7431},
    ],
    "japan": [
        {"name": "Tokyo Kanto Plain", "lat": 35.6762, "lon": 139.6503},
        {"name": "Osaka / Kyoto Kansai", "lat": 34.6937, "lon": 135.5023},
    ],
    "china": [
        {"name": "Beijing North China Plain", "lat": 39.9042, "lon": 116.4074},
        {"name": "Shanghai Yangtze Delta", "lat": 31.2304, "lon": 121.4737},
        {"name": "Guangzhou Pearl River Delta", "lat": 23.1291, "lon": 113.2644},
        {"name": "Chengdu Sichuan Basin", "lat": 30.5728, "lon": 104.0668},
    ],
}


def get_country_anchors(country_name: str, max_anchors: int = 6) -> List[Dict[str, Any]]:
    """Retrieve representative geographic anchors for a specified country."""
    c_clean = country_name.strip().lower()
    for k, anchors in COUNTRY_ANCHORS.items():
        if k == c_clean or k in c_clean or c_clean in k:
            return anchors[:max_anchors]
    return []


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
    """Find matching country based on bounding box lookup with border disambiguation."""
    # 1. High-precision border disambiguation for South Asia
    # Pakistan vs India border logic
    if 23.6 <= lat <= 37.1 and 60.8 <= lon <= 75.3:
        # Southern border: Rajasthan / Gujarat vs Sindh
        if lat < 28.0 and lon > 71.0:
            return "India"
        if lat < 24.5 and lon > 68.2:
            return "India"
        # Central / Punjab border: Indian Punjab / Haryana / Delhi vs Pakistani Punjab
        if 28.0 <= lat < 32.2 and lon > 74.6:
            return "India"
        return "Pakistan"

    # Nepal
    if 26.3 <= lat <= 30.5 and 80.0 <= lon <= 88.2:
        return "Nepal"

    # Bangladesh
    if 20.5 <= lat <= 26.7 and 88.0 <= lon <= 92.7:
        return "Bangladesh"

    # Sri Lanka
    if 5.9 <= lat <= 9.9 and 79.6 <= lon <= 81.9:
        return "Sri Lanka"

    # India broad check
    if 6.7 <= lat <= 35.5 and 68.1 <= lon <= 97.4:
        return "India"

    # 2. General bounding box table
    for country, bbox in COUNTRY_BBOXES.items():
        if country in ("pakistan", "india", "nepal", "bangladesh", "sri lanka"):
            continue
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
