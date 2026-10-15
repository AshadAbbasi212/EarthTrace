"""Adapter wrapping vendored clues.py for tabular knowledge lookups."""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

VENDOR_SCRIPTS = Path(__file__).resolve().parent.parent.parent.parent / "vendor" / "geo-sleuth" / "skills" / "geo-sleuth" / "scripts"
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

import clues

logger = logging.getLogger("geolocator.adapters.clues")


def lookup_plate(prefix: str) -> Optional[Dict[str, Any]]:
    """Lookup license plate prefix (China) -> province and prefecture/city."""
    try:
        data_file = clues.DATA / "cn_plates.json"
        if data_file.exists():
            table = json.loads(data_file.read_text(encoding="utf-8"))
            prov_char = prefix[0]
            letter = prefix[1:].upper() if len(prefix) > 1 else ""
            # Chinese license plates strictly require a province character followed by an ASCII letter (e.g. 京A, 粤B)
            if prov_char in table and letter and letter.isalpha() and letter.isascii():
                info = table[prov_char]
                letters = info.get("letters", {})
                detail = letters.get(letter, "")
                return {
                    "code": prefix,
                    "province": info.get("province"),
                    "city": detail.split("、")[0] if detail else info.get("province"),
                    "detail": detail,
                }
    except Exception as e:
        logger.debug("Plate lookup failed for %s: %s", prefix, e)
    return None


def lookup_driving_side(country_name: str) -> Optional[str]:
    """Lookup traffic driving side (left or right) for country."""
    try:
        data_file = clues.DATA / "driving_side.json"
        if data_file.exists():
            table = json.loads(data_file.read_text(encoding="utf-8"))
            country_clean = country_name.strip().lower()
            if country_clean == "uk":
                country_clean = "united kingdom"
            elif country_clean in ("us", "usa"):
                country_clean = "united states"

            # 1. Exact match
            for key, val in table.items():
                if key == "_meta":
                    continue
                if key.lower() == country_clean:
                    return val.get("side")

            # 2. Substring / alias match
            for key, val in table.items():
                if key == "_meta":
                    continue
                k_lower = key.lower()
                if country_clean in k_lower or k_lower in country_clean:
                    return val.get("side")
    except Exception as e:
        logger.debug("Driving side lookup failed for %s: %s", country_name, e)
    return None


def lookup_calling_code(code: str) -> Optional[Dict[str, Any]]:
    """Lookup international dialing code -> country."""
    try:
        clean_code = code.lstrip("+").strip()
        data_file = clues.DATA / "calling_codes.json"
        if data_file.exists():
            table = json.loads(data_file.read_text(encoding="utf-8"))
            if clean_code in table:
                entries = table[clean_code]
                if entries and isinstance(entries, list):
                    return entries[0]
    except Exception as e:
        logger.debug("Calling code lookup failed for %s: %s", code, e)
    return None


def lookup_territory(country_name: str, continent: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lookup overseas territories and dependencies for sovereign state."""
    try:
        data_file = clues.DATA / "territories.json"
        if data_file.exists():
            table = json.loads(data_file.read_text(encoding="utf-8"))
            matches = []
            
            # Table is a dict where keys are territory names
            for t_name, t_info in table.items():
                if t_name == "_meta":
                    continue
                sov = t_info.get("sovereign", "")
                if sov.lower() == country_name.lower():
                    entry = {"name": t_name, **t_info}
                    if continent:
                        reg = t_info.get("region", "").lower()
                        subreg = t_info.get("subregion", "").lower()
                        if continent.lower() in (reg, subreg):
                            matches.append(entry)
                    else:
                        matches.append(entry)

            for extra in clues.INTEGRAL_OVERSEAS:
                if extra.get("sovereign", "").lower() == country_name.lower():
                    if continent:
                        if continent.lower() in (extra.get("region", "").lower(), extra.get("subregion", "").lower()):
                            matches.append(extra)
                    else:
                        matches.append(extra)
            return matches
    except Exception as e:
        logger.debug("Territory lookup failed for %s: %s", country_name, e)
    return []


# ---------------------------------------------------------------------------
# Geoguessr Meta & Visual Clue Lookups (Scripts, TLDs, Calling Codes)
# ---------------------------------------------------------------------------

COUNTRY_NAME_TO_ISO: Dict[str, str] = {
    "afghanistan": "af", "albania": "al", "algeria": "dz", "argentina": "ar",
    "armenia": "am", "australia": "au", "austria": "at", "azerbaijan": "az",
    "bahrain": "bh", "bangladesh": "bd", "belarus": "by", "belgium": "be",
    "bolivia": "bo", "bosnia and herzegovina": "ba", "brazil": "br", "bulgaria": "bg",
    "cambodia": "kh", "canada": "ca", "chile": "cl", "china": "cn",
    "colombia": "co", "croatia": "hr", "cuba": "cu", "cyprus": "cy",
    "czech republic": "cz", "czechia": "cz", "denmark": "dk", "ecuador": "ec",
    "egypt": "eg", "estonia": "ee", "ethiopia": "et", "finland": "fi",
    "france": "fr", "georgia": "ge", "germany": "de", "ghana": "gh",
    "greece": "gr", "hungary": "hu", "iceland": "is", "india": "in",
    "indonesia": "id", "iran": "ir", "iraq": "iq", "ireland": "ie",
    "israel": "il", "italy": "it", "japan": "jp", "jordan": "jo",
    "kazakhstan": "kz", "kenya": "ke", "kuwait": "kw", "kyrgyzstan": "kg",
    "latvia": "lv", "lebanon": "lb", "libya": "ly", "lithuania": "lt",
    "luxembourg": "lu", "malaysia": "my", "mexico": "mx", "mongolia": "mn",
    "morocco": "ma", "nepal": "np", "netherlands": "nl", "new zealand": "nz",
    "nigeria": "ng", "norway": "no", "oman": "om", "pakistan": "pk",
    "peru": "pe", "philippines": "ph", "poland": "pl", "portugal": "pt",
    "qatar": "qa", "romania": "ro", "russia": "ru", "saudi arabia": "sa",
    "serbia": "rs", "singapore": "sg", "slovakia": "sk", "slovenia": "si",
    "south africa": "za", "south korea": "kr", "korea, south": "kr", "korea": "kr",
    "spain": "es", "sri lanka": "lk", "sweden": "se", "switzerland": "ch",
    "taiwan": "tw", "tajikistan": "tj", "thailand": "th", "tunisia": "tn",
    "turkey": "tr", "türkiye": "tr", "ukraine": "ua", "united arab emirates": "ae",
    "uae": "ae", "united kingdom": "gb", "uk": "gb", "great britain": "gb",
    "united states": "us", "usa": "us", "united states of america": "us",
    "uzbekistan": "uz", "venezuela": "ve", "vietnam": "vn",
}


def country_to_iso(name: str) -> Optional[str]:
    """Convert country name or alias to 2-letter ISO 3166-1 alpha-2 code."""
    if not name:
        return None
    clean = name.strip().lower()
    if clean in COUNTRY_NAME_TO_ISO:
        return COUNTRY_NAME_TO_ISO[clean]
    for k, iso in COUNTRY_NAME_TO_ISO.items():
        if k in clean or clean in k:
            return iso
    return None


CC_TLD_MAP: Dict[str, str] = {
    # 15 Prioritized Target Countries
    "pk": "Pakistan",
    "com.pk": "Pakistan",
    "org.pk": "Pakistan",
    "gov.pk": "Pakistan",
    "edu.pk": "Pakistan",
    "in": "India",
    "co.in": "India",
    "net.in": "India",
    "gov.in": "India",
    "ir": "Iran",
    "co.ir": "Iran",
    "ae": "United Arab Emirates",
    "co.ae": "United Arab Emirates",
    "qa": "Qatar",
    "com.qa": "Qatar",
    "kw": "Kuwait",
    "com.kw": "Kuwait",
    "sa": "Saudi Arabia",
    "com.sa": "Saudi Arabia",
    "ye": "Yemen",
    "com.ye": "Yemen",
    "eg": "Egypt",
    "com.eg": "Egypt",
    "om": "Oman",
    "co.om": "Oman",
    "iq": "Iraq",
    "com.iq": "Iraq",
    "il": "Israel",
    "co.il": "Israel",
    "sy": "Syria",
    "com.sy": "Syria",
    "tr": "Turkey",
    "com.tr": "Turkey",
    "gov.tr": "Turkey",
    "bh": "Bahrain",
    "com.bh": "Bahrain",
    # Worldwide
    "de": "Germany",
    "uk": "United Kingdom",
    "co.uk": "United Kingdom",
    "fr": "France",
    "it": "Italy",
    "es": "Spain",
    "pl": "Poland",
    "ru": "Russia",
    "br": "Brazil",
    "com.br": "Brazil",
    "jp": "Japan",
    "co.jp": "Japan",
    "au": "Australia",
    "com.au": "Australia",
    "ca": "Canada",
    "nz": "New Zealand",
    "co.nz": "New Zealand",
    "za": "South Africa",
    "co.za": "South Africa",
    "mx": "Mexico",
    "com.mx": "Mexico",
    "ar": "Argentina",
    "com.ar": "Argentina",
    "cl": "Chile",
    "ch": "Switzerland",
    "at": "Austria",
    "se": "Sweden",
    "no": "Norway",
    "fi": "Finland",
    "nl": "Netherlands",
    "be": "Belgium",
    "cz": "Czech Republic",
    "ro": "Romania",
    "hu": "Hungary",
    "pt": "Portugal",
    "ie": "Ireland",
    "dk": "Denmark",
    "gr": "Greece",
    "kr": "South Korea",
    "co.kr": "South Korea",
    "id": "Indonesia",
    "co.id": "Indonesia",
    "th": "Thailand",
    "co.th": "Thailand",
    "vn": "Vietnam",
    "sg": "Singapore",
    "com.sg": "Singapore",
    "my": "Malaysia",
    "com.my": "Malaysia",
    "ph": "Philippines",
    "ua": "Ukraine",
    "is": "Iceland",
}

SCRIPT_PATTERNS = [
    # Distinctive Urdu characters: 0679(ٹ), 0688(ڈ), 0691(ڑ), 06BA(ں), 06D2(ے)
    ("urdu_distinctive", re.compile(r"[\u0679\u0688\u0691\u06BA\u06D2]"), ["Pakistan", "India"]),
    # Distinctive Persian characters: 067E(پ), 0686(چ), 0698(ژ), 06AF(گ)
    ("persian_distinctive", re.compile(r"[\u067E\u0686\u0698\u06AF]"), ["Iran", "Afghanistan", "Pakistan"]),
    # Hebrew script: 0590-05FF
    ("hebrew", re.compile(r"[\u0590-\u05FF]"), ["Israel"]),
    # General Arabic script: 0600-06FF
    ("arabic", re.compile(r"[\u0600-\u06FF]"), [
        "Saudi Arabia", "United Arab Emirates", "Egypt", "Qatar", "Kuwait",
        "Oman", "Yemen", "Iraq", "Syria", "Bahrain", "Jordan", "Morocco", "Pakistan", "Iran"
    ]),
    # Devanagari script: 0900-097F
    ("devanagari", re.compile(r"[\u0900-\u097F]"), ["India", "Nepal"]),
    # Other Indic scripts (Gurmukhi, Bengali, Tamil, Telugu)
    ("gurmukhi", re.compile(r"[\u0A00-\u0A7F]"), ["India"]),
    ("bengali", re.compile(r"[\u0980-\u09FF]"), ["India", "Bangladesh"]),
    ("tamil", re.compile(r"[\u0B80-\u0BFF]"), ["India", "Sri Lanka"]),
    ("telugu", re.compile(r"[\u0C00-\u0C7F]"), ["India"]),
    # Cyrillic
    ("cyrillic", re.compile(r"[\u0400-\u04FF]"), ["Russia", "Ukraine", "Belarus", "Bulgaria", "Serbia", "Kazakhstan", "Kyrgyzstan", "Mongolia", "North Macedonia"]),
    # Greek
    ("greek", re.compile(r"[\u0370-\u03FF]"), ["Greece", "Cyprus"]),
    # East Asian scripts
    ("hangul", re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]"), ["South Korea"]),
    ("japanese_kana", re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"), ["Japan"]),
    ("thai", re.compile(r"[\u0E00-\u0E7F]"), ["Thailand"]),
    ("hanzi_kanji", re.compile(r"[\u4E00-\u9FFF]"), ["Japan", "China", "Taiwan", "Hong Kong", "Singapore"]),
]

COMMON_STOP_WORDS = {
    "hotel", "restaurant", "cafe", "coffee", "bar", "pub", "supermarket", "market",
    "shop", "store", "bank", "pharmacy", "farmacia", "apotheke", "police", "hospital",
    "open", "closed", "entrance", "exit", "stop", "parking", "station", "train", "bus",
    "metro", "subway", "taxi", "airport", "welcome", "street", "avenue", "road", "str",
    "drive", "lane", "way", "highway", "expressway", "toll", "free", "city", "center",
    "north", "south", "east", "west", "the", "and", "for", "with", "from", "service",
    "wc", "info", "information", "ticket", "tickets", "fast", "food", "express", "auto",
    "seat", "belt", "seatbelt", "seatbeit", "beit", "nyok", "nyoi", "speed", "limit", "slow",
    "safe", "safety", "fasten", "buckle", "caution", "danger", "warning", "toll plaza",
    "vehicle", "traffic", "rules", "fine", "penalty", "camera", "km/h", "mph", "post", "check",
    "seat belt", "seat beit",
    # Generic sign phrases and markers
    "historic", "historical", "birthplace", "monument", "memorial", "visitor", "visitors",
    "museum", "famous", "scenic", "byway", "route", "national", "park", "heritage",
    "lookout", "viewpoint", "preservation", "historical marker", "marker", "welcome to",
    "welcome", "border", "welcome to the", "landmark", "state line", "country store",
    "trading post", "mile", "miles", "junction", "intersection", "turnpike",
    # Urdu / Persian / Arabic common words
    "پولیس", "کنٹرول", "سب", "چائے", "ہوٹل", "روڈ", "تھانہ", "ڈویژن", "ضلع", "تحصیل", "شہر", "مرکز",
    "شارع", "طريق", "جادة", "دوار", "منطقة", "محافظة", "ولاية", "بلدية", "مستشفى", "صيدلية", "بنك",
    "خیابان", "کوچه", "بزرگراه", "جاده", "بلوار", "میدان", "ایستگاه",
    # Turkish common stop words
    "caddesi", "cad", "sokak", "sok", "bulvarı", "bulv", "mahallesi", "mah", "ilçesi", "ili", "otoyol",
}

GEO_PHONETIC_SYNONYMS = {
    # ---------------- Pakistan ----------------
    "پیر چناسی": "Pir Chinasi",
    "پیرچناسی": "Pir Chinasi",
    "آزاد کشمیر": "Azad Kashmir",
    "ازاد کشمیر": "Azad Kashmir",
    "مظفرآباد": "Muzaffarabad",
    "مظفر آباد": "Muzaffarabad",
    "مظفراباد": "Muzaffarabad",
    "اسلام آباد": "Islamabad",
    "اسلام اباد": "Islamabad",
    "راولپنڈی": "Rawalpindi",
    "لاہور": "Lahore",
    "کراچی": "Karachi",
    "پشاور": "Peshawar",
    "کوئٹہ": "Quetta",
    "گلگت": "Gilgit",
    "سوات": "Swat",
    "مری": "Murree",
    "ناران": "Naran",
    "کاغان": "Kaghan",
    "ہنزہ": "Hunza",
    "سکردو": "Skardu",
    "شاہراہ قراقرم": "Karakoram Highway N-35, Pakistan",
    "مری ایکسپریس وے": "Murree Expressway N-75, Pakistan",
    "فیصل مسجد": "Faisal Mosque, Islamabad, Pakistan",
    "مینار پاکستان": "Minar-e-Pakistan, Lahore",
    "بادشاہی مسجد": "Badshahi Mosque, Lahore",
    "N-75": "N-75, Pakistan",
    "N75": "N-75, Pakistan",
    "N-35": "N-35 Karakoram Highway, Pakistan",
    "N-5": "N-5 National Highway, Pakistan",
    "N-25": "N-25 Regional Highway, Pakistan",
    "N-55": "N-55 Indus Highway, Pakistan",
    "M-1": "M-1 Motorway, Pakistan",
    "M-2": "M-2 Motorway, Pakistan",
    "M-3": "M-3 Motorway, Pakistan",
    "M-4": "M-4 Motorway, Pakistan",
    "M-5": "M-5 Motorway, Pakistan",
    "M-9": "M-9 Motorway, Pakistan",
    "M-11": "M-11 Motorway, Pakistan",
    "M-15": "M-15 Hazara Motorway, Pakistan",

    # ---------------- United Arab Emirates ----------------
    "دبي": "Dubai, United Arab Emirates",
    "أبوظبي": "Abu Dhabi, United Arab Emirates",
    "ابوظبي": "Abu Dhabi, United Arab Emirates",
    "الشارقة": "Sharjah, United Arab Emirates",
    "عجمان": "Ajman, United Arab Emirates",
    "رأس الخيمة": "Ras Al Khaimah, United Arab Emirates",
    "راس الخيمة": "Ras Al Khaimah, United Arab Emirates",
    "الفجيرة": "Fujairah, United Arab Emirates",
    "أم القيوين": "Umm Al Quwain, United Arab Emirates",
    "العين": "Al Ain, Abu Dhabi, United Arab Emirates",
    "برج خليفة": "Burj Khalifa, Dubai, United Arab Emirates",
    "برج العرب": "Burj Al Arab, Dubai, United Arab Emirates",
    "E11": "Sheikh Zayed Road E11, Dubai, United Arab Emirates",
    "E-11": "Sheikh Zayed Road E11, Dubai, United Arab Emirates",
    "E311": "Sheikh Mohammed Bin Zayed Road E311, UAE",
    "E-311": "Sheikh Mohammed Bin Zayed Road E311, UAE",
    "E611": "Emirates Road E611, UAE",
    "E-611": "Emirates Road E611, UAE",
    "E44": "Al Khail Road E44, Dubai, UAE",
    "E66": "Dubai-Al Ain Road E66, UAE",

    # ---------------- Saudi Arabia ----------------
    "الرياض": "Riyadh, Saudi Arabia",
    "جدة": "Jeddah, Saudi Arabia",
    "مكة المكرمة": "Mecca, Saudi Arabia",
    "مكة": "Mecca, Saudi Arabia",
    "المدينة المنورة": "Medina, Saudi Arabia",
    "المدينة": "Medina, Saudi Arabia",
    "الدمام": "Dammam, Saudi Arabia",
    "الخبر": "Khobar, Eastern Province, Saudi Arabia",
    "الظهران": "Dhahran, Eastern Province, Saudi Arabia",
    "أبها": "Abha, Asir, Saudi Arabia",
    "تبوك": "Tabuk, Saudi Arabia",
    "طريق الملك فهد": "King Fahd Road, Riyadh, Saudi Arabia",
    "طريق الملك عبدالله": "King Abdullah Road, Riyadh, Saudi Arabia",
    "Route 40": "Highway 40, Saudi Arabia",
    "Route 65": "Highway 65, Saudi Arabia",
    "Route 15": "Highway 15, Saudi Arabia",
    "Route 85": "Highway 85, Saudi Arabia",

    # ---------------- Qatar ----------------
    "الدوحة": "Doha, Qatar",
    "الوكرة": "Al Wakrah, Qatar",
    "الخور": "Al Khor, Qatar",
    "لوسيل": "Lusail, Qatar",
    "طريق سلوى": "Salwa Road, Qatar",
    "طريق الشمال": "Al Shamal Road, Qatar",
    "Q1": "Al Shamal Road Q1, Qatar",
    "Q2": "Dukhan Highway Q2, Qatar",
    "Q3": "Salwa Road Q3, Qatar",

    # ---------------- Kuwait ----------------
    "الكويت": "Kuwait City, Kuwait",
    "الأحمدي": "Al Ahmadi, Kuwait",
    "الاحمدي": "Al Ahmadi, Kuwait",
    "حولي": "Hawalli, Kuwait",
    "الفروانية": "Al Farwaniyah, Kuwait",
    "الجهراء": "Al Jahra, Kuwait",
    "السالمية": "Salmiya, Kuwait",
    "طريق الفحيحيل": "Fahaheel Expressway Route 30, Kuwait",
    "Route 30": "Fahaheel Expressway Route 30, Kuwait",
    "Route 40": "King Fahd Expressway Route 40, Kuwait",
    "Route 50": "Riyadh Expressway Route 50, Kuwait",
    "Route 80": "Jahra Highway Route 80, Kuwait",

    # ---------------- Bahrain ----------------
    "المنامة": "Manama, Bahrain",
    "المحرق": "Muharraq, Bahrain",
    "الرفاع": "Riffa, Bahrain",
    "مدينة حمد": "Hamad Town, Bahrain",
    "جسر الملك فهد": "King Fahd Causeway, Bahrain",

    # ---------------- Oman ----------------
    "مسقط": "Muscat, Oman",
    "صلالة": "Salalah, Dhofar, Oman",
    "صحار": "Sohar, Al Batinah, Oman",
    "نزوى": "Nizwa, Ad Dakhiliyah, Oman",
    "صور": "Sur, Ash Sharqiyah, Oman",
    "طريق الباطنة السريع": "Al Batinah Expressway, Oman",
    "Route 1": "Route 1, Oman",
    "Route 15": "Route 15, Oman",
    "Route 31": "Route 31, Oman",

    # ---------------- Yemen ----------------
    "صنعاء": "Sanaa, Yemen",
    "عدن": "Aden, Yemen",
    "تعز": "Taiz, Yemen",
    "الحديدة": "Al Hudaydah, Yemen",
    "المكلا": "Mukalla, Hadhramaut, Yemen",
    "إب": "Ibb, Yemen",

    # ---------------- Egypt ----------------
    "القاهرة": "Cairo, Egypt",
    "الإسكندرية": "Alexandria, Egypt",
    "الاسكندرية": "Alexandria, Egypt",
    "الجيزة": "Giza, Egypt",
    "شرم الشيخ": "Sharm El Sheikh, South Sinai, Egypt",
    "الغردقة": "Hurghada, Red Sea, Egypt",
    "الأقصر": "Luxor, Egypt",
    "الاقصر": "Luxor, Egypt",
    "أسوان": "Aswan, Egypt",
    "اسوان": "Aswan, Egypt",
    "بور سعيد": "Port Said, Egypt",
    "بورسعيد": "Port Said, Egypt",
    "طريق مصر اسكندرية الصحراوي": "Cairo-Alexandria Desert Road, Egypt",

    # ---------------- Iraq ----------------
    "بغداد": "Baghdad, Iraq",
    "البصرة": "Basra, Iraq",
    "أربيل": "Erbil, Kurdistan, Iraq",
    "اربيل": "Erbil, Kurdistan, Iraq",
    "الموصل": "Mosul, Nineveh, Iraq",
    "النجف": "Najaf, Iraq",
    "كربلاء": "Karbala, Iraq",
    "السليمانية": "Sulaymaniyah, Kurdistan, Iraq",
    "كركوك": "Kirkuk, Iraq",
    "Highway 1": "Highway 1, Iraq",
    "Highway 6": "Highway 6, Iraq",

    # ---------------- Iran ----------------
    "تهران": "Tehran, Iran",
    "اصفهان": "Isfahan, Iran",
    "مشهد": "Mashhad, Razavi Khorasan, Iran",
    "شیراز": "Shiraz, Fars, Iran",
    "تبریز": "Tabriz, East Azerbaijan, Iran",
    "اهواز": "Ahvaz, Khuzestan, Iran",
    "کرج": "Karaj, Alborz, Iran",
    "یزد": "Yazd, Iran",
    "کرمان": "Kerman, Iran",
    "جاده چالوس": "Chalous Road 59, Mazandaran, Iran",
    "جاده هراز": "Haraz Road 77, Mazandaran, Iran",
    "بزرگراه همت": "Hemmat Expressway, Tehran, Iran",
    "Freeway 5": "Freeway 5, Iran",
    "Freeway 7": "Freeway 7, Iran",
    "Road 44": "Road 44, Iran",
    "Road 65": "Road 65, Iran",

    # ---------------- Israel ----------------
    "ירושלים": "Jerusalem, Israel",
    "תל אביב": "Tel Aviv-Yafo, Israel",
    "חיפה": "Haifa, Israel",
    "באר שבע": "Beersheba, Southern District, Israel",
    "אילת": "Eilat, Southern District, Israel",
    "נתניה": "Netanya, Central District, Israel",
    "אשדוד": "Ashdod, Southern District, Israel",
    "כביש 6": "Highway 6, Israel",
    "כביש 1": "Highway 1, Israel",
    "נתיבי איילון": "Ayalon Highway 20, Tel Aviv, Israel",
    "Route 6": "Highway 6, Israel",
    "Route 1": "Highway 1, Israel",
    "Route 90": "Highway 90, Israel",

    # ---------------- Syria ----------------
    "دمشق": "Damascus, Syria",
    "حلب": "Aleppo, Syria",
    "حمص": "Homs, Syria",
    "اللاذقية": "Latakia, Syria",
    "حماة": "Hama, Syria",
    "M5 Highway": "M5 Highway, Syria",

    # ---------------- Turkey / Türkiye ----------------
    "İstanbul": "Istanbul, Turkey",
    "Istanbul": "Istanbul, Turkey",
    "Ankara": "Ankara, Turkey",
    "İzmir": "Izmir, Turkey",
    "Izmir": "Izmir, Turkey",
    "Bursa": "Bursa, Turkey",
    "Antalya": "Antalya, Turkey",
    "Adana": "Adana, Turkey",
    "Konya": "Konya, Turkey",
    "Gaziantep": "Gaziantep, Turkey",
    "Trabzon": "Trabzon, Turkey",
    "O-1": "O-1 Motorway, Istanbul, Turkey",
    "O-2": "O-2 Motorway, Istanbul, Turkey",
    "O-3": "O-3 Motorway, Turkey",
    "O-4": "O-4 Anadolu Motorway, Turkey",
    "O-5": "O-5 Motorway, Turkey",
    "O-7": "O-7 Kuzey Marmara Motorway, Turkey",
    "D-100": "D-100 Highway, Turkey",
    "D-400": "D-400 Highway, Turkey",

    # ---------------- India ----------------
    "Mumbai": "Mumbai, Maharashtra, India",
    "Delhi": "Delhi, India",
    "Bengaluru": "Bengaluru, Karnataka, India",
    "Bangalore": "Bengaluru, Karnataka, India",
    "Hyderabad": "Hyderabad, Telangana, India",
    "Chennai": "Chennai, Tamil Nadu, India",
    "Kolkata": "Kolkata, West Bengal, India",
    "Ahmedabad": "Ahmedabad, Gujarat, India",
    "Pune": "Pune, Maharashtra, India",
    "Jaipur": "Jaipur, Rajasthan, India",
    "NH-44": "National Highway 44, India",
    "NH-48": "National Highway 48, India",
    "NH-19": "National Highway 19, India",
    "NH-53": "National Highway 53, India",
    "NH-66": "National Highway 66, India",
    "NH-16": "National Highway 16, India",
    "NH-27": "National Highway 27, India",
}


def normalize_arabic_urdu(text: str) -> str:
    """Normalize Arabic and Urdu character variants, strip diacritics and tatweel."""
    if not text:
        return ""
    # Strip tatweel / kashida (ـ)
    text = text.replace("\u0640", "")
    # Remove Arabic / Urdu diacritics / harakat
    text = re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED]", "", text)
    # Character normalizations:
    replacements = {
        "\u064a": "\u06cc",  # Arabic Yeh (ي) -> Urdu Yeh (ی)
        "\u0649": "\u06cc",  # Alef Maksura (ى) -> Urdu Yeh (ی)
        "\u0626": "\u06cc",  # Yeh with Hamza (ئ) -> Urdu Yeh (ی)
        "\u0643": "\u06a9",  # Arabic Kaf (ك) -> Urdu Keheh (ک)
        "\u0629": "\u06c1",  # Ta Marbuta (ة) -> Urdu Goal Heh (ہ)
        "\u0647": "\u06c1",  # Arabic Heh (ه) -> Urdu Goal Heh (ہ)
        "\u06be": "\u06c1",  # Do-chashmi Heh (ھ) -> Urdu Goal Heh (ہ)
        "\u0622": "\u0627",  # Alef with Madda (آ) -> Alef (ا)
    }
    for orig, norm in replacements.items():
        text = text.replace(orig, norm)
    return text


def detect_script(text: str) -> Optional[Dict[str, Any]]:
    """Detect non-Latin writing script in extracted text."""
    if not text:
        return None
    for name, pattern, candidate_countries in SCRIPT_PATTERNS:
        if pattern.search(text):
            return {
                "script": name,
                "candidate_countries": candidate_countries,
            }
    return None


def detect_tld(text: str) -> Optional[Dict[str, str]]:
    """Detect country-code Top Level Domain (.de, .fr, .co.uk, .com.br, .ac.ir, etc.) in text."""
    if not text:
        return None
    text_lower = text.lower()

    # 1. Check compound 2nd-level domains (.com.pk, .ac.ir, .co.uk, etc.)
    compound_match = re.search(r"\b([a-z0-9\-_]+\.(com|co|org|gov|edu|net|ac)\.([a-z]{2}))\b", text_lower)
    if compound_match:
        full_token = compound_match.group(1)
        sub_tld = f"{compound_match.group(2)}.{compound_match.group(3)}"
        cc_tld = compound_match.group(3)
        if sub_tld in CC_TLD_MAP:
            return {"tld": sub_tld, "country": CC_TLD_MAP[sub_tld], "matched_token": full_token}
        if cc_tld in CC_TLD_MAP:
            return {"tld": cc_tld, "country": CC_TLD_MAP[cc_tld], "matched_token": full_token}

    # 2. Check 2-letter ccTLDs at word boundary (.de, .pk, .ir, etc.)
    for m in re.finditer(r"\b([a-z0-9\-_]+\.([a-z]{2}))\b", text_lower):
        tld = m.group(2)
        if tld in CC_TLD_MAP:
            return {"tld": tld, "country": CC_TLD_MAP[tld], "matched_token": m.group(1)}
    return None


def detect_calling_code(text: str) -> Optional[Dict[str, Any]]:
    """Detect international phone dialing code in text snippet (+XX or 00XX)."""
    if not text:
        return None
    # Look for +XX or 00XX
    matches = re.findall(r"(?:\+|00)(\d{1,4})[\s\-\.\)]", text)
    for code in matches:
        res = lookup_calling_code(code)
        if res:
            return {"code": code, "country": res.get("country"), "utc": res.get("utc")}
    return None


def extract_candidate_place_phrases(text: str) -> List[str]:
    """Filter candidate place names, landmarks or highway routes from OCR text."""
    if not text:
        return []
    candidates = []
    norm_text = normalize_arabic_urdu(text)

    # 0. Check phonetic/Urdu/Arabic gazetteer matches directly on raw and normalized text
    for syn_key, syn_val in GEO_PHONETIC_SYNONYMS.items():
        norm_key = normalize_arabic_urdu(syn_key)
        if syn_key in text or norm_key in norm_text:
            candidates.append(syn_val)
            candidates.append(syn_key)

    # Clean up punctuation while preserving non-Latin unicode characters
    cleaned = re.sub(r"[^\w\s\-\.]", " ", text).strip()
    words = [w.strip() for w in cleaned.split() if len(w.strip()) >= 2]

    # 1. Single capitalized words (Latin) or any significant non-Latin words
    for w in words:
        wl = w.lower()
        if wl not in COMMON_STOP_WORDS and not wl.isdigit():
            is_non_latin = any(ord(c) > 127 for c in w)
            if is_non_latin and len(w) >= 3:
                candidates.append(w)
                norm_w = normalize_arabic_urdu(w)
                # Check if this non-latin word matches any gazetteer keyword
                for syn_k, syn_v in GEO_PHONETIC_SYNONYMS.items():
                    norm_k = normalize_arabic_urdu(syn_k)
                    if syn_k in w or w in syn_k or norm_k in norm_w or norm_w in norm_k:
                        candidates.append(syn_v)
                        candidates.append(syn_k)
            elif (w[0].isupper() or any(c.isupper() for c in w)) and len(wl) >= 4:
                candidates.append(w)

    # 2. Highway / Route codes (e.g. A-10, US-101, I-80, M4, RN7, BR-101, Ruta 40, N-35, N-75, E11, NH-44, O-4)
    route_match = re.search(r"\b(US|I|M|A|B|D|N|RN|BR|NH|SH|E|Q|O|Ruta|Route|Hwy|Highway)\s*[\-\.]?\s*(\d{1,4}[A-Z]?)\b", text, re.IGNORECASE)
    if route_match:
        candidates.append(route_match.group(0))

    # 3. Two-word phrases (e.g. "San Pedro", "Mt Cook", "Grand Canyon", "آزاد کشمیر", "پیر چناسی")
    for i in range(len(words) - 1):
        p1, p2 = words[i], words[i + 1]
        p1_non_latin = any(ord(c) > 127 for c in p1)
        p2_non_latin = any(ord(c) > 127 for c in p2)
        if p1_non_latin or p2_non_latin:
            if p1.lower() not in COMMON_STOP_WORDS and p2.lower() not in COMMON_STOP_WORDS:
                phrase = f"{p1} {p2}"
                candidates.append(phrase)
                norm_phrase = normalize_arabic_urdu(phrase)
                for syn_k, syn_v in GEO_PHONETIC_SYNONYMS.items():
                    norm_k = normalize_arabic_urdu(syn_k)
                    if syn_k in phrase or phrase in syn_k or norm_k in norm_phrase or norm_phrase in norm_k:
                        candidates.append(syn_v)
                        candidates.append(syn_k)
        elif (p1[0].isupper() or p2[0].isupper()) and (p1.lower() not in COMMON_STOP_WORDS or p2.lower() not in COMMON_STOP_WORDS):
            phrase = f"{p1} {p2}"
            if len(phrase) >= 6:
                candidates.append(phrase)

    return list(dict.fromkeys(candidates))[:8]  # Deduplicate, max 8 candidates

