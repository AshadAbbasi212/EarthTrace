"""Unit and integration tests for 15-country regional specialization and disambiguation."""
import pytest

from geolocator.pipeline.geo_utils import (
    COUNTRY_BBOXES,
    COUNTRY_ANCHORS,
    get_country_candidate,
    get_country_anchors,
    get_subnational_division,
)
from geolocator.adapters.clues_adapter import (
    CC_TLD_MAP,
    SCRIPT_PATTERNS,
    GEO_PHONETIC_SYNONYMS,
    detect_tld,
    detect_script,
    extract_candidate_place_phrases,
)
from geolocator.pipeline.stage2_prior import GLOBAL_GEOLOC_COUNTRIES

TARGET_COUNTRIES = [
    "Pakistan", "India", "Iran", "United Arab Emirates", "Qatar", "Kuwait",
    "Saudi Arabia", "Yemen", "Egypt", "Oman", "Iraq", "Israel", "Syria",
    "Turkey", "Bahrain"
]


def test_target_countries_registered_in_bboxes_and_anchors():
    """Verify all 15 prioritized countries are present in bboxes and anchor grids."""
    for country in TARGET_COUNTRIES:
        assert country in COUNTRY_BBOXES, f"Missing {country} in COUNTRY_BBOXES"
        assert country in COUNTRY_ANCHORS, f"Missing {country} in COUNTRY_ANCHORS"
        anchors = get_country_anchors(country, max_anchors=10)
        assert len(anchors) >= 6, f"Expected dense anchor grid for {country}, got {len(anchors)}"
        for a in anchors:
            assert "name" in a
            assert "lat" in a and "lon" in a


def test_target_countries_in_global_geoloc_countries():
    """Verify all 15 prioritized countries are registered in vision-language country universe."""
    for country in TARGET_COUNTRIES:
        assert country in GLOBAL_GEOLOC_COUNTRIES, f"Missing {country} in GLOBAL_GEOLOC_COUNTRIES"


def test_arabian_peninsula_precise_border_disambiguation():
    """Verify that small Gulf states are never misclassified as Saudi Arabia or neighbors."""
    test_coordinates = [
        # (lat, lon, expected_country)
        (25.2854, 51.5310, "Qatar"),                 # Doha
        (25.6800, 51.5000, "Qatar"),                 # Al Khor
        (24.8900, 51.2500, "Qatar"),                 # Mesaieed
        (26.2285, 50.5860, "Bahrain"),               # Manama
        (26.1500, 50.5500, "Bahrain"),               # Riffa
        (29.3759, 47.9774, "Kuwait"),                # Kuwait City
        (29.0700, 48.1300, "Kuwait"),                # Al Ahmadi
        (25.2048, 55.2708, "United Arab Emirates"),  # Dubai
        (24.4539, 54.3773, "United Arab Emirates"),  # Abu Dhabi
        (24.2000, 55.7500, "United Arab Emirates"),  # Al Ain
        (23.5859, 58.4059, "Oman"),                  # Muscat
        (17.0150, 54.0924, "Oman"),                  # Salalah
        (24.7136, 46.6753, "Saudi Arabia"),          # Riyadh
        (21.5433, 39.1728, "Saudi Arabia"),          # Jeddah
        (26.4207, 50.0888, "Saudi Arabia"),          # Dammam
        (30.0444, 31.2357, "Egypt"),                 # Cairo
        (31.2001, 29.9187, "Egypt"),                 # Alexandria
        (35.6892, 51.3890, "Iran"),                  # Tehran
        (29.5926, 52.5836, "Iran"),                  # Shiraz
        (33.6844, 73.0479, "Pakistan"),              # Islamabad
        (31.5204, 74.3587, "Pakistan"),              # Lahore
        (28.6139, 77.2090, "India"),                 # Delhi
        (19.0760, 72.8777, "India"),                 # Mumbai
        (31.7683, 35.2137, "Israel"),                # Jerusalem
        (32.0853, 34.7818, "Israel"),                # Tel Aviv
        (33.3152, 44.3661, "Iraq"),                  # Baghdad
        (30.5081, 47.7835, "Iraq"),                  # Basra
        (33.5138, 36.2765, "Syria"),                 # Damascus
        (36.2021, 37.1343, "Syria"),                 # Aleppo
        (41.0082, 28.9784, "Turkey"),                # Istanbul
        (39.9334, 32.8597, "Turkey"),                # Ankara
        (15.3694, 44.1910, "Yemen"),                 # Sanaa
        (12.7855, 45.0187, "Yemen"),                 # Aden
    ]

    for lat, lon, expected in test_coordinates:
        cand = get_country_candidate(lat, lon)
        assert cand == expected, f"Point ({lat}, {lon}) expected {expected}, got {cand}"


def test_subnational_division_resolution():
    """Verify coordinate mapping to provinces, governorates, and districts."""
    test_cases = [
        (33.59, 73.04, "Rawalpindi"),             # Punjab / Rawalpindi
        (33.72, 73.08, "Islamabad"),              # Islamabad Capital Territory
        (31.52, 74.35, "Punjab"),                 # Lahore
        (24.86, 67.00, "Sindh"),                  # Karachi
        (34.01, 71.52, "Khyber Pakhtunkhwa"),     # Peshawar
        (25.20, 55.27, "Dubai"),                  # Emirate of Dubai
        (24.45, 54.37, "Abu Dhabi"),              # Emirate of Abu Dhabi
        (25.35, 55.40, "Sharjah"),                # Emirate of Sharjah
        (25.28, 51.53, "Doha"),                   # Doha Municipality
        (25.68, 51.50, "Al Khor"),                # Al Khor
        (26.22, 50.58, "Capital Governorate"),    # Bahrain Capital
        (29.37, 47.97, "Capital Governorate"),    # Kuwait Capital
        (29.07, 48.13, "Ahmadi"),                 # Al Ahmadi
        (24.71, 46.67, "Riyadh"),                 # Riyadh Province
        (21.54, 39.17, "Makkah"),                 # Makkah Province
        (26.42, 50.08, "Eastern Province"),       # Eastern Province (Dammam)
        (23.58, 58.40, "Muscat"),                 # Muscat Governorate
        (17.01, 54.09, "Dhofar"),                 # Dhofar Governorate
        (30.04, 31.23, "Cairo"),                  # Cairo Governorate
        (31.20, 29.91, "Alexandria"),             # Alexandria Governorate
        (35.68, 51.38, "Tehran"),                 # Tehran Province
        (32.65, 51.66, "Isfahan"),                # Isfahan Province
        (41.00, 28.97, "Istanbul"),               # Istanbul Province
        (39.93, 32.85, "Ankara"),                 # Ankara Province
        (33.31, 44.36, "Baghdad"),                # Baghdad Governorate
        (31.76, 35.21, "Jerusalem"),              # Jerusalem District
        (32.08, 34.78, "Tel Aviv"),               # Tel Aviv District
        (33.51, 36.27, "Damascus"),               # Damascus Governorate
        (15.36, 44.19, "Amanat Al Asimah"),       # Sanaa
        (28.61, 77.20, "Delhi"),                  # National Capital Territory
        (19.07, 72.87, "Maharashtra"),            # Mumbai
    ]

    for lat, lon, expected_substr in test_cases:
        subdiv = get_subnational_division(lat, lon)
        assert subdiv is not None, f"Expected subnational division for ({lat}, {lon})"
        assert expected_substr.lower() in subdiv.lower(), f"Expected '{expected_substr}' in '{subdiv}' for ({lat}, {lon})"


def test_cctld_detection_all_15_countries():
    """Verify ccTLDs and compound domains resolve correctly."""
    tld_cases = [
        ("visit.com.pk", "Pakistan"),
        ("news.pk", "Pakistan"),
        ("shop.co.in", "India"),
        ("site.in", "India"),
        ("uni.ac.ir", "Iran"),
        ("portal.co.ir", "Iran"),
        ("dubai.ae", "United Arab Emirates"),
        ("bank.co.ae", "United Arab Emirates"),
        ("doha.qa", "Qatar"),
        ("qatar.com.qa", "Qatar"),
        ("store.kw", "Kuwait"),
        ("kuwait.com.kw", "Kuwait"),
        ("saudi.sa", "Saudi Arabia"),
        ("riyadh.com.sa", "Saudi Arabia"),
        ("aden.ye", "Yemen"),
        ("cairo.eg", "Egypt"),
        ("alex.com.eg", "Egypt"),
        ("muscat.om", "Oman"),
        ("oman.co.om", "Oman"),
        ("baghdad.iq", "Iraq"),
        ("israel.il", "Israel"),
        ("telaviv.co.il", "Israel"),
        ("syria.sy", "Syria"),
        ("istanbul.tr", "Turkey"),
        ("ankara.com.tr", "Turkey"),
        ("manama.bh", "Bahrain"),
        ("bahrain.com.bh", "Bahrain"),
    ]

    for domain, expected in tld_cases:
        res = detect_tld(domain)
        assert res is not None, f"Failed to detect TLD in '{domain}'"
        assert res["country"] == expected, f"Domain '{domain}' expected {expected}, got {res['country']}"


def test_script_detection():
    """Verify distinct script classification."""
    # Distinct Urdu: contains ٹ or ے
    urdu_res = detect_script("ٹریفک کے قواعد")
    assert urdu_res is not None
    assert urdu_res["script"] == "urdu_distinctive"
    assert "Pakistan" in urdu_res["candidate_countries"]

    # Distinct Persian: contains گ or پ or چ
    persian_res = detect_script("بزرگراه شهید چمران")
    assert persian_res is not None
    assert persian_res["script"] == "persian_distinctive"
    assert "Iran" in persian_res["candidate_countries"]

    # Hebrew
    hebrew_res = detect_script("כביש מספר 6")
    assert hebrew_res is not None
    assert hebrew_res["script"] == "hebrew"
    assert "Israel" in hebrew_res["candidate_countries"]

    # Arabic
    arabic_res = detect_script("شارع الشيخ زايد")
    assert arabic_res is not None
    assert arabic_res["script"] == "arabic"
    assert "Saudi Arabia" in arabic_res["candidate_countries"]
    assert "United Arab Emirates" in arabic_res["candidate_countries"]

    # Devanagari
    devanagari_res = detect_script("राष्ट्रीय राजमार्ग 44")
    assert devanagari_res is not None
    assert devanagari_res["script"] == "devanagari"
    assert "India" in devanagari_res["candidate_countries"]


def test_expressway_and_highway_gazetteer():
    """Verify highway route codes match and resolve across all target countries."""
    highway_samples = [
        "E11", "E311", "E611", "E44", "Route 40", "Route 65", "Route 30",
        "Route 80", "Q1", "Q2", "Q3", "M-1", "M-2", "M-9", "M-15",
        "N-75", "N-35", "N-5", "NH-44", "NH-48", "O-1", "O-4", "D-100", "D-400"
    ]

    for hw in highway_samples:
        assert hw in GEO_PHONETIC_SYNONYMS, f"Missing route {hw} in GEO_PHONETIC_SYNONYMS"
        resolved = GEO_PHONETIC_SYNONYMS[hw]
        assert len(resolved) > len(hw), f"Expected detailed geocodable name for {hw}, got {resolved}"

    # Verify phrase extractor pulls highway codes
    cands = extract_candidate_place_phrases("Exit to E11 toward Dubai Downtown")
    assert any("E11" in c for c in cands)

    cands_nh = extract_candidate_place_phrases("Toll plaza on NH-44 near Hyderabad")
    assert any("NH-44" in c for c in cands_nh)
