"""Adapter wrapping vendored clues.py for tabular knowledge lookups."""
from __future__ import annotations

import json
import logging
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
            if prov_char in table:
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

import re

CC_TLD_MAP: Dict[str, str] = {
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
    "tr": "Turkey",
    "kr": "South Korea",
    "co.kr": "South Korea",
    "id": "Indonesia",
    "co.id": "Indonesia",
    "in": "India",
    "co.in": "India",
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
    ("cyrillic", re.compile(r"[\u0400-\u04FF]"), ["Russia", "Ukraine", "Belarus", "Bulgaria", "Serbia", "Kazakhstan", "Kyrgyzstan", "Mongolia", "North Macedonia"]),
    ("greek", re.compile(r"[\u0370-\u03FF]"), ["Greece", "Cyprus"]),
    ("arabic", re.compile(r"[\u0600-\u06FF]"), ["Egypt", "Saudi Arabia", "Morocco", "United Arab Emirates", "Jordan", "Tunisia", "Algeria", "Iraq"]),
    ("hangul", re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]"), ["South Korea"]),
    ("japanese_kana", re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"), ["Japan"]),
    ("thai", re.compile(r"[\u0E00-\u0E7F]"), ["Thailand"]),
    ("hebrew", re.compile(r"[\u0590-\u05FF]"), ["Israel"]),
    ("devanagari", re.compile(r"[\u0900-\u097F]"), ["India", "Nepal"]),
    ("hanzi", re.compile(r"[\u4E00-\u9FFF]"), ["China", "Taiwan", "Hong Kong", "Singapore"]),
]

COMMON_STOP_WORDS = {
    "hotel", "restaurant", "cafe", "coffee", "bar", "pub", "supermarket", "market",
    "shop", "store", "bank", "pharmacy", "farmacia", "apotheke", "police", "hospital",
    "open", "closed", "entrance", "exit", "stop", "parking", "station", "train", "bus",
    "metro", "subway", "taxi", "airport", "welcome", "street", "avenue", "road", "str",
    "drive", "lane", "way", "highway", "expressway", "toll", "free", "city", "center",
    "north", "south", "east", "west", "the", "and", "for", "with", "from", "service",
    "wc", "info", "information", "ticket", "tickets", "fast", "food", "express", "auto",
}


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
    """Detect country-code Top Level Domain (.de, .fr, .co.uk, .com.br, etc.) in text."""
    if not text:
        return None
    text_lower = text.lower()
    # Check compound TLDs first (.co.uk, .com.br, etc.)
    compound_pattern = re.compile(r"\b[a-z0-9\-_]+\.(co\.uk|com\.br|co\.jp|com\.au|co\.nz|co\.za|com\.mx|com\.ar|co\.kr|co\.id|co\.in|co\.th|com\.sg|com\.my)\b")
    match = compound_pattern.search(text_lower)
    if match:
        tld = match.group(1)
        if tld in CC_TLD_MAP:
            return {"tld": tld, "country": CC_TLD_MAP[tld], "matched_token": match.group(0)}

    # Check 2-letter ccTLDs
    simple_pattern = re.compile(r"\b[a-z0-9\-_]+\.([a-z]{2})\b")
    for m in simple_pattern.finditer(text_lower):
        tld = m.group(1)
        if tld in CC_TLD_MAP:
            return {"tld": tld, "country": CC_TLD_MAP[tld], "matched_token": m.group(0)}
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
    # Clean up punctuation
    cleaned = re.sub(r"[^\w\s\-\.]", " ", text).strip()
    words = [w.strip() for w in cleaned.split() if len(w.strip()) >= 3]

    # 1. Single capitalized / significant words that are not common stop words
    for w in words:
        wl = w.lower()
        if wl not in COMMON_STOP_WORDS and not wl.isdigit() and len(wl) >= 4:
            if w[0].isupper() or any(c.isupper() for c in w):
                candidates.append(w)

    # 2. Highway / Route codes (e.g. A-10, US-101, I-80, M4, RN7, BR-101, Ruta 40)
    route_match = re.search(r"\b(US|I|M|A|B|D|N|RN|BR|Ruta|Route)\s*[\-\.]?\s*(\d{1,4}[A-Z]?)\b", text, re.IGNORECASE)
    if route_match:
        candidates.append(route_match.group(0))

    # 3. Two-word phrases (e.g. "San Pedro", "Mt Cook", "Grand Canyon")
    for i in range(len(words) - 1):
        p1, p2 = words[i], words[i + 1]
        if (p1[0].isupper() or p2[0].isupper()) and (p1.lower() not in COMMON_STOP_WORDS or p2.lower() not in COMMON_STOP_WORDS):
            phrase = f"{p1} {p2}"
            if len(phrase) >= 6:
                candidates.append(phrase)

    return list(dict.fromkeys(candidates))[:5]  # Deduplicate, max 5 candidates

