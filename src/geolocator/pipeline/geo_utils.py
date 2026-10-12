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
    # Distinct sub-continental and Middle Eastern countries with priority checking
    "nepal": (26.3, 80.0, 30.5, 88.2),
    "bangladesh": (20.5, 88.0, 26.7, 92.7),
    "sri lanka": (5.9, 79.6, 9.9, 81.9),
    "pakistan": (23.6, 60.8, 37.1, 75.3),
    "afghanistan": (29.3, 60.5, 38.5, 74.9),
    "iran": (25.0, 44.0, 39.8, 63.4),
    "iraq": (29.0, 38.7, 37.4, 48.6),
    "syria": (32.3, 35.6, 37.4, 42.4),
    "israel": (29.4, 34.2, 33.4, 35.9),
    "saudi arabia": (16.3, 34.5, 32.2, 55.7),
    "united arab emirates": (22.6, 51.5, 26.1, 56.4),
    "qatar": (24.4, 50.7, 26.3, 51.7),
    "kuwait": (28.5, 46.5, 30.2, 48.6),
    "bahrain": (25.7, 50.3, 26.4, 50.7),
    "oman": (16.6, 52.0, 26.5, 59.9),
    "yemen": (12.1, 41.8, 19.0, 54.6),
    "turkey": (35.8, 25.6, 42.1, 44.8),
    "turkiye": (35.8, 25.6, 42.1, 44.8),
    "egypt": (22.0, 24.7, 31.7, 36.9),
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
    "morocco": (21.4, -17.1, 35.9, -1.0),
    "algeria": (18.9, -8.7, 37.1, 12.0),
    "tunisia": (30.2, 7.5, 37.6, 11.6),
    "libya": (19.5, 9.3, 33.2, 25.2),
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
        {"name": "Islamabad Capital Territory", "lat": 33.6844, "lon": 73.0479},
        {"name": "Rawalpindi / Murree Foothills", "lat": 33.5973, "lon": 73.0479},
        {"name": "Murree / Galyat Ridge", "lat": 33.9062, "lon": 73.3903},
        {"name": "Lahore Urban Center", "lat": 31.5204, "lon": 74.3587},
        {"name": "Karachi Coastal Corridor", "lat": 24.8607, "lon": 67.0011},
        {"name": "Peshawar Khyber Gateway", "lat": 34.0151, "lon": 71.5249},
        {"name": "Faisalabad Industrial Hub", "lat": 31.4504, "lon": 73.1350},
        {"name": "Multan Southern Punjab", "lat": 30.1575, "lon": 71.5249},
        {"name": "Quetta Highlands", "lat": 30.1798, "lon": 66.9750},
        {"name": "Abbottabad / Hazara Valley", "lat": 34.1688, "lon": 73.2215},
        {"name": "Gilgit Karakoram Gateway", "lat": 35.9208, "lon": 74.3144},
        {"name": "Gwadar Coastal Port", "lat": 25.1264, "lon": 62.3225},
    ],
    "india": [
        {"name": "Delhi National Capital Region", "lat": 28.6139, "lon": 77.2090},
        {"name": "Mumbai Western Coast", "lat": 19.0760, "lon": 72.8777},
        {"name": "Bengaluru Southern Hub", "lat": 12.9716, "lon": 77.5946},
        {"name": "Hyderabad Deccan Center", "lat": 17.3850, "lon": 78.4867},
        {"name": "Chennai Coromandel Coast", "lat": 13.0827, "lon": 80.2707},
        {"name": "Jaipur Rajasthan Desert Gateway", "lat": 26.9124, "lon": 75.7873},
        {"name": "Kolkata Eastern Hub", "lat": 22.5726, "lon": 88.3639},
        {"name": "Chandigarh Urban Plain", "lat": 30.7333, "lon": 76.7794},
        {"name": "Ahmedabad Gujarat Center", "lat": 23.0225, "lon": 72.5714},
        {"name": "Lucknow Gangetic Plain", "lat": 26.8467, "lon": 80.9462},
        {"name": "Amritsar Punjab Gateway", "lat": 31.6340, "lon": 74.8723},
        {"name": "Srinagar Kashmir Valley", "lat": 34.0837, "lon": 74.7973},
        {"name": "Pune Western Ghats", "lat": 18.5204, "lon": 73.8567},
    ],
    "united arab emirates": [
        {"name": "Dubai Downtown / Sheikh Zayed Rd", "lat": 25.2048, "lon": 55.2708},
        {"name": "Dubai Marina / Palm Jumeirah", "lat": 25.0805, "lon": 55.1403},
        {"name": "Abu Dhabi Corniche / Capital", "lat": 24.4539, "lon": 54.3773},
        {"name": "Abu Dhabi Yas Island", "lat": 24.4984, "lon": 54.6053},
        {"name": "Sharjah Urban Center", "lat": 25.3573, "lon": 55.4033},
        {"name": "Al Ain Oasis / Jebel Hafeet", "lat": 24.2075, "lon": 55.7447},
        {"name": "Ras Al Khaimah / Jebel Jais", "lat": 25.7895, "lon": 55.9432},
        {"name": "Fujairah Gulf of Oman Coast", "lat": 25.1288, "lon": 56.3265},
    ],
    "saudi arabia": [
        {"name": "Riyadh Olaya / Kingdom Centre", "lat": 24.7136, "lon": 46.6753},
        {"name": "Jeddah Corniche / Red Sea Coast", "lat": 21.5433, "lon": 39.1728},
        {"name": "Makkah Holy Valley", "lat": 21.3891, "lon": 39.8579},
        {"name": "Madinah Central Basin", "lat": 24.5247, "lon": 39.5692},
        {"name": "Dammam / Khobar Eastern Coast", "lat": 26.4207, "lon": 50.0888},
        {"name": "Abha / Asir Highland Ridge", "lat": 18.2164, "lon": 42.5053},
        {"name": "Taif Mountain Plateau", "lat": 21.2854, "lon": 40.4222},
        {"name": "Tabuk Northern Oasis", "lat": 28.3835, "lon": 36.5662},
        {"name": "Buraidah / Al Qassim Oasis", "lat": 26.3260, "lon": 43.9750},
        {"name": "Al Ula / Madain Saleh", "lat": 26.6080, "lon": 37.9250},
    ],
    "qatar": [
        {"name": "Doha West Bay / Corniche", "lat": 25.2854, "lon": 51.5310},
        {"name": "Lusail Modern City", "lat": 25.4200, "lon": 51.4900},
        {"name": "Al Rayyan Education City", "lat": 25.3190, "lon": 51.4250},
        {"name": "Al Wakrah Coastal City", "lat": 25.1768, "lon": 51.6048},
        {"name": "Al Khor Northern Coast", "lat": 25.6839, "lon": 51.5058},
        {"name": "Dukhan Western Oilfield", "lat": 25.4290, "lon": 50.7850},
    ],
    "kuwait": [
        {"name": "Kuwait City Capital / Towers", "lat": 29.3759, "lon": 47.9774},
        {"name": "Hawalli / Salmiya Coast", "lat": 29.3333, "lon": 48.0833},
        {"name": "Al Ahmadi Oilfield District", "lat": 29.0769, "lon": 48.0839},
        {"name": "Al Farwaniya Urban Center", "lat": 29.2778, "lon": 47.9589},
        {"name": "Al Jahra Western Oasis", "lat": 29.3375, "lon": 47.6581},
        {"name": "Subiya / Sheikh Jaber Bridge", "lat": 29.6200, "lon": 48.1500},
    ],
    "oman": [
        {"name": "Muscat Capital / Mutrah Corniche", "lat": 23.5880, "lon": 58.3829},
        {"name": "Salalah Dhofar Monsoon Coast", "lat": 17.0151, "lon": 54.0924},
        {"name": "Sohar Batinah Industrial Port", "lat": 24.3644, "lon": 56.7468},
        {"name": "Nizwa Jebel Akhdar Oasis", "lat": 22.9333, "lon": 57.5333},
        {"name": "Sur Eastern Coastal Port", "lat": 22.5667, "lon": 59.5289},
        {"name": "Khasab Musandam Fjords", "lat": 26.1799, "lon": 56.2483},
    ],
    "bahrain": [
        {"name": "Manama Diplomatic Area / Capital", "lat": 26.2285, "lon": 50.5860},
        {"name": "Muharraq Historic Island", "lat": 26.2572, "lon": 50.6119},
        {"name": "Riffa Southern Palaces", "lat": 26.1300, "lon": 50.5550},
        {"name": "King Fahd Causeway Gateway", "lat": 26.1850, "lon": 50.4550},
        {"name": "Sitra Industrial Island", "lat": 26.1550, "lon": 50.6200},
        {"name": "Amwaj Islands Arabian Gulf", "lat": 26.2900, "lon": 50.6650},
    ],
    "egypt": [
        {"name": "Cairo Downtown / Tahrir", "lat": 30.0444, "lon": 31.2357},
        {"name": "Giza Pyramids Plateau", "lat": 29.9792, "lon": 31.1342},
        {"name": "Alexandria Mediterranean Corniche", "lat": 31.2001, "lon": 29.9187},
        {"name": "Sharm El Sheikh Sinai Resort", "lat": 27.9158, "lon": 34.3299},
        {"name": "Hurghada Red Sea Coast", "lat": 27.2579, "lon": 33.8116},
        {"name": "Luxor Nile Temples", "lat": 25.6872, "lon": 32.6396},
        {"name": "Aswan High Dam / Nile Cataracts", "lat": 24.0889, "lon": 32.8998},
        {"name": "Port Said Suez Canal Gateway", "lat": 31.2653, "lon": 32.3019},
    ],
    "iran": [
        {"name": "Tehran Foothills / Milad Tower", "lat": 35.6892, "lon": 51.3890},
        {"name": "Isfahan Naqsh-e Jahan Square", "lat": 32.6546, "lon": 51.6680},
        {"name": "Shiraz Fars / Persepolis", "lat": 29.5918, "lon": 52.5837},
        {"name": "Mashhad Khorasan Shrine", "lat": 36.2605, "lon": 59.6168},
        {"name": "Tabriz Azerbaijan Historic Bazaar", "lat": 38.0800, "lon": 46.2919},
        {"name": "Ahvaz Khuzestan Karun River", "lat": 31.3183, "lon": 48.6706},
        {"name": "Yazd Desert Adobe Architecture", "lat": 31.8974, "lon": 54.3569},
        {"name": "Rasht Caspian Sea Coast", "lat": 37.2808, "lon": 49.5832},
        {"name": "Bandar Abbas Persian Gulf Strait", "lat": 27.1832, "lon": 56.2666},
    ],
    "turkey": [
        {"name": "Istanbul Bosporus / Sultanahmet", "lat": 41.0082, "lon": 28.9784},
        {"name": "Istanbul Kadikoy / Asian Shore", "lat": 40.9910, "lon": 29.0270},
        {"name": "Ankara Central Anatolia / Kizilay", "lat": 39.9334, "lon": 32.8597},
        {"name": "Izmir Aegean Coast / Kordon", "lat": 38.4237, "lon": 27.1428},
        {"name": "Antalya Mediterranean Turquoise Coast", "lat": 36.8969, "lon": 30.7133},
        {"name": "Bursa Uludag Mountain Base", "lat": 40.1885, "lon": 29.0610},
        {"name": "Trabzon Black Sea Foothills", "lat": 41.0027, "lon": 39.7168},
        {"name": "Konya Anatolian Steppe", "lat": 37.8746, "lon": 32.4932},
        {"name": "Gaziantep Southeastern Hub", "lat": 37.0662, "lon": 37.3833},
        {"name": "Cappadocia / Goreme Fairy Chimneys", "lat": 38.6431, "lon": 34.8289},
    ],
    "turkiye": [
        {"name": "Istanbul Bosporus / Sultanahmet", "lat": 41.0082, "lon": 28.9784},
        {"name": "Ankara Central Anatolia / Kizilay", "lat": 39.9334, "lon": 32.8597},
        {"name": "Izmir Aegean Coast / Kordon", "lat": 38.4237, "lon": 27.1428},
        {"name": "Antalya Mediterranean Turquoise Coast", "lat": 36.8969, "lon": 30.7133},
    ],
    "iraq": [
        {"name": "Baghdad Tigris River / Tahrir", "lat": 33.3152, "lon": 44.3661},
        {"name": "Basra Shatt al-Arab Port", "lat": 30.5081, "lon": 47.7835},
        {"name": "Erbil Citadel / Kurdistan Hub", "lat": 36.1901, "lon": 44.0091},
        {"name": "Sulaymaniyah Zagros Mountains", "lat": 35.5558, "lon": 45.4351},
        {"name": "Mosul Ninawa Historic City", "lat": 36.3400, "lon": 43.1300},
        {"name": "Najaf Shrine Oasis", "lat": 32.0000, "lon": 44.3300},
        {"name": "Karbala Euphrates Basin", "lat": 32.6160, "lon": 44.0249},
    ],
    "israel": [
        {"name": "Tel Aviv Mediterranean Promenade", "lat": 32.0853, "lon": 34.7818},
        {"name": "Jerusalem Old City / Judean Hills", "lat": 31.7683, "lon": 35.2137},
        {"name": "Haifa Mount Carmel Bay", "lat": 32.7940, "lon": 34.9896},
        {"name": "Beersheba Negev Desert Hub", "lat": 31.2529, "lon": 34.7915},
        {"name": "Eilat Red Sea Gulf", "lat": 29.5577, "lon": 34.9519},
        {"name": "Nazareth Galilee Hills", "lat": 32.7000, "lon": 35.3000},
    ],
    "syria": [
        {"name": "Damascus Old City / Mount Qasioun", "lat": 33.5138, "lon": 36.2765},
        {"name": "Aleppo Citadel / Northern Hub", "lat": 36.2021, "lon": 37.1343},
        {"name": "Homs Orontes Valley", "lat": 34.7324, "lon": 36.7137},
        {"name": "Latakia Mediterranean Coast", "lat": 35.5317, "lon": 35.7901},
        {"name": "Tartus Coastal Port", "lat": 34.8890, "lon": 35.8866},
        {"name": "Hama Orontes Waterwheels", "lat": 35.1318, "lon": 36.7578},
    ],
    "yemen": [
        {"name": "Sana'a Old City / Sarawat Highlands", "lat": 15.3694, "lon": 44.1910},
        {"name": "Aden Crater / Gulf of Aden Port", "lat": 12.7855, "lon": 45.0187},
        {"name": "Taiz Jebel Saber Foothills", "lat": 13.5795, "lon": 44.0209},
        {"name": "Al Hodeidah Red Sea Coast", "lat": 14.7978, "lon": 42.9545},
        {"name": "Al Mukalla Hadhramaut Coast", "lat": 14.5425, "lon": 49.1242},
        {"name": "Ibb Highland Terraces", "lat": 13.9750, "lon": 44.1750},
        {"name": "Shibam Hadhramaut Mud Skyscraper Oasis", "lat": 15.9265, "lon": 48.6258},
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

# Register title-cased keys for case-insensitive lookup
for _k, _v in list(COUNTRY_BBOXES.items()):
    if _k.title() not in COUNTRY_BBOXES:
        COUNTRY_BBOXES[_k.title()] = _v

for _k, _v in list(COUNTRY_ANCHORS.items()):
    if _k.title() not in COUNTRY_ANCHORS:
        COUNTRY_ANCHORS[_k.title()] = _v


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

    # 2. High-precision border disambiguation for Middle East & Arabian Peninsula
    # Bahrain (Island nation in Persian Gulf)
    if 25.7 <= lat <= 26.4 and 50.3 <= lon <= 50.7:
        return "Bahrain"

    # Qatar (Peninsula)
    if 24.4 <= lat <= 26.3 and 50.7 <= lon <= 51.7:
        return "Qatar"

    # Kuwait (Northwest Persian Gulf)
    if 28.5 <= lat <= 30.2 and 46.5 <= lon <= 48.6:
        return "Kuwait"

    # UAE (North of Oman/Saudi, excluding Musandam tip)
    if 22.6 <= lat <= 26.1 and 51.5 <= lon <= 56.4:
        if lat > 25.8 and lon > 56.1:  # Musandam peninsula tip is Oman
            return "Oman"
        return "United Arab Emirates"

    # Oman (Southeast Arabia & Musandam exclave)
    if 16.6 <= lat <= 26.5 and 52.0 <= lon <= 59.9:
        return "Oman"

    # Yemen (South Arabia)
    if 12.1 <= lat <= 19.0 and 41.8 <= lon <= 54.6:
        return "Yemen"

    # Israel / Levant
    if 29.4 <= lat <= 33.4 and 34.2 <= lon <= 35.9:
        return "Israel"

    # Syria
    if 32.3 <= lat <= 37.4 and 35.6 <= lon <= 42.4:
        return "Syria"

    # Iraq
    if 29.0 <= lat <= 37.4 and 38.7 <= lon <= 48.6:
        return "Iraq"

    # Iran (North & East of Persian Gulf & Gulf of Oman)
    if (
        (lat >= 29.5 and 48.5 <= lon <= 63.4) or
        (lat >= 26.5 and 50.5 <= lon <= 63.4) or
        (lat >= 25.0 and 56.5 <= lon <= 63.4) or
        (lat >= 30.0 and 44.0 <= lon <= 63.4)
    ) and lat <= 39.8:
        return "Iran"

    # Saudi Arabia (Core Arabian Peninsula)
    if (
        (16.3 <= lat <= 32.2 and 34.5 <= lon <= 50.3) or
        (16.3 <= lat <= 24.5 and 50.3 < lon <= 55.7)  # Rub' al Khali in the south
    ):
        return "Saudi Arabia"

    # Turkey / Turkiye
    if 35.8 <= lat <= 42.1 and 25.6 <= lon <= 44.8:
        return "Turkey"

    # Egypt
    if 22.0 <= lat <= 31.7 and 24.7 <= lon <= 36.9:
        return "Egypt"

    # 3. General bounding box table
    for country, bbox in COUNTRY_BBOXES.items():
        if country in (
            "pakistan", "india", "nepal", "bangladesh", "sri lanka",
            "bahrain", "qatar", "kuwait", "united arab emirates", "oman",
            "yemen", "israel", "syria", "iraq", "saudi arabia", "iran",
            "turkey", "turkiye", "egypt"
        ):
            continue
        if point_in_bbox(lat, lon, bbox):
            return country.title()
    return None


class SubnationalDivision(dict):
    """Subnational division metadata supporting both dictionary access and string representation."""

    def __str__(self) -> str:
        div = self.get("division", "")
        dist = self.get("district", "")
        if div and dist and dist.lower() not in div.lower():
            return f"{div} ({dist})"
        return div or dist

    def lower(self) -> str:
        return str(self).lower()


def get_subnational_division(lat: float, lon: float) -> Optional[SubnationalDivision]:
    """Resolve GPS coordinates to province/governorate/state and major district for the 15 priority nations."""
    # Pakistan
    if 23.6 <= lat <= 37.1 and 60.8 <= lon <= 75.3:
        if 33.64 <= lat <= 33.80 and 72.90 <= lon <= 73.25:
            return SubnationalDivision({"country": "Pakistan", "division": "Islamabad Capital Territory", "district": "Islamabad"})
        if 33.80 < lat <= 34.15 and 73.30 <= lon <= 73.55:
            return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Murree / Galyat"})
        if 33.40 <= lat < 33.64 and 72.85 <= lon <= 73.20:
            return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Rawalpindi"})
        if 31.30 <= lat <= 31.75 and 74.15 <= lon <= 74.55:
            return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Lahore"})
        if 33.90 <= lat <= 34.20 and 71.40 <= lon <= 71.70:
            return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Peshawar"})
        if 34.05 <= lat <= 34.35 and 73.10 <= lon <= 73.40:
            return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Abbottabad / Hazara"})
        if 34.15 <= lat <= 34.45 and 73.40 <= lon <= 73.65:
            return SubnationalDivision({"country": "Pakistan", "division": "Azad Kashmir", "district": "Muzaffarabad"})
        if 24.70 <= lat <= 25.15 and 66.85 <= lon <= 67.35:
            return SubnationalDivision({"country": "Pakistan", "division": "Sindh", "district": "Karachi"})
        if 30.05 <= lat <= 30.35 and 66.85 <= lon <= 67.15:
            return SubnationalDivision({"country": "Pakistan", "division": "Balochistan", "district": "Quetta"})
        if 35.75 <= lat <= 36.10 and 74.15 <= lon <= 74.50:
            return SubnationalDivision({"country": "Pakistan", "division": "Gilgit-Baltistan", "district": "Gilgit"})

    # United Arab Emirates
    if 22.6 <= lat <= 26.1 and 51.5 <= lon <= 56.4:
        if 25.32 <= lat <= 25.48 and 55.35 <= lon <= 55.60:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Sharjah", "district": "Sharjah"})
        if 24.95 <= lat < 25.32 and 55.05 <= lon <= 55.45:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Dubai", "district": "Dubai"})
        if 24.30 <= lat <= 24.60 and 54.25 <= lon <= 54.70:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Abu Dhabi", "district": "Abu Dhabi"})
        if 24.05 <= lat <= 24.35 and 55.60 <= lon <= 55.90:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Abu Dhabi", "district": "Al Ain"})
        if 25.65 <= lat <= 25.95 and 55.80 <= lon <= 56.10:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Ras Al Khaimah", "district": "Ras Al Khaimah"})
        if 25.05 <= lat <= 25.25 and 56.25 <= lon <= 56.40:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Fujairah", "district": "Fujairah"})

    # Qatar
    if 24.4 <= lat <= 26.3 and 50.7 <= lon <= 51.7:
        if 25.20 <= lat <= 25.40 and 51.45 <= lon <= 51.60:
            return SubnationalDivision({"country": "Qatar", "division": "Doha Municipality", "district": "Doha"})
        if 25.38 <= lat <= 25.50 and 51.45 <= lon <= 51.55:
            return SubnationalDivision({"country": "Qatar", "division": "Al Daayen", "district": "Lusail"})
        if 25.10 <= lat <= 25.25 and 51.55 <= lon <= 51.65:
            return SubnationalDivision({"country": "Qatar", "division": "Al Wakrah Municipality", "district": "Al Wakrah"})
        if 25.60 <= lat <= 25.75 and 51.45 <= lon <= 51.58:
            return SubnationalDivision({"country": "Qatar", "division": "Al Khor Municipality", "district": "Al Khor"})

    # Saudi Arabia
    if 16.3 <= lat <= 32.2 and 34.5 <= lon <= 55.7:
        if 24.55 <= lat <= 24.90 and 46.55 <= lon <= 46.85:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Riyadh Province", "district": "Riyadh"})
        if 21.40 <= lat <= 21.75 and 39.05 <= lon <= 39.30:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Makkah Province", "district": "Jeddah"})
        if 21.30 <= lat <= 21.50 and 39.75 <= lon <= 39.95:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Makkah Province", "district": "Makkah"})
        if 24.40 <= lat <= 24.60 and 39.50 <= lon <= 39.70:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Madinah Province", "district": "Madinah"})
        if 26.30 <= lat <= 26.55 and 50.00 <= lon <= 50.25:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Eastern Province", "district": "Dammam / Khobar"})
        if 18.15 <= lat <= 18.35 and 42.45 <= lon <= 42.60:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Asir Province", "district": "Abha"})

    # Kuwait
    if 28.5 <= lat <= 30.2 and 46.5 <= lon <= 48.6:
        if 29.30 <= lat <= 29.45 and 47.90 <= lon <= 48.05:
            return SubnationalDivision({"country": "Kuwait", "division": "Capital Governorate (Al Asimah)", "district": "Kuwait City"})
        if 29.28 <= lat <= 29.38 and 48.02 <= lon <= 48.12:
            return SubnationalDivision({"country": "Kuwait", "division": "Hawalli Governorate", "district": "Salmiya / Hawalli"})
        if 29.00 <= lat <= 29.15 and 48.02 <= lon <= 48.15:
            return SubnationalDivision({"country": "Kuwait", "division": "Al Ahmadi Governorate", "district": "Al Ahmadi"})

    # Oman
    if 16.6 <= lat <= 26.5 and 52.0 <= lon <= 59.9:
        if 23.50 <= lat <= 23.70 and 58.30 <= lon <= 58.60:
            return SubnationalDivision({"country": "Oman", "division": "Muscat Governorate", "district": "Muscat"})
        if 16.95 <= lat <= 17.10 and 54.00 <= lon <= 54.20:
            return SubnationalDivision({"country": "Oman", "division": "Dhofar Governorate", "district": "Salalah"})

    # Egypt
    if 22.0 <= lat <= 31.7 and 24.7 <= lon <= 36.9:
        if 29.95 <= lat <= 30.15 and 31.15 <= lon <= 31.40:
            return SubnationalDivision({"country": "Egypt", "division": "Cairo Governorate", "district": "Cairo"})
        if 31.15 <= lat <= 31.30 and 29.85 <= lon <= 30.05:
            return SubnationalDivision({"country": "Egypt", "division": "Alexandria Governorate", "district": "Alexandria"})

    # Turkey
    if 35.8 <= lat <= 42.1 and 25.6 <= lon <= 44.8:
        if 40.90 <= lat <= 41.20 and 28.80 <= lon <= 29.20:
            return SubnationalDivision({"country": "Turkey", "division": "Istanbul Province", "district": "Istanbul"})
        if 39.85 <= lat <= 40.05 and 32.75 <= lon <= 33.00:
            return SubnationalDivision({"country": "Turkey", "division": "Ankara Province", "district": "Ankara"})
        if 38.35 <= lat <= 38.55 and 27.05 <= lon <= 27.25:
            return SubnationalDivision({"country": "Turkey", "division": "Izmir Province", "district": "Izmir"})
        if 36.80 <= lat <= 37.00 and 30.60 <= lon <= 30.80:
            return SubnationalDivision({"country": "Turkey", "division": "Antalya Province", "district": "Antalya"})

    # Iran
    if 25.0 <= lat <= 39.8 and 44.0 <= lon <= 63.4:
        if 35.60 <= lat <= 35.85 and 51.25 <= lon <= 51.55:
            return SubnationalDivision({"country": "Iran", "division": "Tehran Province", "district": "Tehran"})
        if 32.55 <= lat <= 32.75 and 51.55 <= lon <= 51.75:
            return SubnationalDivision({"country": "Iran", "division": "Isfahan Province", "district": "Isfahan"})
        if 29.50 <= lat <= 29.75 and 52.45 <= lon <= 52.70:
            return SubnationalDivision({"country": "Iran", "division": "Fars Province", "district": "Shiraz"})

    # Iraq
    if 29.0 <= lat <= 37.4 and 38.7 <= lon <= 48.6:
        if 33.25 <= lat <= 33.45 and 44.25 <= lon <= 44.45:
            return SubnationalDivision({"country": "Iraq", "division": "Baghdad Governorate", "district": "Baghdad"})
        if 36.10 <= lat <= 36.25 and 43.90 <= lon <= 44.10:
            return SubnationalDivision({"country": "Iraq", "division": "Erbil Governorate", "district": "Erbil"})

    # Israel
    if 29.4 <= lat <= 33.4 and 34.2 <= lon <= 35.9:
        if 32.00 <= lat <= 32.15 and 34.70 <= lon <= 34.85:
            return SubnationalDivision({"country": "Israel", "division": "Tel Aviv District", "district": "Tel Aviv"})
        if 31.70 <= lat <= 31.85 and 35.15 <= lon <= 35.30:
            return SubnationalDivision({"country": "Israel", "division": "Jerusalem District", "district": "Jerusalem"})

    # Bahrain
    if 25.7 <= lat <= 26.4 and 50.3 <= lon <= 50.7:
        return SubnationalDivision({"country": "Bahrain", "division": "Capital Governorate", "district": "Manama"})

    # Syria
    if 32.3 <= lat <= 37.4 and 35.6 <= lon <= 42.4:
        if 33.45 <= lat <= 33.55 and 36.20 <= lon <= 36.35:
            return SubnationalDivision({"country": "Syria", "division": "Damascus Governorate", "district": "Damascus"})
        if 36.15 <= lat <= 36.25 and 37.10 <= lon <= 37.20:
            return SubnationalDivision({"country": "Syria", "division": "Aleppo Governorate", "district": "Aleppo"})

    # Yemen
    if 12.1 <= lat <= 19.0 and 41.8 <= lon <= 54.6:
        if 15.30 <= lat <= 15.45 and 44.15 <= lon <= 44.25:
            return SubnationalDivision({"country": "Yemen", "division": "Amanat Al Asimah", "district": "Sanaa"})
        if 12.75 <= lat <= 12.85 and 44.95 <= lon <= 45.05:
            return SubnationalDivision({"country": "Yemen", "division": "Aden Governorate", "district": "Aden"})

    # India
    if 8.0 <= lat <= 35.5 and 68.1 <= lon <= 97.4:
        if 28.45 <= lat <= 28.85 and 76.95 <= lon <= 77.35:
            return SubnationalDivision({"country": "India", "division": "National Capital Territory of Delhi", "district": "Delhi"})
        if 18.90 <= lat <= 19.25 and 72.75 <= lon <= 73.05:
            return SubnationalDivision({"country": "India", "division": "Maharashtra", "district": "Mumbai"})
        if 12.85 <= lat <= 13.10 and 77.50 <= lon <= 77.75:
            return SubnationalDivision({"country": "India", "division": "Karnataka", "district": "Bengaluru"})

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
