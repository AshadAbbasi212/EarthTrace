"""Offline Transport & Settlement SQLite Gazetteer for sub-millisecond route and place matching."""
from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("geolocator.data.gazetteer")

DB_PATH = Path(__file__).parent / "gazetteer.sqlite"

# Seed dataset of key national highways and corridors
HIGHWAY_SEED_DATA = [
    # Pakistan
    ("M-1", "PK", "Pakistan", "Khyber Pakhtunkhwa / Punjab", "Islamabad - Peshawar Motorway (M-1)", 33.9550, 72.3500),
    ("M-2", "PK", "Pakistan", "Punjab", "Islamabad - Lahore Motorway (M-2)", 32.3500, 73.1000),
    ("M-3", "PK", "Pakistan", "Punjab", "Lahore - Abdul Hakeem Motorway (M-3)", 31.4000, 73.4000),
    ("M-4", "PK", "Pakistan", "Punjab", "Pindi Bhattian - Multan Motorway (M-4)", 30.9500, 72.2500),
    ("M-5", "PK", "Pakistan", "Punjab / Sindh", "Multan - Sukkur Motorway (M-5)", 28.7500, 70.3000),
    ("M-9", "PK", "Pakistan", "Sindh", "Karachi - Hyderabad Motorway (M-9)", 25.1500, 67.6500),
    ("M-11", "PK", "Pakistan", "Punjab", "Lahore - Sialkot Motorway (M-11)", 31.9500, 74.3500),
    ("M-15", "PK", "Pakistan", "Khyber Pakhtunkhwa", "Hazara Motorway (M-15)", 34.3500, 73.1500),
    ("N-5", "PK", "Pakistan", "Punjab / Sindh / KP", "Grand Trunk Road / National Highway 5", 31.6000, 73.8000),
    ("N-25", "PK", "Pakistan", "Balochistan / Sindh", "RCD Highway (Karachi - Quetta - Chaman)", 28.5000, 66.5000),
    ("N-35", "PK", "Pakistan", "Khyber Pakhtunkhwa / Gilgit", "Karakoram Highway (Hassan Abdal - Khunjerab)", 35.3000, 74.5000),
    ("N-55", "PK", "Pakistan", "Sindh / Punjab / KP", "Indus Highway", 29.8000, 70.5000),
    ("N-75", "PK", "Pakistan", "Punjab / Islamabad", "Murree Expressway (N-75 Islamabad - Murree)", 33.8800, 73.3500),

    # United Arab Emirates
    ("E11", "AE", "United Arab Emirates", "Dubai / Abu Dhabi", "Sheikh Zayed Road / E11 Highway", 25.0500, 55.1800),
    ("E311", "AE", "United Arab Emirates", "Dubai / Sharjah", "Sheikh Mohammed Bin Zayed Road (E311)", 25.1800, 55.3500),
    ("E611", "AE", "United Arab Emirates", "Dubai / Sharjah", "Emirates Road (E611)", 25.1000, 55.4500),
    ("E44", "AE", "United Arab Emirates", "Dubai", "Al Khail Road / Ras Al Khor / Hatta (E44)", 25.1500, 55.3000),
    ("E66", "AE", "United Arab Emirates", "Dubai / Abu Dhabi", "Dubai - Al Ain Road (E66)", 24.8000, 55.5000),

    # Saudi Arabia
    ("Route 40", "SA", "Saudi Arabia", "Riyadh / Makkah", "Highway 40 (Dammam - Riyadh - Jeddah)", 24.4500, 45.8000),
    ("Route 65", "SA", "Saudi Arabia", "Riyadh / Al-Qassim", "Highway 65 (Riyadh - Al-Qassim - Hail)", 26.2000, 44.1000),
    ("Route 80", "SA", "Saudi Arabia", "Northern Borders", "Highway 80 (Arar - Sakaka)", 30.2000, 41.5000),
    ("Route 15", "SA", "Saudi Arabia", "Makkah / Asir", "Highway 15 (Taif - Abha - Jizan)", 19.5000, 42.5000),

    # Kuwait
    ("Route 30", "KW", "Kuwait", "Al Ahmadi / Hawalli", "Fahaheel Expressway (Route 30)", 29.2000, 48.0800),
    ("Route 40", "KW", "Kuwait", "Capital / Al Ahmadi", "King Fahd Bin Abdulaziz Road (Route 40)", 29.1800, 48.0200),
    ("Route 50", "KW", "Kuwait", "Capital / Farwaniya", "Riyadh Expressway (Route 50)", 29.2800, 47.9600),
    ("Route 80", "KW", "Kuwait", "Al Jahra", "Jahra Road / Highway of Death (Route 80)", 29.3500, 47.7000),

    # Qatar
    ("Q1", "QA", "Qatar", "Al Daayen / Al Khor", "Al Shamal Road (Q1)", 25.5500, 51.4200),
    ("Q2", "QA", "Qatar", "Al Rayyan / Al Shahaniya", "Dukhan Highway (Q2)", 25.3500, 51.1000),
    ("Q3", "QA", "Qatar", "Al Rayyan / Al Wakrah", "Salwa Road (Q3)", 25.1000, 51.2000),

    # India
    ("NH-44", "IN", "India", "North / Central / South India", "National Highway 44 (Srinagar - Kanyakumari)", 26.5000, 78.0000),
    ("NH-48", "IN", "India", "Delhi / Maharashtra / Karnataka", "National Highway 48 (Delhi - Mumbai - Chennai)", 20.0000, 74.0000),
    ("NH-19", "IN", "India", "Delhi / Uttar Pradesh / West Bengal", "National Highway 19 (Delhi - Kolkata)", 25.5000, 83.0000),
    ("NH-27", "IN", "India", "Gujarat / Rajasthan / Assam", "East-West Corridor (NH-27)", 25.0000, 76.5000),

    # Turkiye
    ("O-1", "TR", "Turkiye", "Istanbul", "Istanbul Inner Ring Motorway (O-1)", 41.0300, 29.0200),
    ("O-2", "TR", "Turkiye", "Istanbul", "Fatih Sultan Mehmet Bridge Motorway (O-2)", 41.0900, 29.0600),
    ("O-4", "TR", "Turkiye", "Marmara / Central Anatolia", "Anatolian Motorway (Istanbul - Ankara O-4)", 40.8500, 31.0000),
    ("D-100", "TR", "Turkiye", "Marmara / Black Sea / Eastern", "State Road D-100 (Edirne - Istanbul - Iran Border)", 40.7500, 31.5000),
    ("D-400", "TR", "Turkiye", "Mediterranean", "State Road D-400 (Mugla - Antalya - Adana - Hakkari)", 36.8500, 31.5000),

    # Israel
    ("Route 6", "IL", "Israel", "Central / Northern", "Cross-Israel Highway (Route 6)", 32.1000, 34.9800),
    ("Route 1", "IL", "Israel", "Central / Jerusalem", "Highway 1 (Tel Aviv - Jerusalem)", 31.8200, 35.0500),
    ("Route 2", "IL", "Israel", "Coastal Plain", "Coastal Highway (Tel Aviv - Haifa)", 32.3500, 34.8800),
    ("Route 90", "IL", "Israel", "Jordan Valley / Arava", "Highway 90 (Metula - Dead Sea - Eilat)", 31.2500, 35.3800),

    # Iran
    ("Freeway 1", "IR", "Iran", "Gilan / Qazvin", "Qazvin - Rasht Freeway", 36.5000, 49.6000),
    ("Freeway 2", "IR", "Iran", "Tehran / East Azerbaijan", "Tehran - Tabriz Freeway", 36.8000, 48.5000),
    ("Freeway 5", "IR", "Iran", "Tehran / Khuzestan", "Tehran - Saveh - Bandar Imam", 33.5000, 49.0000),
    ("Freeway 7", "IR", "Iran", "Tehran / Isfahan", "Persian Gulf Freeway (Tehran - Qom - Isfahan)", 34.2000, 51.0000),

    # Egypt
    ("Cairo-Alexandria Desert Road", "EG", "Egypt", "Giza / Alexandria", "Cairo - Alexandria Desert Road", 30.5000, 30.4000),
    ("Regional Ring Road", "EG", "Egypt", "Greater Cairo", "Greater Cairo Regional Ring Road", 30.0500, 31.4000),
    ("Cairo-Suez Road", "EG", "Egypt", "Cairo / Suez", "Cairo - Suez Highway", 30.0800, 31.9000),

    # Worldwide key routes
    ("I-95", "US", "United States", "East Coast", "Interstate 95", 37.5000, -77.4000),
    ("I-80", "US", "United States", "Transcontinental", "Interstate 80", 41.2000, -96.0000),
    ("M1", "GB", "United Kingdom", "England", "M1 Motorway", 52.3000, -1.2000),
    ("M25", "GB", "United Kingdom", "London", "London Orbital Motorway (M25)", 51.5500, -0.2000),
    ("A1", "FR", "France", "Hauts-de-France", "Autoroute du Nord (A1)", 49.8000, 2.8000),
    ("A7", "DE", "Germany", "North-South", "Bundesautobahn 7", 51.2000, 9.7000),
]

# Seed dataset of key settlements and landmark urban hubs
SETTLEMENT_SEED_DATA = [
    # Pakistan
    ("Islamabad", "PK", "Pakistan", "Islamabad Capital Territory", 33.6844, 73.0479, "capital"),
    ("Rawalpindi", "PK", "Pakistan", "Punjab", 33.5651, 73.0169, "city"),
    ("Lahore", "PK", "Pakistan", "Punjab", 31.5204, 74.3587, "city"),
    ("Karachi", "PK", "Pakistan", "Sindh", 24.8607, 67.0011, "city"),
    ("Peshawar", "PK", "Pakistan", "Khyber Pakhtunkhwa", 34.0151, 71.5249, "city"),
    ("Quetta", "PK", "Pakistan", "Balochistan", 30.1798, 66.9750, "city"),
    ("Multan", "PK", "Pakistan", "Punjab", 30.1575, 71.5249, "city"),
    ("Faisalabad", "PK", "Pakistan", "Punjab", 31.4504, 73.1350, "city"),
    ("Murree", "PK", "Pakistan", "Punjab", 33.9070, 73.3943, "hill_station"),
    ("Abbottabad", "PK", "Pakistan", "Khyber Pakhtunkhwa", 34.1688, 73.2215, "city"),
    ("Muzaffarabad", "PK", "Pakistan", "Azad Kashmir", 34.3700, 73.4711, "city"),
    ("Gilgit", "PK", "Pakistan", "Gilgit-Baltistan", 35.9221, 74.3087, "city"),
    ("Skardu", "PK", "Pakistan", "Gilgit-Baltistan", 35.2971, 75.6333, "city"),
    ("Gwadar", "PK", "Pakistan", "Balochistan", 25.1264, 62.3225, "port"),

    # United Arab Emirates
    ("Dubai", "AE", "United Arab Emirates", "Dubai", 25.2048, 55.2708, "city"),
    ("Abu Dhabi", "AE", "United Arab Emirates", "Abu Dhabi", 24.4539, 54.3773, "capital"),
    ("Sharjah", "AE", "United Arab Emirates", "Sharjah", 25.3463, 55.4209, "city"),
    ("Al Ain", "AE", "United Arab Emirates", "Abu Dhabi", 24.2075, 55.7447, "city"),
    ("Ajman", "AE", "United Arab Emirates", "Ajman", 25.4052, 55.5136, "city"),
    ("Ras Al Khaimah", "AE", "United Arab Emirates", "Ras Al Khaimah", 25.7895, 55.9432, "city"),
    ("Fujairah", "AE", "United Arab Emirates", "Fujairah", 25.1288, 56.3265, "city"),

    # Saudi Arabia
    ("Riyadh", "SA", "Saudi Arabia", "Riyadh", 24.7136, 46.6753, "capital"),
    ("Jeddah", "SA", "Saudi Arabia", "Makkah", 21.5433, 39.1728, "city"),
    ("Makkah", "SA", "Saudi Arabia", "Makkah", 21.3891, 39.8579, "holy_city"),
    ("Medina", "SA", "Saudi Arabia", "Medina", 24.5247, 39.5692, "holy_city"),
    ("Dammam", "SA", "Saudi Arabia", "Eastern Province", 26.4207, 50.0888, "city"),
    ("Khobar", "SA", "Saudi Arabia", "Eastern Province", 26.2172, 50.1971, "city"),
    ("Tabuk", "SA", "Saudi Arabia", "Tabuk", 28.3835, 36.5662, "city"),
    ("Abha", "SA", "Saudi Arabia", "Asir", 18.2164, 42.5053, "city"),

    # Qatar
    ("Doha", "QA", "Qatar", "Ad Dawhah", 25.2854, 51.5310, "capital"),
    ("Al Rayyan", "QA", "Qatar", "Al Rayyan", 25.2919, 51.4244, "city"),
    ("Al Wakrah", "QA", "Qatar", "Al Wakrah", 25.1768, 51.6048, "city"),
    ("Lusail", "QA", "Qatar", "Al Daayen", 25.4194, 51.4934, "city"),
    ("Al Khor", "QA", "Qatar", "Al Khor", 25.6839, 51.5058, "city"),

    # Kuwait
    ("Kuwait City", "KW", "Kuwait", "Capital", 29.3759, 47.9774, "capital"),
    ("Hawally", "KW", "Kuwait", "Hawally", 29.3328, 48.0281, "city"),
    ("Salmiya", "KW", "Kuwait", "Hawally", 29.3344, 48.0772, "city"),
    ("Al Jahra", "KW", "Kuwait", "Al Jahra", 29.3375, 47.6581, "city"),
    ("Ahmadi", "KW", "Kuwait", "Al Ahmadi", 29.0769, 48.0839, "city"),

    # Bahrain
    ("Manama", "BH", "Bahrain", "Capital", 26.2285, 50.5860, "capital"),
    ("Riffa", "BH", "Bahrain", "Southern", 26.1300, 50.5550, "city"),
    ("Muharraq", "BH", "Bahrain", "Muharraq", 26.2572, 50.6119, "city"),

    # Oman
    ("Muscat", "OM", "Oman", "Muscat", 23.5880, 58.3829, "capital"),
    ("Salalah", "OM", "Oman", "Dhofar", 17.0151, 54.0924, "city"),
    ("Sohar", "OM", "Oman", "Al Batinah North", 24.3461, 56.7075, "city"),
    ("Nizwa", "OM", "Oman", "Ad Dakhiliyah", 22.9333, 57.5333, "city"),

    # Iran
    ("Tehran", "IR", "Iran", "Tehran", 35.6892, 51.3890, "capital"),
    ("Mashhad", "IR", "Iran", "Razavi Khorasan", 36.2972, 59.6067, "city"),
    ("Isfahan", "IR", "Iran", "Isfahan", 32.6546, 51.6680, "city"),
    ("Shiraz", "IR", "Iran", "Fars", 29.5918, 52.5837, "city"),
    ("Tabriz", "IR", "Iran", "East Azerbaijan", 38.0800, 46.2919, "city"),

    # India
    ("New Delhi", "IN", "India", "Delhi", 28.6139, 77.2090, "capital"),
    ("Mumbai", "IN", "India", "Maharashtra", 19.0760, 72.8777, "city"),
    ("Bengaluru", "IN", "India", "Karnataka", 12.9716, 77.5946, "city"),
    ("Hyderabad", "IN", "India", "Telangana", 17.3850, 78.4867, "city"),
    ("Chennai", "IN", "India", "Tamil Nadu", 13.0827, 80.2707, "city"),
    ("Kolkata", "IN", "India", "West Bengal", 22.5726, 88.3639, "city"),
    ("Jaipur", "IN", "India", "Rajasthan", 26.9124, 75.7873, "city"),
    ("Srinagar", "IN", "India", "Jammu and Kashmir", 34.0837, 74.7973, "city"),

    # Egypt
    ("Cairo", "EG", "Egypt", "Cairo", 30.0444, 31.2357, "capital"),
    ("Alexandria", "EG", "Egypt", "Alexandria", 31.2001, 29.9187, "city"),
    ("Giza", "EG", "Egypt", "Giza", 30.0131, 31.2089, "city"),
    ("Luxor", "EG", "Egypt", "Luxor", 25.6872, 32.6396, "city"),
    ("Aswan", "EG", "Egypt", "Aswan", 24.0889, 32.8998, "city"),

    # Turkiye
    ("Ankara", "TR", "Turkiye", "Ankara", 39.9334, 32.8597, "capital"),
    ("Istanbul", "TR", "Turkiye", "Istanbul", 41.0082, 28.9784, "city"),
    ("Izmir", "TR", "Turkiye", "Izmir", 38.4237, 27.1428, "city"),
    ("Antalya", "TR", "Turkiye", "Antalya", 36.8969, 30.7133, "city"),
    ("Bursa", "TR", "Turkiye", "Bursa", 40.1885, 29.0610, "city"),

    # Israel
    ("Jerusalem", "IL", "Israel", "Jerusalem District", 31.7683, 35.2137, "capital"),
    ("Tel Aviv", "IL", "Israel", "Tel Aviv District", 32.0853, 34.7818, "city"),
    ("Haifa", "IL", "Israel", "Haifa District", 32.7940, 34.9896, "city"),
    ("Beersheba", "IL", "Israel", "Southern District", 31.2529, 34.7915, "city"),

    # Iraq
    ("Baghdad", "IQ", "Iraq", "Baghdad", 33.3152, 44.3661, "capital"),
    ("Basra", "IQ", "Iraq", "Basra", 30.5081, 47.7835, "city"),
    ("Erbil", "IQ", "Iraq", "Kurdistan Region", 36.1911, 44.0092, "city"),
    ("Mosul", "IQ", "Iraq", "Nineveh", 36.3400, 43.1300, "city"),

    # Syria
    ("Damascus", "SY", "Syria", "Damascus", 33.5138, 36.2765, "capital"),
    ("Aleppo", "SY", "Syria", "Aleppo", 36.2021, 37.1343, "city"),
    ("Homs", "SY", "Syria", "Homs", 34.7324, 36.7137, "city"),
    ("Latakia", "SY", "Syria", "Latakia", 35.5317, 35.7900, "port"),

    # Yemen
    ("Sana'a", "YE", "Yemen", "Amanat Al Asimah", 15.3694, 44.1910, "capital"),
    ("Aden", "YE", "Yemen", "Aden", 12.7855, 45.0187, "port"),
]


def init_gazetteer_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize SQLite gazetteer schema and populate seed data if empty."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS highways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_code TEXT NOT NULL COLLATE NOCASE,
                iso2 TEXT NOT NULL COLLATE NOCASE,
                country TEXT NOT NULL,
                subdivision TEXT NOT NULL,
                corridor_name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hw_route ON highways(route_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hw_iso ON highways(iso2)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS settlements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE,
                iso2 TEXT NOT NULL COLLATE NOCASE,
                country TEXT NOT NULL,
                subdivision TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                category TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_settle_name ON settlements(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_settle_iso ON settlements(iso2)")

        # Check if highways populated
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM highways")
        hw_count = cur.fetchone()[0]
        if hw_count == 0:
            logger.info("Seeding %d national highways into local gazetteer...", len(HIGHWAY_SEED_DATA))
            cur.executemany(
                "INSERT INTO highways (route_code, iso2, country, subdivision, corridor_name, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)",
                HIGHWAY_SEED_DATA,
            )

        cur.execute("SELECT COUNT(*) FROM settlements")
        st_count = cur.fetchone()[0]
        if st_count == 0:
            logger.info("Seeding %d settlements into local gazetteer...", len(SETTLEMENT_SEED_DATA))
            cur.executemany(
                "INSERT INTO settlements (name, iso2, country, subdivision, lat, lon, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
                SETTLEMENT_SEED_DATA,
            )

    return conn


# Singleton connection
_CONN: Optional[sqlite3.Connection] = None


def get_gazetteer_connection() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        _CONN = init_gazetteer_db()
    return _CONN


def query_offline_gazetteer(query: str, country_iso: Optional[str] = None) -> List[Dict[str, Any]]:
    """Query the local SQLite gazetteer for exact or prefix matches on highways and settlements."""
    q = query.strip()
    if not q or len(q) < 2:
        return []

    # Clean punctuation: e.g. "M-1" -> match "M-1" or "M1", "N-75" -> "N-75" or "N75"
    cleaned_route = re.sub(r"[\s\-_]+", "", q).upper()
    route_with_dash = re.sub(r"^([A-Z]+)(\d+)$", r"\1-\2", cleaned_route)

    conn = get_gazetteer_connection()
    cur = conn.cursor()
    results: List[Dict[str, Any]] = []

    # 1. Highway match
    hw_sql = "SELECT * FROM highways WHERE (route_code = ? OR route_code = ? OR route_code = ?)"
    params: List[Any] = [q, cleaned_route, route_with_dash]
    if country_iso:
        hw_sql += " AND iso2 = ?"
        params.append(country_iso.upper())

    cur.execute(hw_sql, params)
    for row in cur.fetchall():
        results.append({
            "place_id": f"gaz_hw_{row['id']}",
            "lat": str(row["lat"]),
            "lon": str(row["lon"]),
            "display_name": f"{row['corridor_name']}, {row['subdivision']}, {row['country']}",
            "type": "highway",
            "country": row["country"],
            "country_code": row["iso2"].lower(),
            "subdivision": row["subdivision"],
            "importance": 0.85,
            "address": {
                "road": row["corridor_name"],
                "state": row["subdivision"],
                "country": row["country"],
                "country_code": row["iso2"].lower(),
            },
        })

    if results:
        return results

    # 2. Settlement match
    settle_sql = "SELECT * FROM settlements WHERE (name = ? OR name LIKE ?)"
    s_params: List[Any] = [q, f"{q}%"]
    if country_iso:
        settle_sql += " AND iso2 = ?"
        s_params.append(country_iso.upper())

    cur.execute(settle_sql, s_params)
    for row in cur.fetchall():
        results.append({
            "place_id": f"gaz_st_{row['id']}",
            "lat": str(row["lat"]),
            "lon": str(row["lon"]),
            "display_name": f"{row['name']}, {row['subdivision']}, {row['country']}",
            "type": row["category"],
            "country": row["country"],
            "country_code": row["iso2"].lower(),
            "subdivision": row["subdivision"],
            "importance": 0.80,
            "address": {
                "city": row["name"],
                "state": row["subdivision"],
                "country": row["country"],
                "country_code": row["iso2"].lower(),
            },
        })

    return results
