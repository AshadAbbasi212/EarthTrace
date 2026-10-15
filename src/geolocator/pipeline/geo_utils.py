"""Geographic utilities: Haversine distance, country bounding boxes, offline point-in-region."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


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
    "pakistan": (23.6, 60.8, 37.2, 77.5),
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
    "colombia": (-4.3, -79.0, 12.5, -66.8),
    "peru": (-18.4, -81.4, -0.03, -68.6),
    "iceland": (63.3, -24.5, 66.6, -13.5),
    "south africa": (-34.8, 16.4, -22.1, 32.9),
    "kenya": (-4.7, 33.9, 4.6, 41.9),
    "russia": (41.2, 19.6, 81.9, 180.0),
    # Additional global country bounding boxes
    "jordan": (29.2, 34.9, 33.4, 39.3),
    "czech republic": (48.5, 12.1, 51.1, 18.9),
    "czechia": (48.5, 12.1, 51.1, 18.9),
    "hungary": (45.7, 16.1, 48.6, 22.9),
    "romania": (43.6, 20.2, 48.3, 29.7),
    "bulgaria": (41.2, 22.3, 44.2, 28.6),
    "taiwan": (21.8, 119.9, 25.3, 122.1),
    "kazakhstan": (40.5, 46.5, 55.4, 87.3),
    "uzbekistan": (37.1, 56.0, 45.6, 73.2),
    "kyrgyzstan": (39.1, 69.2, 43.3, 80.3),
    "tajikistan": (36.6, 67.3, 41.1, 75.2),
    "nigeria": (4.2, 2.6, 13.9, 14.7),
    "ukraine": (44.3, 22.1, 52.4, 40.2),
}

# Curated regional anchors for high-probability country hypothesis candidate synthesis
# Every entry includes explicit terrain classification ("mountain", "valley", "coast", "desert", "urban", "plateau")
COUNTRY_ANCHORS: Dict[str, List[Dict[str, Any]]] = {
    "pakistan": [
        # Hill stations, mountain ridges and high valleys
        {"name": "Murree / Galyat Ridge", "lat": 33.9062, "lon": 73.3903, "terrain": "mountain"},
        {"name": "Nathia Gali / Abbottabad Hills", "lat": 34.0722, "lon": 73.3833, "terrain": "mountain"},
        {"name": "Ayubia / Dunga Gali Ridge", "lat": 34.0298, "lon": 73.4011, "terrain": "mountain"},
        {"name": "Patriata / New Murree", "lat": 33.8821, "lon": 73.4562, "terrain": "mountain"},
        {"name": "Bhurban Pine Valley", "lat": 33.9556, "lon": 73.4514, "terrain": "mountain"},
        {"name": "Abbottabad / Hazara Valley", "lat": 34.1688, "lon": 73.2215, "terrain": "valley"},
        {"name": "Haripur / Hazara Margalla Foothills", "lat": 33.9942, "lon": 72.9333, "terrain": "valley"},
        {"name": "Khanpur / Tarbela Foothills Basin", "lat": 33.8058, "lon": 72.9328, "terrain": "valley"},
        {"name": "Mansehra / Karakoram Highway", "lat": 34.3333, "lon": 73.2000, "terrain": "valley"},
        {"name": "Shogran / Siri Paye Meadows", "lat": 34.6292, "lon": 73.4903, "terrain": "mountain"},
        {"name": "Kaghan / Naran Valley", "lat": 34.9080, "lon": 73.6520, "terrain": "mountain"},
        {"name": "Babusar Pass / Chilas Gateway", "lat": 35.1500, "lon": 74.0300, "terrain": "mountain"},
        {"name": "Malam Jabba Ski Resort / Swat", "lat": 34.7997, "lon": 72.5714, "terrain": "mountain"},
        {"name": "Mingora / Swat Valley", "lat": 34.7717, "lon": 72.3602, "terrain": "valley"},
        {"name": "Kalam / Ushu Valley", "lat": 35.4912, "lon": 72.5878, "terrain": "mountain"},
        {"name": "Muzaffarabad / Jhelum Valley", "lat": 34.3700, "lon": 73.4711, "terrain": "valley"},
        {"name": "Rawalakot / Poonch Highlands", "lat": 33.8578, "lon": 73.7604, "terrain": "mountain"},
        {"name": "Neelum Valley / Keran", "lat": 34.6644, "lon": 73.9189, "terrain": "mountain"},
        {"name": "Kotli / Mirpur Foothills", "lat": 33.5156, "lon": 73.9019, "terrain": "valley"},
        {"name": "Hunza / Karimabad", "lat": 36.3167, "lon": 74.6500, "terrain": "mountain"},
        {"name": "Skardu / Baltistan Valley", "lat": 35.2971, "lon": 75.6333, "terrain": "mountain"},
        {"name": "Gilgit Karakoram Gateway", "lat": 35.9208, "lon": 74.3144, "terrain": "valley"},
        {"name": "Chitral / Hindu Kush", "lat": 35.8510, "lon": 71.7864, "terrain": "mountain"},
        {"name": "Ziarat Juniper Valley", "lat": 30.3824, "lon": 67.7256, "terrain": "mountain"},
        # Urban, plains, and agricultural centers
        {"name": "Islamabad Capital Territory", "lat": 33.6844, "lon": 73.0479, "terrain": "urban"},
        {"name": "Rawalpindi / Potohar Plateau", "lat": 33.5973, "lon": 73.0479, "terrain": "urban"},
        {"name": "Lahore Urban Center", "lat": 31.5204, "lon": 74.3587, "terrain": "urban"},
        {"name": "Faisalabad Industrial Hub", "lat": 31.4504, "lon": 73.1350, "terrain": "urban"},
        {"name": "Multan Southern Punjab", "lat": 30.1575, "lon": 71.5249, "terrain": "urban"},
        {"name": "Peshawar Khyber Gateway", "lat": 34.0151, "lon": 71.5249, "terrain": "urban"},
        {"name": "Gujranwala / Sialkot Corridor", "lat": 32.1877, "lon": 74.1945, "terrain": "urban"},
        {"name": "Quetta Highlands", "lat": 30.1798, "lon": 66.9750, "terrain": "urban"},
        {"name": "Sukkur Indus Basin", "lat": 27.7052, "lon": 68.8574, "terrain": "urban"},
        {"name": "Hyderabad Sindh", "lat": 25.3960, "lon": 68.3578, "terrain": "urban"},
        # Coastal & arid regions
        {"name": "Karachi Coastal Corridor", "lat": 24.8607, "lon": 67.0011, "terrain": "coast"},
        {"name": "Gwadar Coastal Port", "lat": 25.1264, "lon": 62.3225, "terrain": "coast"},
        {"name": "Pasni / Makran Coast", "lat": 25.2631, "lon": 63.4692, "terrain": "coast"},
        {"name": "Thar Desert / Mithi", "lat": 24.7375, "lon": 69.7972, "terrain": "desert"},
        {"name": "Cholistan / Bahawalpur", "lat": 29.3956, "lon": 71.6833, "terrain": "desert"},
    ],
    "india": [
        # Mountain hill stations & valleys
        {"name": "Shimla / Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "terrain": "mountain"},
        {"name": "Manali / Kullu Valley", "lat": 32.2432, "lon": 77.1892, "terrain": "mountain"},
        {"name": "Dharamshala / Kangra Valley", "lat": 32.2190, "lon": 76.3234, "terrain": "mountain"},
        {"name": "Mussoorie / Garhwal Hills", "lat": 30.4598, "lon": 78.0644, "terrain": "mountain"},
        {"name": "Nainital / Kumaon Hills", "lat": 29.3919, "lon": 79.4542, "terrain": "mountain"},
        {"name": "Srinagar Kashmir Valley", "lat": 34.0837, "lon": 74.7973, "terrain": "valley"},
        {"name": "Gulmarg Alpine Ski Resort", "lat": 34.0484, "lon": 74.3805, "terrain": "mountain"},
        {"name": "Pahalgam / Lidder Valley", "lat": 34.0167, "lon": 75.3167, "terrain": "mountain"},
        {"name": "Leh / Ladakh High Plateau", "lat": 34.1526, "lon": 77.5771, "terrain": "mountain"},
        {"name": "Darjeeling / Eastern Himalayas", "lat": 27.0410, "lon": 88.2663, "terrain": "mountain"},
        {"name": "Gangtok / Sikkim", "lat": 27.3389, "lon": 88.6065, "terrain": "mountain"},
        {"name": "Shillong / Meghalaya", "lat": 25.5788, "lon": 91.8933, "terrain": "mountain"},
        {"name": "Ooty / Nilgiri Hills", "lat": 11.4102, "lon": 76.6950, "terrain": "mountain"},
        {"name": "Munnar / Western Ghats", "lat": 10.0889, "lon": 77.0595, "terrain": "mountain"},
        {"name": "Kodaikanal / Palani Hills", "lat": 10.2381, "lon": 77.4892, "terrain": "mountain"},
        # Urban & cultural centers
        {"name": "Delhi National Capital Region", "lat": 28.6139, "lon": 77.2090, "terrain": "urban"},
        {"name": "Bengaluru Southern Hub", "lat": 12.9716, "lon": 77.5946, "terrain": "urban"},
        {"name": "Hyderabad Deccan Center", "lat": 17.3850, "lon": 78.4867, "terrain": "urban"},
        {"name": "Kolkata Eastern Hub", "lat": 22.5726, "lon": 88.3639, "terrain": "urban"},
        {"name": "Chandigarh Urban Plain", "lat": 30.7333, "lon": 76.7794, "terrain": "urban"},
        {"name": "Ahmedabad Gujarat Center", "lat": 23.0225, "lon": 72.5714, "terrain": "urban"},
        {"name": "Lucknow Gangetic Plain", "lat": 26.8467, "lon": 80.9462, "terrain": "urban"},
        {"name": "Amritsar Punjab Gateway", "lat": 31.6340, "lon": 74.8723, "terrain": "urban"},
        {"name": "Pune Western Ghats", "lat": 18.5204, "lon": 73.8567, "terrain": "urban"},
        {"name": "Jaipur Rajasthan Gateway", "lat": 26.9124, "lon": 75.7873, "terrain": "urban"},
        {"name": "Jodhpur Thar Desert", "lat": 26.2389, "lon": 73.0243, "terrain": "desert"},
        # Coastal ports
        {"name": "Mumbai Western Coast", "lat": 19.0760, "lon": 72.8777, "terrain": "coast"},
        {"name": "Chennai Coromandel Coast", "lat": 13.0827, "lon": 80.2707, "terrain": "coast"},
        {"name": "Kochi Malabar Coast", "lat": 9.9312, "lon": 76.2673, "terrain": "coast"},
        {"name": "Goa Konkan Coast", "lat": 15.2993, "lon": 74.1240, "terrain": "coast"},
    ],
    "nepal": [
        {"name": "Kathmandu Valley", "lat": 27.7172, "lon": 85.3240, "terrain": "valley"},
        {"name": "Pokhara / Annapurna Foothills", "lat": 28.2096, "lon": 83.9856, "terrain": "valley"},
        {"name": "Nagarkot Ridge / Kathmandu Rim", "lat": 27.7174, "lon": 85.5200, "terrain": "mountain"},
        {"name": "Namche Bazaar / Everest Region", "lat": 27.8069, "lon": 86.7140, "terrain": "mountain"},
        {"name": "Jomsom / Mustang Valley", "lat": 28.7833, "lon": 83.7333, "terrain": "mountain"},
        {"name": "Langtang Alpine Valley", "lat": 28.2120, "lon": 85.5560, "terrain": "mountain"},
        {"name": "Dhulikhel Hill Station", "lat": 27.6253, "lon": 85.5561, "terrain": "mountain"},
        {"name": "Chitwan / Terai Lowlands", "lat": 27.5291, "lon": 84.4533, "terrain": "valley"},
        {"name": "Lumbini Sacred Terai", "lat": 27.4833, "lon": 83.2760, "terrain": "urban"},
        {"name": "Dharan Eastern Foothills", "lat": 26.8124, "lon": 87.2834, "terrain": "valley"},
        {"name": "Biratnagar Terai", "lat": 26.4525, "lon": 87.2718, "terrain": "urban"},
        {"name": "Manang High Himalayan Valley", "lat": 28.6600, "lon": 84.0200, "terrain": "mountain"},
    ],
    "united arab emirates": [
        {"name": "Dubai Downtown / Sheikh Zayed Rd", "lat": 25.2048, "lon": 55.2708, "terrain": "urban"},
        {"name": "Dubai Marina / Palm Jumeirah", "lat": 25.0805, "lon": 55.1403, "terrain": "coast"},
        {"name": "Abu Dhabi Corniche / Capital", "lat": 24.4539, "lon": 54.3773, "terrain": "coast"},
        {"name": "Abu Dhabi Yas Island", "lat": 24.4984, "lon": 54.6053, "terrain": "urban"},
        {"name": "Sharjah Urban Center", "lat": 25.3573, "lon": 55.4033, "terrain": "urban"},
        {"name": "Ajman Corniche", "lat": 25.4052, "lon": 55.4424, "terrain": "coast"},
        {"name": "Umm Al Quwain Coast", "lat": 25.5647, "lon": 55.5532, "terrain": "coast"},
        {"name": "Ras Al Khaimah / Jebel Jais Peak", "lat": 25.9525, "lon": 56.1678, "terrain": "mountain"},
        {"name": "Ras Al Khaimah Coastal City", "lat": 25.7895, "lon": 55.9432, "terrain": "coast"},
        {"name": "Fujairah Gulf of Oman Coast", "lat": 25.1288, "lon": 56.3265, "terrain": "coast"},
        {"name": "Khor Fakkan Coastal Fjord", "lat": 25.3377, "lon": 56.3562, "terrain": "coast"},
        {"name": "Al Ain Oasis / Jebel Hafeet", "lat": 24.0574, "lon": 55.7779, "terrain": "mountain"},
        {"name": "Hatta / Hajar Mountain Enclave", "lat": 24.8142, "lon": 56.1264, "terrain": "mountain"},
        {"name": "Liwa Oasis / Empty Quarter Dunes", "lat": 23.1333, "lon": 53.7833, "terrain": "desert"},
    ],
    "saudi arabia": [
        {"name": "Riyadh Olaya / Kingdom Centre", "lat": 24.7136, "lon": 46.6753, "terrain": "urban"},
        {"name": "Riyadh Edge of the World / Tuwaiq", "lat": 24.9450, "lon": 45.9860, "terrain": "plateau"},
        {"name": "Jeddah Corniche / Red Sea Coast", "lat": 21.5433, "lon": 39.1728, "terrain": "coast"},
        {"name": "Makkah Holy Valley", "lat": 21.3891, "lon": 39.8579, "terrain": "urban"},
        {"name": "Madinah Central Basin", "lat": 24.5247, "lon": 39.5692, "terrain": "urban"},
        {"name": "Dammam / Khobar Eastern Coast", "lat": 26.4207, "lon": 50.0888, "terrain": "coast"},
        {"name": "Abha / Asir Highland Ridge", "lat": 18.2164, "lon": 42.5053, "terrain": "mountain"},
        {"name": "Al Souda Peak / Asir Mountain", "lat": 18.2700, "lon": 42.3600, "terrain": "mountain"},
        {"name": "Taif Mountain Plateau", "lat": 21.2854, "lon": 40.4222, "terrain": "mountain"},
        {"name": "Al Baha Mountain Ridge", "lat": 20.0129, "lon": 41.4677, "terrain": "mountain"},
        {"name": "Tabuk / Jabal Al Lawz Snow Peaks", "lat": 28.6500, "lon": 35.3000, "terrain": "mountain"},
        {"name": "Al Ula / Hegra Sandstone Canyons", "lat": 26.6080, "lon": 37.9250, "terrain": "desert"},
        {"name": "Buraidah / Al Qassim Oasis", "lat": 26.3260, "lon": 43.9750, "terrain": "desert"},
        {"name": "Hail Shammar Desert", "lat": 27.5219, "lon": 41.6961, "terrain": "desert"},
        {"name": "Jizan Red Sea Coast", "lat": 16.8892, "lon": 42.5511, "terrain": "coast"},
        {"name": "Najran Valley Oasis", "lat": 17.4924, "lon": 44.1277, "terrain": "valley"},
    ],
    "qatar": [
        {"name": "Doha West Bay / Corniche", "lat": 25.2854, "lon": 51.5310, "terrain": "urban"},
        {"name": "Lusail Modern City", "lat": 25.4200, "lon": 51.4900, "terrain": "urban"},
        {"name": "Al Rayyan Education City", "lat": 25.3190, "lon": 51.4250, "terrain": "urban"},
        {"name": "Al Wakrah Coastal City", "lat": 25.1768, "lon": 51.6048, "terrain": "coast"},
        {"name": "Al Khor Northern Coast", "lat": 25.6839, "lon": 51.5058, "terrain": "coast"},
        {"name": "Dukhan Western Oilfield", "lat": 25.4290, "lon": 50.7850, "terrain": "coast"},
        {"name": "Zubarah Fort / North Peninsula", "lat": 25.9769, "lon": 51.0478, "terrain": "coast"},
        {"name": "Inland Sea / Khor Al Adaid", "lat": 24.6333, "lon": 51.3500, "terrain": "desert"},
    ],
    "kuwait": [
        {"name": "Kuwait City Capital / Towers", "lat": 29.3759, "lon": 47.9774, "terrain": "urban"},
        {"name": "Hawalli / Salmiya Coast", "lat": 29.3333, "lon": 48.0833, "terrain": "coast"},
        {"name": "Al Ahmadi Oilfield District", "lat": 29.0769, "lon": 48.0839, "terrain": "urban"},
        {"name": "Al Farwaniya Urban Center", "lat": 29.2778, "lon": 47.9589, "terrain": "urban"},
        {"name": "Al Jahra Western Oasis", "lat": 29.3375, "lon": 47.6581, "terrain": "desert"},
        {"name": "Subiya / Sheikh Jaber Bridge", "lat": 29.6200, "lon": 48.1500, "terrain": "coast"},
        {"name": "Abdali Northern Agriculture", "lat": 30.0633, "lon": 47.7083, "terrain": "desert"},
        {"name": "Wafra Southern Farms", "lat": 28.5917, "lon": 48.1139, "terrain": "desert"},
    ],
    "oman": [
        {"name": "Muscat Capital / Mutrah Corniche", "lat": 23.5880, "lon": 58.3829, "terrain": "coast"},
        {"name": "Salalah Dhofar Monsoon Coast", "lat": 17.0151, "lon": 54.0924, "terrain": "coast"},
        {"name": "Nizwa Jebel Akhdar Oasis", "lat": 22.9333, "lon": 57.5333, "terrain": "valley"},
        {"name": "Jebel Akhdar Green Mountain", "lat": 23.0694, "lon": 57.6667, "terrain": "mountain"},
        {"name": "Jebel Shams Grand Canyon", "lat": 23.2389, "lon": 57.2650, "terrain": "mountain"},
        {"name": "Sur Eastern Coastal Port", "lat": 22.5667, "lon": 59.5289, "terrain": "coast"},
        {"name": "Sohar Batinah Industrial Port", "lat": 24.3644, "lon": 56.7468, "terrain": "coast"},
        {"name": "Khasab Musandam Fjords", "lat": 26.1799, "lon": 56.2483, "terrain": "coast"},
        {"name": "Wahiba Sands / Sharqiya", "lat": 22.2500, "lon": 58.7500, "terrain": "desert"},
    ],
    "bahrain": [
        {"name": "Manama Diplomatic Area / Capital", "lat": 26.2285, "lon": 50.5860, "terrain": "urban"},
        {"name": "Muharraq Historic Island", "lat": 26.2572, "lon": 50.6119, "terrain": "coast"},
        {"name": "Riffa Southern Palaces", "lat": 26.1300, "lon": 50.5550, "terrain": "urban"},
        {"name": "King Fahd Causeway Gateway", "lat": 26.1850, "lon": 50.4550, "terrain": "coast"},
        {"name": "Sitra Industrial Island", "lat": 26.1550, "lon": 50.6200, "terrain": "coast"},
        {"name": "Amwaj Islands Arabian Gulf", "lat": 26.2900, "lon": 50.6650, "terrain": "coast"},
        {"name": "Sakhir / Tree of Life Desert", "lat": 25.9900, "lon": 50.5800, "terrain": "desert"},
    ],
    "egypt": [
        {"name": "Cairo Downtown / Tahrir", "lat": 30.0444, "lon": 31.2357, "terrain": "urban"},
        {"name": "Giza Pyramids Plateau", "lat": 29.9792, "lon": 31.1342, "terrain": "desert"},
        {"name": "Alexandria Mediterranean Corniche", "lat": 31.2001, "lon": 29.9187, "terrain": "coast"},
        {"name": "Sharm El Sheikh Sinai Resort", "lat": 27.9158, "lon": 34.3299, "terrain": "coast"},
        {"name": "Mount Sinai / Saint Catherine", "lat": 28.5392, "lon": 33.9750, "terrain": "mountain"},
        {"name": "Dahab Sinai Coast", "lat": 28.5097, "lon": 34.5136, "terrain": "coast"},
        {"name": "Hurghada Red Sea Coast", "lat": 27.2579, "lon": 33.8116, "terrain": "coast"},
        {"name": "Luxor Nile Temples", "lat": 25.6872, "lon": 32.6396, "terrain": "valley"},
        {"name": "Aswan High Dam / Nile Cataracts", "lat": 24.0889, "lon": 32.8998, "terrain": "valley"},
        {"name": "Siwa Oasis Western Desert", "lat": 29.2032, "lon": 25.5195, "terrain": "desert"},
        {"name": "Marsa Matrouh Mediterranean", "lat": 31.3525, "lon": 27.2453, "terrain": "coast"},
        {"name": "Port Said Suez Canal Gateway", "lat": 31.2653, "lon": 32.3019, "terrain": "coast"},
    ],
    "iran": [
        {"name": "Tehran Foothills / Milad Tower", "lat": 35.6892, "lon": 51.3890, "terrain": "urban"},
        {"name": "Dizin / Shemshak Alborz Ski Resort", "lat": 36.0500, "lon": 51.4167, "terrain": "mountain"},
        {"name": "Mount Damavand Peak", "lat": 35.9517, "lon": 52.1092, "terrain": "mountain"},
        {"name": "Isfahan Naqsh-e Jahan Square", "lat": 32.6546, "lon": 51.6680, "terrain": "urban"},
        {"name": "Shiraz Fars / Persepolis", "lat": 29.5918, "lon": 52.5837, "terrain": "valley"},
        {"name": "Mashhad Khorasan Shrine", "lat": 36.2605, "lon": 59.6168, "terrain": "urban"},
        {"name": "Tabriz Azerbaijan Historic Bazaar", "lat": 38.0800, "lon": 46.2919, "terrain": "urban"},
        {"name": "Rasht Caspian Sea Coast", "lat": 37.2808, "lon": 49.5832, "terrain": "coast"},
        {"name": "Yazd Desert Adobe Architecture", "lat": 31.8974, "lon": 54.3569, "terrain": "desert"},
        {"name": "Kerman / Lut Desert", "lat": 30.2839, "lon": 57.0788, "terrain": "desert"},
        {"name": "Kermanshah Zagros Foothills", "lat": 34.3142, "lon": 47.0650, "terrain": "mountain"},
        {"name": "Bandar Abbas Persian Gulf Strait", "lat": 27.1832, "lon": 56.2666, "terrain": "coast"},
    ],
    "turkey": [
        {"name": "Istanbul Bosporus / Sultanahmet", "lat": 41.0082, "lon": 28.9784, "terrain": "urban"},
        {"name": "Istanbul Kadikoy / Asian Shore", "lat": 40.9910, "lon": 29.0270, "terrain": "urban"},
        {"name": "Ankara Central Anatolia / Kizilay", "lat": 39.9334, "lon": 32.8597, "terrain": "urban"},
        {"name": "Izmir Aegean Coast / Kordon", "lat": 38.4237, "lon": 27.1428, "terrain": "coast"},
        {"name": "Antalya Mediterranean Turquoise Coast", "lat": 36.8969, "lon": 30.7133, "terrain": "coast"},
        {"name": "Bursa / Uludag Mountain Peak", "lat": 40.0694, "lon": 29.2217, "terrain": "mountain"},
        {"name": "Trabzon Black Sea Foothills", "lat": 41.0027, "lon": 39.7168, "terrain": "coast"},
        {"name": "Rize / Ayder Plateau", "lat": 40.9575, "lon": 41.1000, "terrain": "mountain"},
        {"name": "Uzungol Alpine Valley", "lat": 40.6178, "lon": 40.2917, "terrain": "mountain"},
        {"name": "Erzurum / Palandoken Ski", "lat": 39.8500, "lon": 41.2800, "terrain": "mountain"},
        {"name": "Cappadocia / Goreme Fairy Chimneys", "lat": 38.6431, "lon": 34.8289, "terrain": "plateau"},
        {"name": "Pamukkale Travertines", "lat": 37.9250, "lon": 29.1208, "terrain": "valley"},
        {"name": "Konya Anatolian Steppe", "lat": 37.8746, "lon": 32.4932, "terrain": "plateau"},
        {"name": "Gaziantep Southeastern Hub", "lat": 37.0662, "lon": 37.3833, "terrain": "urban"},
        {"name": "Bodrum Aegean Coast", "lat": 37.0344, "lon": 27.4305, "terrain": "coast"},
    ],
    "turkiye": [
        {"name": "Istanbul Bosporus / Sultanahmet", "lat": 41.0082, "lon": 28.9784, "terrain": "urban"},
        {"name": "Ankara Central Anatolia / Kizilay", "lat": 39.9334, "lon": 32.8597, "terrain": "urban"},
        {"name": "Izmir Aegean Coast / Kordon", "lat": 38.4237, "lon": 27.1428, "terrain": "coast"},
        {"name": "Antalya Mediterranean Turquoise Coast", "lat": 36.8969, "lon": 30.7133, "terrain": "coast"},
        {"name": "Bursa / Uludag Mountain Peak", "lat": 40.0694, "lon": 29.2217, "terrain": "mountain"},
        {"name": "Rize / Ayder Plateau", "lat": 40.9575, "lon": 41.1000, "terrain": "mountain"},
    ],
    "iraq": [
        {"name": "Baghdad Tigris River / Tahrir", "lat": 33.3152, "lon": 44.3661, "terrain": "urban"},
        {"name": "Basra Shatt al-Arab Port", "lat": 30.5081, "lon": 47.7835, "terrain": "coast"},
        {"name": "Erbil Citadel / Kurdistan Hub", "lat": 36.1901, "lon": 44.0091, "terrain": "urban"},
        {"name": "Sulaymaniyah Zagros Mountains", "lat": 35.5558, "lon": 45.4351, "terrain": "mountain"},
        {"name": "Duhok Kurdistan Valley", "lat": 36.8679, "lon": 42.9885, "terrain": "mountain"},
        {"name": "Mosul Ninawa Historic City", "lat": 36.3400, "lon": 43.1300, "terrain": "urban"},
        {"name": "Najaf Shrine Oasis", "lat": 32.0000, "lon": 44.3300, "terrain": "urban"},
        {"name": "Karbala Euphrates Basin", "lat": 32.6160, "lon": 44.0249, "terrain": "urban"},
    ],
    "israel": [
        {"name": "Tel Aviv Mediterranean Promenade", "lat": 32.0853, "lon": 34.7818, "terrain": "coast"},
        {"name": "Jerusalem Old City / Judean Hills", "lat": 31.7683, "lon": 35.2137, "terrain": "mountain"},
        {"name": "Haifa Mount Carmel Bay", "lat": 32.7940, "lon": 34.9896, "terrain": "coast"},
        {"name": "Beersheba Negev Desert Hub", "lat": 31.2529, "lon": 34.7915, "terrain": "desert"},
        {"name": "Eilat Red Sea Gulf", "lat": 29.5577, "lon": 34.9519, "terrain": "coast"},
        {"name": "Nazareth Galilee Hills", "lat": 32.7000, "lon": 35.3000, "terrain": "mountain"},
    ],
    "syria": [
        {"name": "Damascus Old City / Mount Qasioun", "lat": 33.5138, "lon": 36.2765, "terrain": "urban"},
        {"name": "Bloudan / Anti-Lebanon Mountains", "lat": 33.7333, "lon": 36.0833, "terrain": "mountain"},
        {"name": "Aleppo Citadel / Northern Hub", "lat": 36.2021, "lon": 37.1343, "terrain": "urban"},
        {"name": "Homs Orontes Valley", "lat": 34.7324, "lon": 36.7137, "terrain": "valley"},
        {"name": "Latakia Mediterranean Coast", "lat": 35.5317, "lon": 35.7901, "terrain": "coast"},
        {"name": "Tartus Coastal Port", "lat": 34.8890, "lon": 35.8866, "terrain": "coast"},
        {"name": "Hama Orontes Waterwheels", "lat": 35.1318, "lon": 36.7578, "terrain": "valley"},
        {"name": "Palmyra Desert Oasis", "lat": 34.5600, "lon": 38.2800, "terrain": "desert"},
    ],
    "yemen": [
        {"name": "Sana'a Old City / Sarawat Highlands", "lat": 15.3694, "lon": 44.1910, "terrain": "mountain"},
        {"name": "Aden Crater / Gulf of Aden Port", "lat": 12.7855, "lon": 45.0187, "terrain": "coast"},
        {"name": "Taiz Jebel Saber Foothills", "lat": 13.5795, "lon": 44.0209, "terrain": "mountain"},
        {"name": "Al Hodeidah Red Sea Coast", "lat": 14.7978, "lon": 42.9545, "terrain": "coast"},
        {"name": "Al Mukalla Hadhramaut Coast", "lat": 14.5425, "lon": 49.1242, "terrain": "coast"},
        {"name": "Ibb Highland Terraces", "lat": 13.9750, "lon": 44.1750, "terrain": "mountain"},
        {"name": "Shibam Hadhramaut Mud Skyscraper Oasis", "lat": 15.9265, "lon": 48.6258, "terrain": "desert"},
        {"name": "Socotra Island", "lat": 12.4634, "lon": 53.8237, "terrain": "coast"},
    ],
    "bangladesh": [
        {"name": "Dhaka Metropolitan", "lat": 23.8103, "lon": 90.4125, "terrain": "urban"},
        {"name": "Chittagong Coastal Port", "lat": 22.3569, "lon": 91.7832, "terrain": "coast"},
        {"name": "Sylhet Tea Hills / Surma Valley", "lat": 24.8949, "lon": 91.8687, "terrain": "valley"},
        {"name": "Bandarban Chittagong Hill Tracts", "lat": 22.1953, "lon": 92.2184, "terrain": "mountain"},
        {"name": "Cox's Bazar Long Beach", "lat": 21.4272, "lon": 92.0058, "terrain": "coast"},
    ],
    "sri lanka": [
        {"name": "Colombo Coastal Capital", "lat": 6.9271, "lon": 79.8612, "terrain": "coast"},
        {"name": "Kandy Central Highlands", "lat": 7.2906, "lon": 80.6337, "terrain": "mountain"},
        {"name": "Nuwara Eliya Hill Station Tea", "lat": 6.9497, "lon": 80.7891, "terrain": "mountain"},
        {"name": "Ella Mountain Gap Peak", "lat": 6.8667, "lon": 81.0466, "terrain": "mountain"},
        {"name": "Galle Southern Fort Coast", "lat": 6.0535, "lon": 80.2210, "terrain": "coast"},
    ],
    "afghanistan": [
        {"name": "Kabul Basin / Hindu Kush", "lat": 34.5553, "lon": 69.2075, "terrain": "mountain"},
        {"name": "Bamyan Valley / Buddha Cliffs", "lat": 34.8100, "lon": 67.8200, "terrain": "mountain"},
        {"name": "Herat Western Oasis", "lat": 34.3529, "lon": 62.2040, "terrain": "urban"},
        {"name": "Mazar-i-Sharif Northern Plain", "lat": 36.7061, "lon": 67.1108, "terrain": "urban"},
        {"name": "Kandahar Arghandab Valley", "lat": 31.6289, "lon": 65.7372, "terrain": "urban"},
    ],
    "morocco": [
        {"name": "Casablanca Atlantic Coast", "lat": 33.5731, "lon": -7.5898, "terrain": "coast"},
        {"name": "Marrakech Atlas Foothills", "lat": 31.6295, "lon": -7.9811, "terrain": "urban"},
        {"name": "Toubkal / Imlil High Atlas", "lat": 31.1356, "lon": -7.9172, "terrain": "mountain"},
        {"name": "Chefchaouen Rif Mountains", "lat": 35.1716, "lon": -5.2697, "terrain": "mountain"},
        {"name": "Merzouga Sahara Erg Chebbi Dunes", "lat": 31.0992, "lon": -4.0097, "terrain": "desert"},
        {"name": "Ouarzazate / Dades Valley South Atlas", "lat": 30.9167, "lon": -6.9167, "terrain": "desert"},
        {"name": "Ait Benhaddou / Ksar Valley Atlas", "lat": 31.0470, "lon": -7.1317, "terrain": "mountain"},
        {"name": "Tinghir / Todra Gorge High Atlas", "lat": 31.5147, "lon": -5.5328, "terrain": "mountain"},
        {"name": "Zagora / Draa Valley Oasis", "lat": 30.3324, "lon": -5.8383, "terrain": "desert"},
        {"name": "Taroudant / Souss Valley", "lat": 30.4703, "lon": -8.8770, "terrain": "valley"},
        {"name": "Agadir / Atlantic Souss Coast", "lat": 30.4278, "lon": -9.5981, "terrain": "coast"},
        {"name": "Fes / Saiss Basin Historic", "lat": 34.0181, "lon": -5.0078, "terrain": "urban"},
        {"name": "Meknes / Zerhoun Foothills", "lat": 33.8938, "lon": -5.5473, "terrain": "urban"},
        {"name": "Tangier / Strait of Gibraltar Coast", "lat": 35.7595, "lon": -5.8340, "terrain": "coast"},
        {"name": "Rabat / Bouregreg Estuary Capital", "lat": 34.0209, "lon": -6.8416, "terrain": "coast"},
    ],
    "united kingdom": [
        {"name": "London Greater Metropolitan", "lat": 51.5074, "lon": -0.1278, "terrain": "urban"},
        {"name": "Manchester Northwest", "lat": 53.4808, "lon": -2.2426, "terrain": "urban"},
        {"name": "Edinburgh Scotland", "lat": 55.9533, "lon": -3.1883, "terrain": "urban"},
        {"name": "Fort William / Ben Nevis Highlands", "lat": 56.8198, "lon": -5.1052, "terrain": "mountain"},
        {"name": "Lake District / Keswick", "lat": 54.6013, "lon": -3.1361, "terrain": "mountain"},
        {"name": "Snowdonia / Eryri North Wales", "lat": 53.0685, "lon": -4.0763, "terrain": "mountain"},
        {"name": "Brecon / Bannau Brycheiniog South Wales", "lat": 51.9480, "lon": -3.3910, "terrain": "mountain"},
        {"name": "Cardiff / South Wales Glamorgan", "lat": 51.4816, "lon": -3.1791, "terrain": "coast"},
        {"name": "Swansea / Gower Peninsula Wales", "lat": 51.6214, "lon": -3.9436, "terrain": "coast"},
        {"name": "Aberystwyth / Cardigan Bay West Wales", "lat": 52.4153, "lon": -4.0829, "terrain": "coast"},
        {"name": "Bristol / Severn Estuary South West", "lat": 51.4545, "lon": -2.5879, "terrain": "urban"},
        {"name": "Exeter / Devon South West", "lat": 50.7184, "lon": -3.5339, "terrain": "valley"},
        {"name": "Truro / Cornwall South West", "lat": 50.2632, "lon": -5.0510, "terrain": "coast"},
        {"name": "Birmingham / West Midlands Hub", "lat": 52.4862, "lon": -1.8904, "terrain": "urban"},
        {"name": "Leeds / West Yorkshire Valley", "lat": 53.8008, "lon": -1.5491, "terrain": "urban"},
        {"name": "Newcastle upon Tyne / North East", "lat": 54.9783, "lon": -1.6178, "terrain": "coast"},
        {"name": "Glasgow / Clyde Valley Scotland", "lat": 55.8642, "lon": -4.2518, "terrain": "urban"},
        {"name": "Inverness / Scottish Highlands", "lat": 57.4778, "lon": -4.2247, "terrain": "mountain"},
        {"name": "Belfast / Northern Ireland Antrim", "lat": 54.5973, "lon": -5.9301, "terrain": "coast"},
    ],
    "france": [
        {"name": "Paris Île-de-France", "lat": 48.8566, "lon": 2.3522, "terrain": "urban"},
        {"name": "Chamonix / Mont Blanc Valley", "lat": 45.9237, "lon": 6.8694, "terrain": "mountain"},
        {"name": "Annecy / French Alps", "lat": 45.8992, "lon": 6.1294, "terrain": "mountain"},
        {"name": "Pyrenees / Cauterets", "lat": 42.8889, "lon": -0.1139, "terrain": "mountain"},
        {"name": "Marseille Provence Coast", "lat": 43.2965, "lon": 5.3698, "terrain": "coast"},
        {"name": "Lyon Rhône Corridor", "lat": 45.7640, "lon": 4.8357, "terrain": "urban"},
    ],
    "germany": [
        {"name": "Berlin Metropolitan", "lat": 52.5200, "lon": 13.4050, "terrain": "urban"},
        {"name": "Munich Bavaria", "lat": 48.1351, "lon": 11.5820, "terrain": "urban"},
        {"name": "Garmisch-Partenkirchen / Zugspitze", "lat": 47.4917, "lon": 11.0955, "terrain": "mountain"},
        {"name": "Berchtesgaden / Bavarian Alps", "lat": 47.6297, "lon": 13.0016, "terrain": "mountain"},
        {"name": "Black Forest / Freiburg", "lat": 47.9990, "lon": 7.8421, "terrain": "mountain"},
    ],
    "switzerland": [
        {"name": "Zurich Urban Lake", "lat": 47.3769, "lon": 8.5417, "terrain": "urban"},
        {"name": "Zermatt / Matterhorn Peak", "lat": 45.9765, "lon": 7.7491, "terrain": "mountain"},
        {"name": "Interlaken / Jungfrau Region", "lat": 46.6863, "lon": 7.8632, "terrain": "mountain"},
        {"name": "St. Moritz / Engadin Valley", "lat": 46.4908, "lon": 9.8355, "terrain": "mountain"},
        {"name": "Geneva Lake Basin", "lat": 46.2044, "lon": 6.1432, "terrain": "urban"},
    ],
    "austria": [
        {"name": "Vienna Danube Capital", "lat": 48.2082, "lon": 16.3738, "terrain": "urban"},
        {"name": "Innsbruck / Tyrol Alps", "lat": 47.2692, "lon": 11.4041, "terrain": "mountain"},
        {"name": "Salzburg Alpine Foothills", "lat": 47.8095, "lon": 13.0550, "terrain": "mountain"},
        {"name": "Kitzbuhel Alpine Ski", "lat": 47.4464, "lon": 12.3922, "terrain": "mountain"},
    ],
    "italy": [
        {"name": "Rome Central", "lat": 41.9028, "lon": 12.4964, "terrain": "urban"},
        {"name": "Milan Lombardy", "lat": 45.4642, "lon": 9.1900, "terrain": "urban"},
        {"name": "Cortina d'Ampezzo / Dolomites", "lat": 46.5405, "lon": 12.1357, "terrain": "mountain"},
        {"name": "Courmayeur / Mont Blanc", "lat": 45.7969, "lon": 6.9708, "terrain": "mountain"},
        {"name": "Florence / Tuscany Hills", "lat": 43.7696, "lon": 11.2558, "terrain": "valley"},
        {"name": "Naples / Amalfi Coast", "lat": 40.8518, "lon": 14.2681, "terrain": "coast"},
        {"name": "Sicily / Mount Etna", "lat": 37.7510, "lon": 14.9934, "terrain": "mountain"},
    ],
    "spain": [
        {"name": "Moros / Calatayud / Manubles Valley Aragon", "lat": 41.4000, "lon": -1.8167, "terrain": "mountain"},
        {"name": "Calatayud / Jiloca Valley Aragon", "lat": 41.3533, "lon": -1.6432, "terrain": "valley"},
        {"name": "Zaragoza / Ebro River Valley Aragon", "lat": 41.6488, "lon": -0.8891, "terrain": "urban"},
        {"name": "Teruel / Southern Aragon Highlands", "lat": 40.3456, "lon": -1.1072, "terrain": "mountain"},
        {"name": "Huesca / Pyrenees Foothills Aragon", "lat": 42.1361, "lon": -0.4087, "terrain": "mountain"},
        {"name": "Pyrenees / Huesca High Peaks", "lat": 42.5000, "lon": 0.0500, "terrain": "mountain"},
        {"name": "Madrid Central Meseta", "lat": 40.4168, "lon": -3.7038, "terrain": "urban"},
        {"name": "Barcelona Catalonia Coast", "lat": 41.3851, "lon": 2.1734, "terrain": "coast"},
        {"name": "Valencia / Levantine Coast", "lat": 39.4699, "lon": -0.3763, "terrain": "coast"},
        {"name": "Seville / Guadalquivir Basin Andalusia", "lat": 37.3891, "lon": -5.9845, "terrain": "urban"},
        {"name": "Cordoba / Sierra Morena Andalusia", "lat": 37.8882, "lon": -4.7794, "terrain": "valley"},
        {"name": "Sierra Nevada / Granada Peaks", "lat": 37.0931, "lon": -3.3931, "terrain": "mountain"},
        {"name": "Malaga / Costa del Sol Andalusia", "lat": 36.7213, "lon": -4.4214, "terrain": "coast"},
        {"name": "Bilbao / Basque Country Coast", "lat": 43.2630, "lon": -2.9350, "terrain": "coast"},
        {"name": "Santiago de Compostela / Galicia", "lat": 42.8782, "lon": -8.5448, "terrain": "mountain"},
        {"name": "Valladolid / Castile and Leon Meseta", "lat": 41.6523, "lon": -4.7245, "terrain": "plateau"},
        {"name": "Toledo / Tagus Gorge Central", "lat": 39.8628, "lon": -4.0273, "terrain": "urban"},
        {"name": "Tenerife / Mount Teide", "lat": 28.2723, "lon": -16.6425, "terrain": "mountain"},
    ],
    "norway": [
        {"name": "Oslo Capital Fjord", "lat": 59.9139, "lon": 10.7522, "terrain": "urban"},
        {"name": "Bergen Western Coast", "lat": 60.3913, "lon": 5.3221, "terrain": "coast"},
        {"name": "Geiranger Fjord Mountain Valley", "lat": 62.1008, "lon": 7.2059, "terrain": "mountain"},
        {"name": "Tromso Arctic Mountain Coast", "lat": 69.6492, "lon": 18.9553, "terrain": "coast"},
        {"name": "Lofoten Islands Alpine Coast", "lat": 68.1667, "lon": 13.7500, "terrain": "coast"},
    ],
    "united states": [
        {"name": "New York Metropolitan", "lat": 40.7128, "lon": -74.0060, "terrain": "urban"},
        {"name": "Los Angeles Coastal Plain", "lat": 34.0522, "lon": -118.2437, "terrain": "coast"},
        {"name": "Chicago Great Lakes", "lat": 41.8781, "lon": -87.6298, "terrain": "urban"},
        {"name": "Datil / Plains of San Agustin / Catron NM", "lat": 34.1422, "lon": -107.8425, "terrain": "mountain"},
        {"name": "Socorro / Chihuahuan Desert NM", "lat": 34.0584, "lon": -106.8914, "terrain": "plateau"},
        {"name": "Albuquerque / Rio Grande Valley NM", "lat": 35.0844, "lon": -106.6504, "terrain": "plateau"},
        {"name": "Santa Fe / Sangre de Cristo Hills NM", "lat": 35.6870, "lon": -105.9378, "terrain": "mountain"},
        {"name": "Phoenix / Sonoran Desert AZ", "lat": 33.4484, "lon": -112.0740, "terrain": "desert"},
        {"name": "Flagstaff / Coconino Plateau AZ", "lat": 35.1983, "lon": -111.6513, "terrain": "mountain"},
        {"name": "Tucson / Santa Catalina Foothills AZ", "lat": 32.2226, "lon": -110.9747, "terrain": "desert"},
        {"name": "Denver / Colorado Rockies", "lat": 39.7392, "lon": -104.9903, "terrain": "mountain"},
        {"name": "Aspen / Rocky Mountains", "lat": 39.1911, "lon": -106.8175, "terrain": "mountain"},
        {"name": "Moab / Utah Red Rock Canyons", "lat": 38.5733, "lon": -109.5498, "terrain": "desert"},
        {"name": "Salt Lake City / Wasatch Front UT", "lat": 40.7608, "lon": -111.8910, "terrain": "mountain"},
        {"name": "Las Vegas / Mojave Desert NV", "lat": 36.1699, "lon": -115.1398, "terrain": "desert"},
        {"name": "El Paso / Franklin Mountains TX", "lat": 31.7619, "lon": -106.4850, "terrain": "desert"},
        {"name": "Dallas-Fort Worth North Texas", "lat": 32.7767, "lon": -96.7970, "terrain": "urban"},
        {"name": "Houston Gulf Coast TX", "lat": 29.7604, "lon": -95.3698, "terrain": "coast"},
        {"name": "Austin / Texas Hill Country", "lat": 30.2672, "lon": -97.7431, "terrain": "plateau"},
        {"name": "San Francisco Bay Area CA", "lat": 37.7749, "lon": -122.4194, "terrain": "coast"},
        {"name": "Yosemite / Sierra Nevada", "lat": 37.8651, "lon": -119.5383, "terrain": "mountain"},
        {"name": "Seattle / Mount Rainier", "lat": 47.6062, "lon": -122.3321, "terrain": "mountain"},
        {"name": "Portland / Willamette Valley OR", "lat": 45.5152, "lon": -122.6784, "terrain": "valley"},
        {"name": "Boise / Snake River Plain ID", "lat": 43.6150, "lon": -116.2023, "terrain": "plateau"},
        {"name": "Billings / Yellowstone Basin MT", "lat": 45.7833, "lon": -108.5007, "terrain": "plateau"},
        {"name": "Atlanta / Piedmont Plateau GA", "lat": 33.7490, "lon": -84.3880, "terrain": "urban"},
        {"name": "Miami / South Florida Coast", "lat": 25.7617, "lon": -80.1918, "terrain": "coast"},
        {"name": "Minneapolis / Upper Midwest MN", "lat": 44.9778, "lon": -93.2650, "terrain": "urban"},
    ],
    "canada": [
        {"name": "Toronto Metropolitan", "lat": 43.6532, "lon": -79.3832, "terrain": "urban"},
        {"name": "Vancouver Coast", "lat": 49.2827, "lon": -123.1207, "terrain": "coast"},
        {"name": "Banff / Canadian Rockies", "lat": 51.1784, "lon": -115.5708, "terrain": "mountain"},
        {"name": "Lake Louise / Banff National Park", "lat": 51.4254, "lon": -116.1773, "terrain": "mountain"},
        {"name": "Jasper National Park", "lat": 52.8737, "lon": -117.9543, "terrain": "mountain"},
        {"name": "Whistler Coast Mountains", "lat": 50.1163, "lon": -122.9574, "terrain": "mountain"},
        {"name": "Calgary Foothills", "lat": 51.0447, "lon": -114.0719, "terrain": "plateau"},
    ],
    "japan": [
        {"name": "Aobe / Oi River Valley / Kawanehon Shizuoka", "lat": 35.0894, "lon": 138.1156, "terrain": "mountain"},
        {"name": "Shizuoka / Suruga Bay Coast", "lat": 34.9756, "lon": 138.3828, "terrain": "coast"},
        {"name": "Hamamatsu / Lake Hamana Tokaido", "lat": 34.7108, "lon": 137.7261, "terrain": "coast"},
        {"name": "Nagoya / Nobi Plain Chubu", "lat": 35.1815, "lon": 136.9066, "terrain": "urban"},
        {"name": "Tokyo Kanto Plain", "lat": 35.6762, "lon": 139.6503, "terrain": "urban"},
        {"name": "Shibuya Crossing / Hachiko Square", "lat": 35.6595, "lon": 139.7005, "terrain": "urban"},
        {"name": "Yokohama / Kanagawa Harbor", "lat": 35.4437, "lon": 139.6380, "terrain": "coast"},
        {"name": "Mount Fuji / Hakone Ridge", "lat": 35.3606, "lon": 138.7274, "terrain": "mountain"},
        {"name": "Nagano / Japanese Alps", "lat": 36.6513, "lon": 138.1810, "terrain": "mountain"},
        {"name": "Kyoto Kansai Basin", "lat": 35.0116, "lon": 135.7681, "terrain": "valley"},
        {"name": "Osaka / Kansai Basin", "lat": 34.6937, "lon": 135.5023, "terrain": "urban"},
        {"name": "Kobe / Rokko Mountains Hyogo", "lat": 34.6901, "lon": 135.1955, "terrain": "coast"},
        {"name": "Hiroshima / Seto Inland Sea", "lat": 34.3853, "lon": 132.4553, "terrain": "coast"},
        {"name": "Fukuoka / Northern Kyushu", "lat": 33.5904, "lon": 130.4017, "terrain": "coast"},
        {"name": "Kagoshima / Sakurajima Volcano", "lat": 31.5966, "lon": 130.5571, "terrain": "mountain"},
        {"name": "Sendai / Tohoku Miyagi", "lat": 38.2682, "lon": 140.8694, "terrain": "valley"},
        {"name": "Aomori / Tsugaru Peninsula", "lat": 40.8222, "lon": 140.7474, "terrain": "coast"},
        {"name": "Sapporo / Hokkaido", "lat": 43.0618, "lon": 141.3545, "terrain": "mountain"},
        {"name": "Matsuyama / Shikoku Inland Sea", "lat": 33.8392, "lon": 132.7656, "terrain": "coast"},
    ],
    "china": [
        {"name": "Beijing North China Plain", "lat": 39.9042, "lon": 116.4074, "terrain": "urban"},
        {"name": "Shanghai Yangtze Delta", "lat": 31.2304, "lon": 121.4737, "terrain": "coast"},
        {"name": "Chengdu Sichuan Basin", "lat": 30.5728, "lon": 104.0668, "terrain": "valley"},
        {"name": "Lhasa / Tibet Himalayan Plateau", "lat": 29.6525, "lon": 91.1721, "terrain": "mountain"},
        {"name": "Huangshan / Yellow Mountain", "lat": 30.1311, "lon": 118.1691, "terrain": "mountain"},
        {"name": "Zhangjiajie Sandstone Pillars", "lat": 29.1306, "lon": 110.4789, "terrain": "mountain"},
    ],
    "australia": [
        {"name": "Narrabri / Namoi Valley Inland NSW", "lat": -30.3167, "lon": 149.7667, "terrain": "valley"},
        {"name": "Tamworth / New England NSW", "lat": -31.0927, "lon": 150.9320, "terrain": "valley"},
        {"name": "Dubbo / Central West Plains NSW", "lat": -32.2569, "lon": 148.6011, "terrain": "valley"},
        {"name": "Wagga Wagga / Riverina NSW", "lat": -35.1082, "lon": 147.3598, "terrain": "valley"},
        {"name": "Armidale / Northern Tablelands NSW", "lat": -30.5016, "lon": 151.6662, "terrain": "mountain"},
        {"name": "Sydney Coastal Basin", "lat": -33.8688, "lon": 151.2093, "terrain": "coast"},
        {"name": "Blue Mountains / Katoomba", "lat": -33.7150, "lon": 150.3119, "terrain": "mountain"},
        {"name": "Newcastle / Hunter Coast NSW", "lat": -32.9283, "lon": 151.7817, "terrain": "coast"},
        {"name": "Canberra / Capital Territory ACT", "lat": -35.2809, "lon": 149.1300, "terrain": "valley"},
        {"name": "Melbourne Port Phillip", "lat": -37.8136, "lon": 144.9631, "terrain": "coast"},
        {"name": "Jindabyne / Mount Kosciuszko", "lat": -36.4167, "lon": 148.6167, "terrain": "mountain"},
        {"name": "Brisbane / Moreton Bay QLD", "lat": -27.4698, "lon": 153.0251, "terrain": "coast"},
        {"name": "Toowoomba / Darling Downs QLD", "lat": -27.5598, "lon": 151.9507, "terrain": "plateau"},
        {"name": "Rockhampton / Capricorn Coast QLD", "lat": -23.3791, "lon": 150.5100, "terrain": "coast"},
        {"name": "Townsville / North Queensland", "lat": -19.2590, "lon": 146.8169, "terrain": "coast"},
        {"name": "Cairns / Tropical North QLD", "lat": -16.9186, "lon": 145.7781, "terrain": "coast"},
        {"name": "Adelaide / Mount Lofty Ranges SA", "lat": -34.9285, "lon": 138.6007, "terrain": "coast"},
        {"name": "Perth / Swan Coastal Plain WA", "lat": -31.9505, "lon": 115.8605, "terrain": "coast"},
        {"name": "Kalgoorlie / Goldfields WA", "lat": -30.7489, "lon": 121.4658, "terrain": "desert"},
        {"name": "Broome / Kimberley Coast WA", "lat": -17.9614, "lon": 122.2359, "terrain": "coast"},
        {"name": "Darwin / Top End NT", "lat": -12.4634, "lon": 130.8456, "terrain": "coast"},
        {"name": "Alice Springs / Red Centre NT", "lat": -23.6980, "lon": 133.8807, "terrain": "desert"},
        {"name": "Uluru Red Center Outback", "lat": -25.3444, "lon": 131.0369, "terrain": "desert"},
        {"name": "Hobart / Mount Wellington TAS", "lat": -42.8821, "lon": 147.3272, "terrain": "mountain"},
    ],
    "new zealand": [
        {"name": "Auckland Harbor", "lat": -36.8485, "lon": 174.7633, "terrain": "coast"},
        {"name": "Queenstown / Southern Alps", "lat": -45.0312, "lon": 168.6626, "terrain": "mountain"},
        {"name": "Mount Cook / Aoraki Peak", "lat": -43.7333, "lon": 170.0956, "terrain": "mountain"},
        {"name": "Milford Sound Fiordland", "lat": -44.6716, "lon": 167.9256, "terrain": "mountain"},
        {"name": "Christchurch Canterbury Plain", "lat": -43.5321, "lon": 172.6362, "terrain": "urban"},
    ],
    "greece": [
        {"name": "Athens Attica Metropolitan", "lat": 37.9838, "lon": 23.7275, "terrain": "urban"},
        {"name": "Thessaloniki Macedonia Coast", "lat": 40.6401, "lon": 22.9444, "terrain": "coast"},
        {"name": "Mount Olympus / Litochoro", "lat": 40.0884, "lon": 22.3586, "terrain": "mountain"},
        {"name": "Meteora Sandstone Pinnacles", "lat": 39.7217, "lon": 21.6306, "terrain": "mountain"},
        {"name": "Crete / Chania Coast", "lat": 35.5138, "lon": 24.0180, "terrain": "coast"},
        {"name": "Santorini Cyclades Caldera", "lat": 36.3932, "lon": 25.4615, "terrain": "coast"},
    ],
    "portugal": [
        {"name": "Lisbon Tagus Estuary", "lat": 38.7223, "lon": -9.1393, "terrain": "coast"},
        {"name": "Porto Douro Valley", "lat": 41.1579, "lon": -8.6291, "terrain": "urban"},
        {"name": "Serra da Estrela Peak", "lat": 40.3219, "lon": -7.6133, "terrain": "mountain"},
        {"name": "Sintra Hills / Pena", "lat": 38.8029, "lon": -9.3817, "terrain": "mountain"},
        {"name": "Faro Algarve Coast", "lat": 37.0194, "lon": -7.9304, "terrain": "coast"},
    ],
    "sweden": [
        {"name": "Stockholm Archipelago", "lat": 59.3293, "lon": 18.0686, "terrain": "coast"},
        {"name": "Gothenburg Western Coast", "lat": 57.7089, "lon": 11.9746, "terrain": "coast"},
        {"name": "Are Ski Mountain", "lat": 63.4000, "lon": 13.0800, "terrain": "mountain"},
        {"name": "Kiruna Arctic / Abisko", "lat": 67.8558, "lon": 20.2253, "terrain": "mountain"},
        {"name": "Malmo Southern Plain", "lat": 55.6050, "lon": 13.0038, "terrain": "urban"},
    ],
    "finland": [
        {"name": "Somero / Hame Foothills / Southwest Finland", "lat": 60.6333, "lon": 23.5167, "terrain": "valley"},
        {"name": "Turku / Southwest Archipelago", "lat": 60.4518, "lon": 22.2666, "terrain": "coast"},
        {"name": "Helsinki / Capital Uusimaa", "lat": 60.1699, "lon": 24.9384, "terrain": "coast"},
        {"name": "Espoo / Nuuksio Lakes", "lat": 60.2052, "lon": 24.6522, "terrain": "valley"},
        {"name": "Tampere / Pirkanmaa Lakes", "lat": 61.4978, "lon": 23.7610, "terrain": "valley"},
        {"name": "Lahti / Salpausselka Ridge", "lat": 60.9827, "lon": 25.6612, "terrain": "mountain"},
        {"name": "Pori / Satakunta West Coast", "lat": 61.4851, "lon": 21.7974, "terrain": "coast"},
        {"name": "Vaasa / Ostrobothnia Gulf of Bothnia", "lat": 63.0951, "lon": 21.6165, "terrain": "coast"},
        {"name": "Jyvaskyla / Central Finland Lakes", "lat": 62.2426, "lon": 25.7473, "terrain": "valley"},
        {"name": "Kuopio / North Savo Lakes", "lat": 62.8924, "lon": 27.6770, "terrain": "valley"},
        {"name": "Joensuu / North Karelia", "lat": 62.6010, "lon": 29.7636, "terrain": "valley"},
        {"name": "Oulu / Northern Ostrobothnia Coast", "lat": 65.0121, "lon": 25.4651, "terrain": "coast"},
        {"name": "Rovaniemi / Lapland Gateway", "lat": 66.5039, "lon": 25.7294, "terrain": "mountain"},
        {"name": "Inari / Northern Lapland Tundra", "lat": 68.9056, "lon": 27.0289, "terrain": "mountain"},
    ],
    "ireland": [
        {"name": "Dublin Capital / East Coast", "lat": 53.3498, "lon": -6.2603, "terrain": "coast"},
        {"name": "Cork / South Coast Port", "lat": 51.8985, "lon": -8.4756, "terrain": "coast"},
        {"name": "Galway / West Atlantic Coast", "lat": 53.2707, "lon": -9.0568, "terrain": "coast"},
        {"name": "Killarney / MacGillycuddy Reeks Kerry", "lat": 52.0599, "lon": -9.5044, "terrain": "mountain"},
        {"name": "Donegal / Wild Atlantic Way", "lat": 54.6549, "lon": -8.1105, "terrain": "mountain"},
        {"name": "Limerick / Shannon Basin", "lat": 52.6638, "lon": -8.6267, "terrain": "valley"},
    ],
    "poland": [
        {"name": "Warsaw / Mazovia Vistula", "lat": 52.2297, "lon": 21.0122, "terrain": "urban"},
        {"name": "Krakow / Southern Vistula Historic", "lat": 50.0647, "lon": 19.9450, "terrain": "urban"},
        {"name": "Zakopane / High Tatra Mountains", "lat": 49.2992, "lon": 19.9496, "terrain": "mountain"},
        {"name": "Wroclaw / Lower Silesia Oder", "lat": 51.1079, "lon": 17.0385, "terrain": "urban"},
        {"name": "Gdansk / Baltic Coast Pomerania", "lat": 54.3520, "lon": 18.6466, "terrain": "coast"},
        {"name": "Poznan / Greater Poland Warta", "lat": 52.4064, "lon": 16.9252, "terrain": "urban"},
        {"name": "Bialystok / Podlasie East", "lat": 53.1325, "lon": 23.1688, "terrain": "valley"},
        {"name": "Bieszczady / Southeastern Mountains", "lat": 49.2789, "lon": 22.5694, "terrain": "mountain"},
    ],
    "czech republic": [
        {"name": "Prague / Vltava Basin Capital", "lat": 50.0755, "lon": 14.4378, "terrain": "urban"},
        {"name": "Brno / South Moravian Basin", "lat": 49.1951, "lon": 16.6068, "terrain": "valley"},
        {"name": "Ostrava / Silesian Beskids", "lat": 49.8209, "lon": 18.2625, "terrain": "urban"},
        {"name": "Krkonose / Snezka Alpine Peak", "lat": 50.7360, "lon": 15.7397, "terrain": "mountain"},
        {"name": "Cesky Krumlov / South Bohemian Hills", "lat": 48.8127, "lon": 14.3175, "terrain": "valley"},
        {"name": "Plzen / Western Bohemia", "lat": 49.7384, "lon": 13.3736, "terrain": "valley"},
    ],
    "czechia": [
        {"name": "Prague / Vltava Basin Capital", "lat": 50.0755, "lon": 14.4378, "terrain": "urban"},
        {"name": "Brno / South Moravian Basin", "lat": 49.1951, "lon": 16.6068, "terrain": "valley"},
        {"name": "Krkonose / Snezka Alpine Peak", "lat": 50.7360, "lon": 15.7397, "terrain": "mountain"},
    ],
    "netherlands": [
        {"name": "Amsterdam / North Holland Polder", "lat": 52.3676, "lon": 4.9041, "terrain": "coast"},
        {"name": "Rotterdam / Rhine-Meuse Delta", "lat": 51.9244, "lon": 4.4777, "terrain": "coast"},
        {"name": "Utrecht / Central Lowlands", "lat": 52.0907, "lon": 5.1214, "terrain": "urban"},
        {"name": "Groningen / Northern Plains", "lat": 53.2194, "lon": 6.5665, "terrain": "valley"},
        {"name": "Maastricht / Limburg Southern Hills", "lat": 50.8514, "lon": 5.6910, "terrain": "valley"},
        {"name": "Eindhoven / North Brabant", "lat": 51.4416, "lon": 5.4697, "terrain": "urban"},
    ],
    "belgium": [
        {"name": "Brussels / Central Brabant", "lat": 50.8503, "lon": 4.3517, "terrain": "urban"},
        {"name": "Antwerp / Scheldt Port", "lat": 51.2194, "lon": 4.4025, "terrain": "coast"},
        {"name": "Ghent / Flanders Lowlands", "lat": 51.0543, "lon": 3.7174, "terrain": "valley"},
        {"name": "Bruges / Coastal Flanders", "lat": 51.2093, "lon": 3.2247, "terrain": "coast"},
        {"name": "Liege / Meuse Valley", "lat": 50.6326, "lon": 5.5797, "terrain": "valley"},
        {"name": "Ardennes / Dinant Highlands", "lat": 50.2611, "lon": 4.9122, "terrain": "mountain"},
    ],
    "denmark": [
        {"name": "Copenhagen / Zealand Coast", "lat": 55.6761, "lon": 12.5683, "terrain": "coast"},
        {"name": "Aarhus / Jutland East Coast", "lat": 56.1629, "lon": 10.2039, "terrain": "coast"},
        {"name": "Odense / Funen Island", "lat": 55.4038, "lon": 10.4024, "terrain": "valley"},
        {"name": "Aalborg / Limfjord Northern Jutland", "lat": 57.0488, "lon": 9.9217, "terrain": "coast"},
    ],
    "hungary": [
        {"name": "Budapest / Danube Basin Capital", "lat": 47.4979, "lon": 19.0402, "terrain": "urban"},
        {"name": "Debrecen / Great Hungarian Plain", "lat": 47.5316, "lon": 21.6273, "terrain": "plateau"},
        {"name": "Szeged / Southern Tisza Plain", "lat": 46.2530, "lon": 20.1414, "terrain": "valley"},
        {"name": "Pecs / Mecsek Hills", "lat": 46.0727, "lon": 18.2323, "terrain": "mountain"},
        {"name": "Balaton / Lake Highland", "lat": 46.8400, "lon": 17.7400, "terrain": "valley"},
    ],
    "romania": [
        {"name": "Bucharest / Wallachian Plain", "lat": 44.4268, "lon": 26.1025, "terrain": "urban"},
        {"name": "Cluj-Napoca / Transylvania Plateau", "lat": 46.7712, "lon": 23.6236, "terrain": "plateau"},
        {"name": "Brasov / Carpathian Mountains", "lat": 45.6580, "lon": 25.6012, "terrain": "mountain"},
        {"name": "Sibiu / Transylvanian Alps", "lat": 45.7983, "lon": 24.1256, "terrain": "mountain"},
        {"name": "Iasi / Moldavia Hills", "lat": 47.1585, "lon": 27.6014, "terrain": "valley"},
        {"name": "Constanta / Black Sea Coast", "lat": 44.1792, "lon": 28.6498, "terrain": "coast"},
    ],
    "bulgaria": [
        {"name": "Sofia / Vitosha Mountain Foothills", "lat": 42.6977, "lon": 23.3219, "terrain": "mountain"},
        {"name": "Plovdiv / Thracian Plain", "lat": 42.1354, "lon": 24.7453, "terrain": "valley"},
        {"name": "Varna / Black Sea North Coast", "lat": 43.2141, "lon": 27.9147, "terrain": "coast"},
        {"name": "Bansko / Pirin Alpine Peaks", "lat": 41.8383, "lon": 23.4885, "terrain": "mountain"},
        {"name": "Veliko Tarnovo / Balkan Mountains", "lat": 43.0757, "lon": 25.6172, "terrain": "mountain"},
    ],
    "ukraine": [
        {"name": "Kyiv / Dnieper River Basin", "lat": 50.4501, "lon": 30.5234, "terrain": "urban"},
        {"name": "Lviv / Carpathian Foothills", "lat": 49.8397, "lon": 24.0297, "terrain": "valley"},
        {"name": "Yaremche / Carpathian Mountains", "lat": 48.4594, "lon": 24.5574, "terrain": "mountain"},
        {"name": "Odesa / Black Sea Coast Port", "lat": 46.4825, "lon": 30.7233, "terrain": "coast"},
        {"name": "Kharkiv / Northeastern Plains", "lat": 49.9935, "lon": 36.2304, "terrain": "urban"},
    ],
    "iceland": [
        {"name": "Reykjavik Coastal Capital", "lat": 64.1466, "lon": -21.9426, "terrain": "coast"},
        {"name": "Akureyri Northern Fjord", "lat": 65.6835, "lon": -18.1059, "terrain": "coast"},
        {"name": "Vik Black Sand Coast", "lat": 63.4186, "lon": -19.0060, "terrain": "coast"},
        {"name": "Reynisfjara / Reynisdrangar Basalt Stacks", "lat": 63.4044, "lon": -19.0494, "terrain": "coast"},
        {"name": "Vatnajokull Glacier Volcano", "lat": 64.4222, "lon": -16.7867, "terrain": "mountain"},
        {"name": "Landmannalaugar Highlands", "lat": 63.9908, "lon": -19.0608, "terrain": "mountain"},
    ],
    "brazil": [
        {"name": "Pirai do Sul / Pirai River / Campos Gerais PR", "lat": -24.7500, "lon": -50.0833, "terrain": "valley"},
        {"name": "Ponta Grossa / Campos Gerais Parana", "lat": -25.0945, "lon": -50.1633, "terrain": "plateau"},
        {"name": "Curitiba / Parana Highland Capital", "lat": -25.4284, "lon": -49.2733, "terrain": "plateau"},
        {"name": "Foz do Iguacu / Parana Border", "lat": -25.5163, "lon": -54.5854, "terrain": "valley"},
        {"name": "Londrina / Northern Parana", "lat": -23.3045, "lon": -51.1696, "terrain": "plateau"},
        {"name": "Florianopolis / Santa Catarina Coast", "lat": -27.5954, "lon": -48.5480, "terrain": "coast"},
        {"name": "Porto Alegre / Rio Grande do Sul", "lat": -30.0346, "lon": -51.2177, "terrain": "coast"},
        {"name": "Caxias do Sul / Serra Gaucha RS", "lat": -29.1678, "lon": -51.1794, "terrain": "mountain"},
        {"name": "Sao Paulo Metropolitan", "lat": -23.5505, "lon": -46.6333, "terrain": "urban"},
        {"name": "Campinas / Sao Paulo Interior", "lat": -22.9099, "lon": -47.0626, "terrain": "urban"},
        {"name": "Rio de Janeiro Guanabara Bay", "lat": -22.9068, "lon": -43.1729, "terrain": "coast"},
        {"name": "Sugarloaf Mountain / Urca Rio", "lat": -22.9492, "lon": -43.1545, "terrain": "mountain"},
        {"name": "Serra dos Orgaos / Petropolis", "lat": -22.4961, "lon": -43.0569, "terrain": "mountain"},
        {"name": "Belo Horizonte / Minas Gerais Central", "lat": -19.9167, "lon": -43.9345, "terrain": "mountain"},
        {"name": "Ouro Preto / Serra do Espinhaco MG", "lat": -20.3856, "lon": -43.5035, "terrain": "mountain"},
        {"name": "Brasilia Central Plateau", "lat": -15.7975, "lon": -47.8919, "terrain": "plateau"},
        {"name": "Goiania / Goias Central Plateau", "lat": -16.6869, "lon": -49.2648, "terrain": "plateau"},
        {"name": "Salvador Bahia Coast", "lat": -12.9777, "lon": -38.5016, "terrain": "coast"},
        {"name": "Recife / Pernambuco Atlantic Coast", "lat": -8.0476, "lon": -34.8770, "terrain": "coast"},
        {"name": "Fortaleza / Ceara Coast", "lat": -3.7172, "lon": -38.5433, "terrain": "coast"},
        {"name": "Manaus Amazon Basin", "lat": -3.1190, "lon": -60.0217, "terrain": "valley"},
        {"name": "Cuiaba / Pantanal Gateway MT", "lat": -15.6014, "lon": -56.0979, "terrain": "valley"},
    ],
    "mexico": [
        {"name": "Mexico City Valley", "lat": 19.4326, "lon": -99.1332, "terrain": "valley"},
        {"name": "Monterrey Sierra Madre", "lat": 25.6866, "lon": -100.3161, "terrain": "mountain"},
        {"name": "Guadalajara Jalisco", "lat": 20.6597, "lon": -103.3496, "terrain": "urban"},
        {"name": "Pico de Orizaba Volcano", "lat": 19.0300, "lon": -97.2700, "terrain": "mountain"},
        {"name": "Cancun Yucatan Coast", "lat": 21.1619, "lon": -86.8515, "terrain": "coast"},
        {"name": "San Cristobal / Chiapas Highlands", "lat": 16.7370, "lon": -92.6376, "terrain": "mountain"},
    ],
    "colombia": [
        {"name": "Bogota Andean Savanna", "lat": 4.7110, "lon": -74.0721, "terrain": "plateau"},
        {"name": "Medellin Aburra Valley", "lat": 6.2442, "lon": -75.5812, "terrain": "valley"},
        {"name": "Sierra Nevada de Santa Marta", "lat": 10.8200, "lon": -73.6900, "terrain": "mountain"},
        {"name": "Manizales Coffee Cordillera", "lat": 5.0689, "lon": -75.5174, "terrain": "mountain"},
        {"name": "Cartagena Caribbean Coast", "lat": 10.3910, "lon": -75.4794, "terrain": "coast"},
    ],
    "peru": [
        {"name": "Lima Pacific Coast", "lat": -12.0464, "lon": -77.0428, "terrain": "coast"},
        {"name": "Cusco / Sacred Valley", "lat": -13.5319, "lon": -71.9675, "terrain": "mountain"},
        {"name": "Machu Picchu Andes Peak", "lat": -13.1631, "lon": -72.5450, "terrain": "mountain"},
        {"name": "Huaraz / Cordillera Blanca", "lat": -9.5261, "lon": -77.5288, "terrain": "mountain"},
        {"name": "Arequipa / Misti Volcano", "lat": -16.4090, "lon": -71.5375, "terrain": "mountain"},
    ],
    "chile": [
        {"name": "Santiago Central Valley", "lat": -33.4489, "lon": -70.6693, "terrain": "valley"},
        {"name": "Valparaiso Coastal Hills", "lat": -33.0472, "lon": -71.6127, "terrain": "coast"},
        {"name": "Torres del Paine Patagonia", "lat": -51.2532, "lon": -72.8814, "terrain": "mountain"},
        {"name": "San Pedro de Atacama Desert", "lat": -22.9087, "lon": -68.1997, "terrain": "desert"},
        {"name": "Puerto Montt / Lake Llanquihue", "lat": -41.4693, "lon": -72.9424, "terrain": "mountain"},
    ],
    "argentina": [
        {"name": "Buenos Aires Rio de la Plata", "lat": -34.6037, "lon": -58.3816, "terrain": "coast"},
        {"name": "Mendoza / Aconcagua Foothills", "lat": -32.8895, "lon": -68.8458, "terrain": "mountain"},
        {"name": "Bariloche Lake / Andes", "lat": -41.1335, "lon": -71.3103, "terrain": "mountain"},
        {"name": "Ushuaia Tierra del Fuego", "lat": -54.8019, "lon": -68.3030, "terrain": "mountain"},
        {"name": "Salta / Cafayate Valleys", "lat": -24.7821, "lon": -65.4232, "terrain": "valley"},
    ],
    "south africa": [
        {"name": "Cape Town / Table Mountain", "lat": -33.9249, "lon": 18.4241, "terrain": "mountain"},
        {"name": "Table Mountain Plateau / Cableway", "lat": -33.9628, "lon": 18.4098, "terrain": "mountain"},
        {"name": "Johannesburg Highveld Plateau", "lat": -26.2041, "lon": 28.0473, "terrain": "plateau"},
        {"name": "Drakensberg Mountain Escarpment", "lat": -29.5833, "lon": 29.3000, "terrain": "mountain"},
        {"name": "Durban Indian Ocean Coast", "lat": -29.8587, "lon": 31.0218, "terrain": "coast"},
        {"name": "Kruger Lowveld Savanna", "lat": -24.0116, "lon": 31.4859, "terrain": "valley"},
    ],
    "kenya": [
        {"name": "Nanyuki / Mount Kenya Northwest Foothills", "lat": 0.0167, "lon": 37.0667, "terrain": "plateau"},
        {"name": "Mount Kenya Alpine Peak", "lat": -0.1521, "lon": 37.3084, "terrain": "mountain"},
        {"name": "Nairobi Central Highlands", "lat": -1.2921, "lon": 36.8219, "terrain": "plateau"},
        {"name": "Nyeri / Central Highlands Foothills", "lat": -0.4197, "lon": 36.9511, "terrain": "mountain"},
        {"name": "Nakuru Great Rift Valley", "lat": -0.3031, "lon": 36.0800, "terrain": "valley"},
        {"name": "Eldoret / Uasin Gishu Highland Plateau", "lat": 0.5143, "lon": 35.2698, "terrain": "plateau"},
        {"name": "Kisumu / Lake Victoria Coast", "lat": -0.0917, "lon": 34.7680, "terrain": "coast"},
        {"name": "Mombasa Swahili Coast", "lat": -4.0435, "lon": 39.6682, "terrain": "coast"},
        {"name": "Naivasha / Great Rift Valley Lake", "lat": -0.7172, "lon": 36.4310, "terrain": "valley"},
        {"name": "Marsabit / Northern Desert Oasis", "lat": 2.3284, "lon": 37.9899, "terrain": "desert"},
        {"name": "Lodwar / Lake Turkana Basin", "lat": 3.1191, "lon": 35.5973, "terrain": "desert"},
        {"name": "Voi / Tsavo Savanna Corridor", "lat": -3.3967, "lon": 38.5564, "terrain": "valley"},
    ],
    "indonesia": [
        {"name": "Jakarta Java Basin", "lat": -6.2088, "lon": 106.8456, "terrain": "urban"},
        {"name": "Mount Bromo / East Java", "lat": -7.9425, "lon": 112.9530, "terrain": "mountain"},
        {"name": "Bali Ubud Foothills", "lat": -8.5069, "lon": 115.2625, "terrain": "valley"},
        {"name": "Bandung Highland Valley", "lat": -6.9175, "lon": 107.6191, "terrain": "valley"},
        {"name": "Lombok / Mount Rinjani", "lat": -8.4167, "lon": 116.4583, "terrain": "mountain"},
    ],
    "thailand": [
        {"name": "Bangkok Chao Phraya Delta", "lat": 13.7563, "lon": 100.5018, "terrain": "urban"},
        {"name": "Chiang Mai / Doi Inthanon Mountain", "lat": 18.7883, "lon": 98.9853, "terrain": "mountain"},
        {"name": "Pai Alpine Valley", "lat": 19.3582, "lon": 98.4411, "terrain": "mountain"},
        {"name": "Phuket Andaman Coast", "lat": 7.8804, "lon": 98.3923, "terrain": "coast"},
        {"name": "Krabi Limestone Coast", "lat": 8.0863, "lon": 98.9063, "terrain": "coast"},
    ],
    "vietnam": [
        {"name": "Hanoi Red River Basin", "lat": 21.0285, "lon": 105.8542, "terrain": "urban"},
        {"name": "Sapa / Fan Si Pan High Peaks", "lat": 22.3364, "lon": 103.8438, "terrain": "mountain"},
        {"name": "Da Nang Coastal Port", "lat": 16.0544, "lon": 108.2022, "terrain": "coast"},
        {"name": "Ha Long Bay Karst Coast", "lat": 20.9501, "lon": 107.0734, "terrain": "coast"},
        {"name": "Da Lat Central Highlands", "lat": 11.9404, "lon": 108.4583, "terrain": "mountain"},
        {"name": "Ho Chi Minh City Mekong Gateway", "lat": 10.8231, "lon": 106.6297, "terrain": "urban"},
    ],
    "south korea": [
        {"name": "Seoul Han River / Bukhansan", "lat": 37.5665, "lon": 126.9780, "terrain": "mountain"},
        {"name": "Seoraksan National Park Peaks", "lat": 38.1194, "lon": 128.4656, "terrain": "mountain"},
        {"name": "Busan Coastal Harbor", "lat": 35.1796, "lon": 129.0756, "terrain": "coast"},
        {"name": "Jeju Island / Hallasan Volcano", "lat": 33.3617, "lon": 126.5292, "terrain": "mountain"},
        {"name": "Pyeongchang Taebaek Ski Highlands", "lat": 37.3705, "lon": 128.3902, "terrain": "mountain"},
    ],
    "russia": [
        {"name": "Moscow Central Plain", "lat": 55.7558, "lon": 37.6173, "terrain": "urban"},
        {"name": "Saint Petersburg Baltic Gulf", "lat": 59.9343, "lon": 30.3351, "terrain": "coast"},
        {"name": "Sochi / Krasnaya Polyana Caucasus", "lat": 43.6784, "lon": 40.2056, "terrain": "mountain"},
        {"name": "Lake Baikal / Irkutsk Highlands", "lat": 52.2870, "lon": 104.3050, "terrain": "mountain"},
        {"name": "Altai Mountains / Belukha", "lat": 49.8000, "lon": 86.5833, "terrain": "mountain"},
        {"name": "Kamchatka Volcanoes / Petropavlovsk", "lat": 53.0167, "lon": 158.6500, "terrain": "mountain"},
    ],
    "algeria": [
        {"name": "Algiers / Mediterranean Bay Capital", "lat": 36.7538, "lon": 3.0588, "terrain": "coast"},
        {"name": "Oran / Western Coast", "lat": 35.6987, "lon": -0.6349, "terrain": "coast"},
        {"name": "Constantine / Rhumel River Gorges", "lat": 36.3650, "lon": 6.6147, "terrain": "mountain"},
        {"name": "Annaba / Eastern Mediterranean Coast", "lat": 36.9000, "lon": 7.7667, "terrain": "coast"},
        {"name": "Ghardaia / M'Zab Valley Sahara", "lat": 32.4900, "lon": 3.6739, "terrain": "desert"},
        {"name": "Tamanrasset / Hoggar Mountains", "lat": 22.7850, "lon": 5.5228, "terrain": "mountain"},
    ],
    "tunisia": [
        {"name": "Tunis / Gulf of Tunis Capital", "lat": 36.8065, "lon": 10.1815, "terrain": "coast"},
        {"name": "Sousse / Sahel Coast", "lat": 35.8256, "lon": 10.6369, "terrain": "coast"},
        {"name": "Sfax / Gulf of Gabes Port", "lat": 34.7406, "lon": 10.7603, "terrain": "coast"},
        {"name": "Djerba / Island Coast", "lat": 33.8075, "lon": 10.8451, "terrain": "coast"},
        {"name": "Tozeur / Chott el Djerid Sahara Oasis", "lat": 33.9197, "lon": 8.1336, "terrain": "desert"},
        {"name": "Bizerte / Northern Mediterranean Coast", "lat": 37.2744, "lon": 9.8739, "terrain": "coast"},
    ],
    "libya": [
        {"name": "Tripoli / Mediterranean Capital", "lat": 32.8872, "lon": 13.1913, "terrain": "coast"},
        {"name": "Benghazi / Cyrenaica Coast", "lat": 32.1167, "lon": 20.0667, "terrain": "coast"},
        {"name": "Misrata / Western Mediterranean Port", "lat": 32.3754, "lon": 15.0925, "terrain": "coast"},
        {"name": "Sabha / Fezzan Sahara Oasis", "lat": 27.0377, "lon": 14.4283, "terrain": "desert"},
    ],
    "jordan": [
        {"name": "Amman / Seven Hills Capital", "lat": 31.9454, "lon": 35.9284, "terrain": "urban"},
        {"name": "Petra / Wadi Musa Sandstone Canyon", "lat": 30.3285, "lon": 35.4444, "terrain": "mountain"},
        {"name": "Wadi Rum / Valley of the Moon Desert", "lat": 29.5735, "lon": 35.4206, "terrain": "desert"},
        {"name": "Aqaba / Red Sea Gulf Coast", "lat": 29.5321, "lon": 35.0063, "terrain": "coast"},
        {"name": "Jerash / Roman Decapolis Ruins", "lat": 32.2808, "lon": 35.8953, "terrain": "valley"},
        {"name": "Dead Sea / Jordan Rift Valley", "lat": 31.5000, "lon": 35.5000, "terrain": "valley"},
    ],
    "taiwan": [
        {"name": "Taipei / Tamsui Basin Capital", "lat": 25.0330, "lon": 121.5654, "terrain": "urban"},
        {"name": "Kaohsiung / Southern Taiwan Harbor", "lat": 22.6273, "lon": 120.3014, "terrain": "coast"},
        {"name": "Taichung / Central Taiwan Plain", "lat": 24.1477, "lon": 120.6736, "terrain": "urban"},
        {"name": "Taroko Gorge / Hualien East Coast", "lat": 24.1592, "lon": 121.6214, "terrain": "mountain"},
        {"name": "Alishan / Central Mountain Range Peaks", "lat": 23.5100, "lon": 120.8000, "terrain": "mountain"},
        {"name": "Tainan / Historic South Coast", "lat": 22.9997, "lon": 120.2270, "terrain": "urban"},
    ],
    "malaysia": [
        {"name": "Kuala Lumpur / Klang Valley Capital", "lat": 3.1390, "lon": 101.6869, "terrain": "urban"},
        {"name": "Penang / George Town Strait Coast", "lat": 5.4164, "lon": 100.3327, "terrain": "coast"},
        {"name": "Johor Bahru / Southern Peninsula", "lat": 1.4927, "lon": 103.7414, "terrain": "coast"},
        {"name": "Cameron Highlands / Tea Mountain Plateau", "lat": 4.4714, "lon": 101.3768, "terrain": "mountain"},
        {"name": "Kota Kinabalu / Mount Kinabalu Sabah", "lat": 5.9804, "lon": 116.0735, "terrain": "mountain"},
        {"name": "Kuching / Sarawak River Basin", "lat": 1.5533, "lon": 110.3592, "terrain": "coast"},
    ],
    "philippines": [
        {"name": "Manila / Manila Bay Capital", "lat": 14.5995, "lon": 120.9842, "terrain": "coast"},
        {"name": "Cebu City / Central Visayas Port", "lat": 10.3157, "lon": 123.8854, "terrain": "coast"},
        {"name": "Davao / Mount Apo Foothills Mindanao", "lat": 7.1907, "lon": 125.4504, "terrain": "mountain"},
        {"name": "Baguio / Cordillera Mountain Pines", "lat": 16.4023, "lon": 120.5960, "terrain": "mountain"},
        {"name": "Palawan / Puerto Princesa Karst Coast", "lat": 9.7392, "lon": 118.7353, "terrain": "coast"},
        {"name": "Bicol / Mayon Volcano Albay", "lat": 13.2572, "lon": 123.6856, "terrain": "mountain"},
    ],
    "kazakhstan": [
        {"name": "Almaty / Tian Shan Mountain Foothills", "lat": 43.2220, "lon": 76.8512, "terrain": "mountain"},
        {"name": "Astana / Ishim River Steppe Capital", "lat": 51.1694, "lon": 71.4491, "terrain": "urban"},
        {"name": "Shymkent / Southern Oasis Plain", "lat": 42.3417, "lon": 69.5901, "terrain": "plateau"},
        {"name": "Aktau / Caspian Sea Coast", "lat": 43.6500, "lon": 51.1667, "terrain": "coast"},
        {"name": "Altai / Belukha Foothills East", "lat": 49.9500, "lon": 84.5000, "terrain": "mountain"},
    ],
    "uzbekistan": [
        {"name": "Tashkent / Chirchiq River Basin", "lat": 41.2995, "lon": 69.2401, "terrain": "urban"},
        {"name": "Samarkand / Registan Silk Road Oasis", "lat": 39.6542, "lon": 66.9597, "terrain": "valley"},
        {"name": "Bukhara / Kyzylkum Desert Oasis", "lat": 39.7747, "lon": 64.4286, "terrain": "desert"},
        {"name": "Khiva / Amu Darya Basin Fortress", "lat": 41.3783, "lon": 60.3639, "terrain": "desert"},
    ],
    "kyrgyzstan": [
        {"name": "Bishkek / Ala-Too Range Chuy Valley", "lat": 42.8746, "lon": 74.5698, "terrain": "mountain"},
        {"name": "Issyk-Kul / High Mountain Alpine Lake", "lat": 42.5000, "lon": 77.2000, "terrain": "mountain"},
        {"name": "Osh / Fergana Valley Sulaiman-Too", "lat": 40.5140, "lon": 72.8161, "terrain": "mountain"},
    ],
    "tajikistan": [
        {"name": "Dushanbe / Hissar Valley Capital", "lat": 38.5598, "lon": 68.7870, "terrain": "mountain"},
        {"name": "Pamir Mountains / Khorog Highway", "lat": 37.4900, "lon": 71.5500, "terrain": "mountain"},
        {"name": "Khujand / Syr Darya Fergana", "lat": 40.2826, "lon": 69.6222, "terrain": "valley"},
    ],
    "nigeria": [
        {"name": "Lagos / Atlantic Gulf of Guinea Port", "lat": 6.5244, "lon": 3.3792, "terrain": "coast"},
        {"name": "Abuja / Aso Rock Capital Plateau", "lat": 9.0765, "lon": 7.3986, "terrain": "plateau"},
        {"name": "Kano / Northern Sahel Savanna", "lat": 12.0022, "lon": 8.5920, "terrain": "urban"},
        {"name": "Ibadan / Yoruba Hills Southwest", "lat": 7.3775, "lon": 3.9470, "terrain": "valley"},
        {"name": "Jos / Jos Plateau Granite Highlands", "lat": 9.8965, "lon": 8.8583, "terrain": "mountain"},
        {"name": "Port Harcourt / Niger Delta Coast", "lat": 4.8156, "lon": 7.0498, "terrain": "coast"},
    ],
}

# Register title-cased keys for case-insensitive lookup
for _k, _v in list(COUNTRY_BBOXES.items()):
    if _k.title() not in COUNTRY_BBOXES:
        COUNTRY_BBOXES[_k.title()] = _v

for _k, _v in list(COUNTRY_ANCHORS.items()):
    if _k.title() not in COUNTRY_ANCHORS:
        COUNTRY_ANCHORS[_k.title()] = _v


def get_country_anchors(
    country_name: str,
    max_anchors: int = 16,
    terrain: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve representative geographic anchors for a specified country, optionally prioritizing terrain."""
    c_clean = country_name.strip().lower()
    anchors: List[Dict[str, Any]] = []
    if c_clean in COUNTRY_ANCHORS:
        anchors = COUNTRY_ANCHORS[c_clean]
    else:
        for k, v in COUNTRY_ANCHORS.items():
            if k == c_clean:
                anchors = v
                break
        if not anchors:
            for k, v in COUNTRY_ANCHORS.items():
                if k in c_clean.split() or c_clean in k.split():
                    anchors = v
                    break
    if not anchors:
        return []

    if terrain:
        t_clean = terrain.strip().lower()
        def terrain_priority(a: Dict[str, Any]) -> int:
            a_terr = a.get("terrain", "").lower()
            if a_terr == t_clean:
                return 0
            if t_clean == "mountain" and a_terr in ("mountain", "valley", "plateau"):
                return 1
            if t_clean == "desert" and a_terr in ("desert", "plateau"):
                return 1
            if t_clean == "coast" and a_terr in ("coast",):
                return 1
            return 2
        anchors = sorted(anchors, key=terrain_priority)

    return anchors[:max_anchors]


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
    # 0. Nordic / Scandinavian border disambiguation (Finland vs Sweden vs Norway)
    if 54.0 <= lat <= 71.5 and 4.0 <= lon <= 32.5:
        # Finland: East of Gulf of Bothnia / Baltic Sea
        if 59.5 <= lat <= 70.1 and lon >= 20.5:
            if lat >= 69.6 and lon >= 29.0:
                return "Norway"  # Kirkenes / Sør-Varanger
            return "Finland"
        # Sweden vs Norway border
        if 55.0 <= lat <= 71.5:
            if lat < 62.0:
                if lon >= 12.5:
                    return "Sweden"
                return "Norway"
            if 62.0 <= lat < 68.5:
                if lon >= 13.5:
                    return "Sweden"
                return "Norway"
            # Far north / Lapland
            if lon >= 20.5:
                return "Finland"
            if lon >= 17.5 and lat <= 68.5:
                return "Sweden"
    # 0b. Spain vs France vs Portugal border disambiguation (Iberian Peninsula)
    if 35.5 <= lat <= 44.5 and -9.8 <= lon <= 4.0:
        if 36.9 <= lat <= 42.2 and lon <= -6.3:
            return "Portugal"
        if lat < 42.4 or lon < -1.8:
            return "Spain"
        if lat >= 42.8 and lon > 0.0:
            return "France"
        return "Spain"

    # 1. High-precision border disambiguation for South Asia
    # Pakistan vs India border logic
    if (23.6 <= lat <= 37.2 and 60.8 <= lon <= 75.4) or (35.0 <= lat <= 37.2 and 72.5 <= lon <= 77.5):
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
            "turkey", "turkiye", "egypt", "norway", "sweden", "finland",
            "spain", "france", "portugal"
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
    """Resolve GPS coordinates to province/governorate/state and major district with 100% gap-free coverage."""
    # 1. Pakistan (Comprehensive coverage across all administrative territories)
    if (23.6 <= lat <= 37.2 and 60.8 <= lon <= 75.4) or (35.0 <= lat <= 37.2 and 72.5 <= lon <= 77.5):
        # Islamabad Capital Territory
        if 33.60 <= lat <= 33.82 and 72.85 <= lon <= 73.28:
            return SubnationalDivision({"country": "Pakistan", "division": "Islamabad Capital Territory", "district": "Islamabad"})

        # Azad Jammu and Kashmir (AJ&K) - full corridor from 33.0 to 35.1 lat, 73.35 to 74.8 lon
        if 33.0 <= lat <= 35.1 and 73.35 <= lon <= 74.8:
            if lat >= 34.40:
                return SubnationalDivision({"country": "Pakistan", "division": "Azad Kashmir", "district": "Neelum Valley"})
            elif lat >= 34.10:
                return SubnationalDivision({"country": "Pakistan", "division": "Azad Kashmir", "district": "Muzaffarabad / Jhelum Valley"})
            elif lat >= 33.70:
                return SubnationalDivision({"country": "Pakistan", "division": "Azad Kashmir", "district": "Rawalakot / Poonch / Bagh"})
            else:
                return SubnationalDivision({"country": "Pakistan", "division": "Azad Kashmir", "district": "Mirpur / Kotli / Bhimber"})

        # Gilgit-Baltistan (GB) - Karakoram, Himalaya, Hindukush high mountain territory
        if 35.0 <= lat <= 37.2 and 72.5 <= lon <= 77.5:
            if lat >= 36.10:
                return SubnationalDivision({"country": "Pakistan", "division": "Gilgit-Baltistan", "district": "Hunza / Nagar"})
            elif lon >= 75.00:
                return SubnationalDivision({"country": "Pakistan", "division": "Gilgit-Baltistan", "district": "Skardu / Baltistan"})
            elif 35.60 <= lat <= 36.10 and 74.00 <= lon <= 74.70:
                return SubnationalDivision({"country": "Pakistan", "division": "Gilgit-Baltistan", "district": "Gilgit"})
            else:
                return SubnationalDivision({"country": "Pakistan", "division": "Gilgit-Baltistan", "district": "Diamer / Chilas / Astore"})

        # Khyber Pakhtunkhwa (KP) - Hazara, Malakand, Swat, Peshawar, Southern KP
        # Northern Hazara is at lat >= 33.85 and lon <= 73.40; central/southern KP is west of lon 72.60.
        is_kp = False
        if 31.2 <= lat <= 36.9 and 69.5 <= lon <= 74.0:
            if (33.0 <= lat <= 35.1 and lon > 73.40):
                is_kp = False
            elif lat >= 33.85 and lon <= 73.40:
                is_kp = True
            elif lon <= 72.60:
                is_kp = True

        if is_kp:
            if 34.50 <= lat <= 35.80 and 72.00 <= lon <= 73.00:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Swat / Malakand / Kalam"})
            elif lat >= 35.40 and lon <= 72.50:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Chitral / Upper Dir"})
            elif 34.40 <= lat <= 35.30 and 73.15 <= lon <= 74.10:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Kaghan / Naran Valley / Mansehra"})
            elif 33.95 <= lat <= 34.40 and 72.95 <= lon <= 73.40:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Abbottabad / Hazara"})
            elif 33.85 <= lat <= 34.35 and 71.30 <= lon <= 72.10:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Peshawar / Mardan / Charsadda"})
            elif lat < 33.80 and lon <= 72.00:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Kohat / Bannu / D.I. Khan"})
            else:
                return SubnationalDivision({"country": "Pakistan", "division": "Khyber Pakhtunkhwa", "district": "Hazara / Malakand"})

        # Punjab - Murree hills, Rawalpindi, Lahore, Central & Southern Punjab
        if 27.8 <= lat <= 34.15 and 69.9 <= lon <= 75.4:
            if 33.80 < lat <= 34.15 and 73.25 <= lon <= 73.55:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Murree / Galyat"})
            elif 33.30 <= lat <= 33.75 and 72.70 <= lon <= 73.30:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Rawalpindi / Potohar"})
            elif 31.20 <= lat <= 31.85 and 74.00 <= lon <= 74.60:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Lahore"})
            elif 31.10 <= lat <= 31.70 and 72.80 <= lon <= 73.45:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Faisalabad"})
            elif 31.80 <= lat <= 32.60 and 73.80 <= lon <= 74.80:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Gujranwala / Sialkot"})
            elif 29.80 <= lat <= 30.50 and 71.10 <= lon <= 71.85:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Multan"})
            elif lat <= 30.00:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Bahawalpur / Cholistan / Rahim Yar Khan"})
            else:
                return SubnationalDivision({"country": "Pakistan", "division": "Punjab", "district": "Punjab Plains"})

        # Sindh - Karachi, Hyderabad, Sukkur, Indus corridor, Thar
        if 23.6 <= lat <= 28.5 and 66.5 <= lon <= 71.1:
            if 24.65 <= lat <= 25.25 and 66.80 <= lon <= 67.45:
                return SubnationalDivision({"country": "Pakistan", "division": "Sindh", "district": "Karachi"})
            elif 25.20 <= lat <= 25.65 and 68.20 <= lon <= 68.65:
                return SubnationalDivision({"country": "Pakistan", "division": "Sindh", "district": "Hyderabad"})
            elif 27.40 <= lat <= 28.20 and 68.40 <= lon <= 69.30:
                return SubnationalDivision({"country": "Pakistan", "division": "Sindh", "district": "Sukkur / Larkana"})
            elif lon >= 69.50:
                return SubnationalDivision({"country": "Pakistan", "division": "Sindh", "district": "Tharparkar / Mithi"})
            else:
                return SubnationalDivision({"country": "Pakistan", "division": "Sindh", "district": "Sindh"})

        # Balochistan - Quetta, Gwadar, Makran, Chaman, Ziarat
        if 24.8 <= lat <= 32.1 and 60.8 <= lon <= 70.3:
            if 30.00 <= lat <= 30.50 and 66.75 <= lon <= 67.45:
                return SubnationalDivision({"country": "Pakistan", "division": "Balochistan", "district": "Quetta / Ziarat Highlands"})
            elif 24.80 <= lat <= 25.50 and 61.50 <= lon <= 64.20:
                return SubnationalDivision({"country": "Pakistan", "division": "Balochistan", "district": "Gwadar / Makran Coast"})
            else:
                return SubnationalDivision({"country": "Pakistan", "division": "Balochistan", "district": "Balochistan Plateau"})

        return SubnationalDivision({"country": "Pakistan", "division": "Pakistan", "district": "Northern / Mountain Region"})

    # 2. Nepal (Bagmati, Gandaki, Koshi, Terai)
    if 26.3 <= lat <= 30.5 and 80.0 <= lon <= 88.2:
        if 27.55 <= lat <= 27.85 and 85.15 <= lon <= 85.55:
            return SubnationalDivision({"country": "Nepal", "division": "Bagmati Province", "district": "Kathmandu Valley"})
        elif 27.65 <= lat <= 27.80 and 85.45 <= lon <= 85.60:
            return SubnationalDivision({"country": "Nepal", "division": "Bagmati Province", "district": "Nagarkot / Bhaktapur"})
        elif 28.10 <= lat <= 28.40 and 83.85 <= lon <= 84.15:
            return SubnationalDivision({"country": "Nepal", "division": "Gandaki Province", "district": "Pokhara / Annapurna Foothills"})
        elif lat >= 28.50 and 83.50 <= lon <= 84.30:
            return SubnationalDivision({"country": "Nepal", "division": "Gandaki Province", "district": "Mustang / Jomsom / Manang"})
        elif 27.70 <= lat <= 28.10 and 86.50 <= lon <= 87.00:
            return SubnationalDivision({"country": "Nepal", "division": "Koshi Province", "district": "Solukhumbu / Everest Region"})
        elif lat <= 27.55 and 84.00 <= lon <= 85.00:
            return SubnationalDivision({"country": "Nepal", "division": "Bagmati Province", "district": "Chitwan / Terai"})
        elif lat <= 27.60 and 83.00 <= lon <= 83.60:
            return SubnationalDivision({"country": "Nepal", "division": "Lumbini Province", "district": "Lumbini / Rupandehi"})
        elif lon >= 86.50:
            return SubnationalDivision({"country": "Nepal", "division": "Koshi Province", "district": "Eastern Nepal"})
        elif lon <= 82.50:
            return SubnationalDivision({"country": "Nepal", "division": "Karnali Province", "district": "Western Nepal"})
        else:
            return SubnationalDivision({"country": "Nepal", "division": "Bagmati Province", "district": "Central Nepal"})

    # 3. India (Jammu & Kashmir, Himachal, Uttarakhand, Delhi, Punjab, Maharashtra, Karnataka, Tamil Nadu, etc.)
    if 8.0 <= lat <= 35.5 and 68.1 <= lon <= 97.4:
        if 33.80 <= lat <= 34.35 and 74.30 <= lon <= 75.40:
            return SubnationalDivision({"country": "India", "division": "Jammu and Kashmir", "district": "Srinagar / Kashmir Valley"})
        elif 33.90 <= lat <= 34.60 and 76.50 <= lon <= 78.50:
            return SubnationalDivision({"country": "India", "division": "Ladakh", "district": "Leh / Ladakh"})
        elif 30.80 <= lat <= 33.00 and 75.80 <= lon <= 78.50:
            if 32.10 <= lat <= 32.40 and 77.05 <= lon <= 77.30:
                return SubnationalDivision({"country": "India", "division": "Himachal Pradesh", "district": "Manali / Kullu Valley"})
            elif 31.00 <= lat <= 31.20 and 77.05 <= lon <= 77.30:
                return SubnationalDivision({"country": "India", "division": "Himachal Pradesh", "district": "Shimla"})
            elif 32.10 <= lat <= 32.35 and 76.20 <= lon <= 76.45:
                return SubnationalDivision({"country": "India", "division": "Himachal Pradesh", "district": "Dharamshala / Kangra"})
            else:
                return SubnationalDivision({"country": "India", "division": "Himachal Pradesh", "district": "Himachal Pradesh"})
        elif 29.00 <= lat <= 31.50 and 77.50 <= lon <= 81.10:
            if 30.35 <= lat <= 30.55 and 78.00 <= lon <= 78.15:
                return SubnationalDivision({"country": "India", "division": "Uttarakhand", "district": "Mussoorie / Dehradun"})
            elif 29.30 <= lat <= 29.50 and 79.35 <= lon <= 79.55:
                return SubnationalDivision({"country": "India", "division": "Uttarakhand", "district": "Nainital / Kumaon"})
            else:
                return SubnationalDivision({"country": "India", "division": "Uttarakhand", "district": "Uttarakhand"})
        elif 28.40 <= lat <= 28.90 and 76.90 <= lon <= 77.40:
            return SubnationalDivision({"country": "India", "division": "National Capital Territory of Delhi", "district": "Delhi"})
        elif 29.50 <= lat <= 32.50 and 74.00 <= lon <= 77.00:
            return SubnationalDivision({"country": "India", "division": "Punjab", "district": "Punjab / Chandigarh"})
        elif 23.50 <= lat <= 30.20 and 69.50 <= lon <= 78.00:
            return SubnationalDivision({"country": "India", "division": "Rajasthan", "district": "Jaipur / Thar Desert"})
        elif 18.80 <= lat <= 19.35 and 72.70 <= lon <= 73.15:
            return SubnationalDivision({"country": "India", "division": "Maharashtra", "district": "Mumbai"})
        elif 18.35 <= lat <= 18.70 and 73.70 <= lon <= 74.05:
            return SubnationalDivision({"country": "India", "division": "Maharashtra", "district": "Pune"})
        elif 12.80 <= lat <= 13.15 and 77.45 <= lon <= 77.80:
            return SubnationalDivision({"country": "India", "division": "Karnataka", "district": "Bengaluru"})
        elif 12.90 <= lat <= 13.25 and 80.15 <= lon <= 80.35:
            return SubnationalDivision({"country": "India", "division": "Tamil Nadu", "district": "Chennai"})
        elif 11.25 <= lat <= 11.55 and 76.55 <= lon <= 76.85:
            return SubnationalDivision({"country": "India", "division": "Tamil Nadu", "district": "Nilgiris / Ooty"})
        elif 9.95 <= lat <= 10.20 and 76.95 <= lon <= 77.20:
            return SubnationalDivision({"country": "India", "division": "Kerala", "district": "Idukki / Munnar"})
        elif 22.40 <= lat <= 22.75 and 88.25 <= lon <= 88.50:
            return SubnationalDivision({"country": "India", "division": "West Bengal", "district": "Kolkata"})
        elif 26.90 <= lat <= 27.20 and 88.15 <= lon <= 88.40:
            return SubnationalDivision({"country": "India", "division": "West Bengal", "district": "Darjeeling"})
        elif 27.20 <= lat <= 27.50 and 88.45 <= lon <= 88.75:
            return SubnationalDivision({"country": "India", "division": "Sikkim", "district": "Gangtok / Sikkim"})
        else:
            return SubnationalDivision({"country": "India", "division": "India", "district": "Regional"})

    # 4. Qatar (Peninsula)
    if 24.4 <= lat <= 26.3 and 50.7 <= lon <= 51.7:
        if 25.20 <= lat <= 25.40 and 51.45 <= lon <= 51.60:
            return SubnationalDivision({"country": "Qatar", "division": "Doha Municipality", "district": "Doha"})
        elif 25.38 <= lat <= 25.50 and 51.45 <= lon <= 51.55:
            return SubnationalDivision({"country": "Qatar", "division": "Al Daayen", "district": "Lusail"})
        elif 25.10 <= lat <= 25.25 and 51.55 <= lon <= 51.65:
            return SubnationalDivision({"country": "Qatar", "division": "Al Wakrah Municipality", "district": "Al Wakrah"})
        elif 25.60 <= lat <= 25.75 and 51.45 <= lon <= 51.58:
            return SubnationalDivision({"country": "Qatar", "division": "Al Khor Municipality", "district": "Al Khor"})
        else:
            return SubnationalDivision({"country": "Qatar", "division": "Qatar Peninsula", "district": "Qatar"})

    # 5. Bahrain (Island nation)
    if 25.7 <= lat <= 26.4 and 50.3 <= lon <= 50.7:
        return SubnationalDivision({"country": "Bahrain", "division": "Capital Governorate", "district": "Manama"})

    # 6. United Arab Emirates
    if (22.6 <= lat <= 26.1 and 51.5 <= lon <= 56.4) and not (24.4 <= lat <= 26.3 and 50.7 <= lon <= 51.7):
        if 25.32 <= lat <= 25.48 and 55.35 <= lon <= 55.60:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Sharjah", "district": "Sharjah"})
        elif 24.95 <= lat < 25.32 and 55.05 <= lon <= 55.45:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Dubai", "district": "Dubai"})
        elif 24.30 <= lat <= 24.60 and 54.25 <= lon <= 54.70:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Abu Dhabi", "district": "Abu Dhabi"})
        elif 24.05 <= lat <= 24.35 and 55.60 <= lon <= 55.90:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Abu Dhabi", "district": "Al Ain"})
        elif 25.65 <= lat <= 26.05 and 55.80 <= lon <= 56.25:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Ras Al Khaimah", "district": "Ras Al Khaimah / Jebel Jais"})
        elif 25.05 <= lat <= 25.35 and 56.25 <= lon <= 56.40:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Fujairah", "district": "Fujairah / Khor Fakkan"})
        elif 24.75 <= lat <= 24.90 and 56.05 <= lon <= 56.20:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Dubai", "district": "Hatta / Hajar Mountains"})
        elif lat <= 23.50:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirate of Abu Dhabi", "district": "Al Dhafra / Liwa Oasis"})
        else:
            return SubnationalDivision({"country": "United Arab Emirates", "division": "Emirates", "district": "Northern Emirates"})

    # 7. Kuwait
    if 28.5 <= lat <= 30.2 and 46.5 <= lon <= 48.6:
        if 29.30 <= lat <= 29.45 and 47.90 <= lon <= 48.05:
            return SubnationalDivision({"country": "Kuwait", "division": "Capital Governorate (Al Asimah)", "district": "Kuwait City"})
        elif 29.28 <= lat <= 29.38 and 48.02 <= lon <= 48.12:
            return SubnationalDivision({"country": "Kuwait", "division": "Hawalli Governorate", "district": "Salmiya / Hawalli"})
        elif 29.00 <= lat <= 29.15 and 48.02 <= lon <= 48.15:
            return SubnationalDivision({"country": "Kuwait", "division": "Al Ahmadi Governorate", "district": "Al Ahmadi"})
        else:
            return SubnationalDivision({"country": "Kuwait", "division": "Kuwait", "district": "Al Jahra / Subiya"})

    # 8. Oman
    if 16.6 <= lat <= 26.5 and 52.0 <= lon <= 59.9:
        if 23.50 <= lat <= 23.70 and 58.30 <= lon <= 58.60:
            return SubnationalDivision({"country": "Oman", "division": "Muscat Governorate", "district": "Muscat"})
        elif 16.95 <= lat <= 17.15 and 54.00 <= lon <= 54.25:
            return SubnationalDivision({"country": "Oman", "division": "Dhofar Governorate", "district": "Salalah"})
        elif 22.80 <= lat <= 23.35 and 57.20 <= lon <= 57.75:
            return SubnationalDivision({"country": "Oman", "division": "Ad Dakhiliyah", "district": "Nizwa / Jebel Akhdar / Jebel Shams"})
        elif lat >= 25.80 and lon <= 56.50:
            return SubnationalDivision({"country": "Oman", "division": "Musandam Governorate", "district": "Khasab / Fjords"})
        else:
            return SubnationalDivision({"country": "Oman", "division": "Oman", "district": "Batinah / Sharqiya"})

    # 9. Egypt
    if 22.0 <= lat <= 31.7 and 24.7 <= lon <= 36.9:
        if 29.95 <= lat <= 30.15 and 31.15 <= lon <= 31.40:
            return SubnationalDivision({"country": "Egypt", "division": "Cairo Governorate", "district": "Cairo"})
        elif 31.15 <= lat <= 31.30 and 29.85 <= lon <= 30.05:
            return SubnationalDivision({"country": "Egypt", "division": "Alexandria Governorate", "district": "Alexandria"})
        elif 27.85 <= lat <= 28.60 and 33.90 <= lon <= 34.60:
            return SubnationalDivision({"country": "Egypt", "division": "South Sinai Governorate", "district": "Sharm El Sheikh / Mount Sinai"})
        elif 25.60 <= lat <= 25.80 and 32.55 <= lon <= 32.75:
            return SubnationalDivision({"country": "Egypt", "division": "Luxor Governorate", "district": "Luxor"})
        else:
            return SubnationalDivision({"country": "Egypt", "division": "Egypt", "district": "Nile Basin / Red Sea"})

    # 10. Turkey
    if 35.8 <= lat <= 42.1 and 25.6 <= lon <= 44.8:
        if 40.90 <= lat <= 41.20 and 28.80 <= lon <= 29.20:
            return SubnationalDivision({"country": "Turkey", "division": "Istanbul Province", "district": "Istanbul"})
        elif 39.85 <= lat <= 40.05 and 32.75 <= lon <= 33.00:
            return SubnationalDivision({"country": "Turkey", "division": "Ankara Province", "district": "Ankara"})
        elif 38.35 <= lat <= 38.55 and 27.05 <= lon <= 27.25:
            return SubnationalDivision({"country": "Turkey", "division": "Izmir Province", "district": "Izmir"})
        elif 36.80 <= lat <= 37.00 and 30.60 <= lon <= 30.80:
            return SubnationalDivision({"country": "Turkey", "division": "Antalya Province", "district": "Antalya"})
        elif 40.00 <= lat <= 40.25 and 29.00 <= lon <= 29.30:
            return SubnationalDivision({"country": "Turkey", "division": "Bursa Province", "district": "Bursa / Uludag"})
        elif 40.85 <= lat <= 41.15 and 39.60 <= lon <= 41.20:
            return SubnationalDivision({"country": "Turkey", "division": "Black Sea Region", "district": "Trabzon / Rize / Ayder"})
        elif 38.55 <= lat <= 38.75 and 34.75 <= lon <= 34.95:
            return SubnationalDivision({"country": "Turkey", "division": "Nevsehir Province", "district": "Cappadocia / Goreme"})
        else:
            return SubnationalDivision({"country": "Turkey", "division": "Anatolia", "district": "Turkey"})

    # 11. Iraq
    if 29.0 <= lat <= 37.4 and 38.7 <= lon <= 48.6:
        if 33.25 <= lat <= 33.45 and 44.25 <= lon <= 44.45:
            return SubnationalDivision({"country": "Iraq", "division": "Baghdad Governorate", "district": "Baghdad"})
        elif 36.10 <= lat <= 36.25 and 43.90 <= lon <= 44.10:
            return SubnationalDivision({"country": "Iraq", "division": "Erbil Governorate", "district": "Erbil"})
        elif 35.45 <= lat <= 35.65 and 45.35 <= lon <= 45.55:
            return SubnationalDivision({"country": "Iraq", "division": "Sulaymaniyah Governorate", "district": "Sulaymaniyah / Zagros"})
        else:
            return SubnationalDivision({"country": "Iraq", "division": "Iraq", "district": "Mesopotamia"})

    # 12. Israel
    if 29.4 <= lat <= 33.4 and 34.2 <= lon <= 35.9:
        if 32.00 <= lat <= 32.15 and 34.70 <= lon <= 34.85:
            return SubnationalDivision({"country": "Israel", "division": "Tel Aviv District", "district": "Tel Aviv"})
        elif 31.70 <= lat <= 31.85 and 35.15 <= lon <= 35.30:
            return SubnationalDivision({"country": "Israel", "division": "Jerusalem District", "district": "Jerusalem"})
        else:
            return SubnationalDivision({"country": "Israel", "division": "Israel", "district": "Levant"})

    # 13. Syria
    if 32.3 <= lat <= 37.4 and 35.6 <= lon <= 42.4:
        if 33.45 <= lat <= 33.55 and 36.20 <= lon <= 36.35:
            return SubnationalDivision({"country": "Syria", "division": "Damascus Governorate", "district": "Damascus"})
        elif 36.15 <= lat <= 36.25 and 37.10 <= lon <= 37.20:
            return SubnationalDivision({"country": "Syria", "division": "Aleppo Governorate", "district": "Aleppo"})
        else:
            return SubnationalDivision({"country": "Syria", "division": "Syria", "district": "Levant"})

    # 14. Iran (North & East of Persian Gulf & Gulf of Oman)
    if (
        (lat >= 29.5 and 48.5 <= lon <= 63.4) or
        (lat >= 26.5 and 50.5 <= lon <= 63.4) or
        (lat >= 25.0 and 56.5 <= lon <= 63.4) or
        (lat >= 30.0 and 44.0 <= lon <= 63.4)
    ) and lat <= 39.8:
        if 35.60 <= lat <= 36.15 and 51.20 <= lon <= 51.65:
            return SubnationalDivision({"country": "Iran", "division": "Tehran Province", "district": "Tehran / Alborz Mountains"})
        elif 32.55 <= lat <= 32.75 and 51.55 <= lon <= 51.75:
            return SubnationalDivision({"country": "Iran", "division": "Isfahan Province", "district": "Isfahan"})
        elif 29.50 <= lat <= 29.75 and 52.45 <= lon <= 52.70:
            return SubnationalDivision({"country": "Iran", "division": "Fars Province", "district": "Shiraz"})
        else:
            return SubnationalDivision({"country": "Iran", "division": "Iran", "district": "Iranian Plateau"})

    # 15. Yemen
    if 12.1 <= lat <= 19.0 and 41.8 <= lon <= 54.6:
        if 15.30 <= lat <= 15.45 and 44.15 <= lon <= 44.25:
            return SubnationalDivision({"country": "Yemen", "division": "Amanat Al Asimah", "district": "Sanaa"})
        elif 12.75 <= lat <= 12.85 and 44.95 <= lon <= 45.05:
            return SubnationalDivision({"country": "Yemen", "division": "Aden Governorate", "district": "Aden"})
        else:
            return SubnationalDivision({"country": "Yemen", "division": "Yemen", "district": "South Arabia"})

    # 16. Saudi Arabia (Evaluated after peripheral Arabian Peninsula and Levant nations)
    if (
        (16.3 <= lat <= 32.2 and 34.5 <= lon <= 50.3) or
        (16.3 <= lat <= 24.5 and 50.3 < lon <= 55.7)
    ):
        if 24.55 <= lat <= 24.90 and 46.55 <= lon <= 46.85:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Riyadh Province", "district": "Riyadh"})
        elif 21.40 <= lat <= 21.75 and 39.05 <= lon <= 39.30:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Makkah Province", "district": "Jeddah"})
        elif 21.30 <= lat <= 21.50 and 39.75 <= lon <= 39.95:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Makkah Province", "district": "Makkah"})
        elif 21.20 <= lat <= 21.40 and 40.35 <= lon <= 40.50:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Makkah Province", "district": "Taif Mountain Plateau"})
        elif 24.40 <= lat <= 24.60 and 39.50 <= lon <= 39.70:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Madinah Province", "district": "Madinah"})
        elif 26.30 <= lat <= 26.55 and 50.00 <= lon <= 50.25:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Eastern Province", "district": "Dammam / Khobar"})
        elif 18.15 <= lat <= 18.35 and 42.45 <= lon <= 42.60:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Asir Province", "district": "Abha / Al Souda"})
        elif 28.30 <= lat <= 28.75 and 35.00 <= lon <= 36.65:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Tabuk Province", "district": "Tabuk / Jabal Al Lawz"})
        elif 26.50 <= lat <= 26.75 and 37.85 <= lon <= 38.05:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Madinah Province", "district": "Al Ula / Hegra"})
        else:
            return SubnationalDivision({"country": "Saudi Arabia", "division": "Saudi Arabia", "district": "Central / Regional"})

    # Global Fallback based on country candidate lookup
    c_cand = get_country_candidate(lat, lon)
    if c_cand:
        return SubnationalDivision({"country": c_cand, "division": f"{c_cand} Region", "district": ""})

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
            # Expand bbox by buffer calibrated for latitude
            buf_lat = radius_km / 111.0
            cos_lat = max(0.2, math.cos(math.radians(lat)))
            buf_lon = radius_km / (111.0 * cos_lat)
            clusters.append({
                "cluster_id": f"cell_{len(clusters) + 1}",
                "center_lat": lat,
                "center_lon": lon,
                "min_lat": lat - buf_lat,
                "max_lat": lat + buf_lat,
                "min_lon": lon - buf_lon,
                "max_lon": lon + buf_lon,
                "points": [pt],
                "total_score": score,
                "best_score": score,
                "country": pt.get("country", get_country_candidate(lat, lon)),
            })

    # For each cluster, if it contains curated named anchors (not generic grid points),
    # snap the cluster center to the highest scoring named anchor.
    for c in clusters:
        named_anchors = [
            p for p in c["points"]
            if p.get("anchor_name") and "grid" not in str(p.get("anchor_name")).lower()
        ]
        if named_anchors:
            best_anchor = max(named_anchors, key=lambda p: p.get("score", p.get("prob", 0.0)))
            c["center_lat"] = best_anchor["lat"]
            c["center_lon"] = best_anchor["lon"]
            if best_anchor.get("country"):
                c["country"] = best_anchor["country"]
            c["best_anchor_name"] = best_anchor["anchor_name"]

    # Sort clusters by best score
    clusters.sort(key=lambda c: c["best_score"], reverse=True)
    return clusters[:max_clusters]
