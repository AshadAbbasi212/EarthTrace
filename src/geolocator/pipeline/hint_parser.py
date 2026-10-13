"""Natural language user hint parser extracting geographic, seasonal, and landmark priors."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

SEASONS = {
    "winter": "winter",
    "spring": "spring",
    "summer": "summer",
    "autumn": "autumn",
    "fall": "autumn",
}

CONTINENTS = {
    "europe": "Europe",
    "asia": "Asia",
    "africa": "Africa",
    "north america": "North America",
    "south america": "South America",
    "oceania": "Oceania",
    "antarctica": "Antarctica",
}

COMMON_COUNTRIES = [
    "united states", "usa", "canada", "mexico", "brazil", "argentina", "chile", "peru", "colombia",
    "france", "germany", "italy", "spain", "united kingdom", "uk", "ireland", "switzerland", "austria",
    "norway", "sweden", "finland", "iceland", "poland", "greece", "turkey", "russia", "ukraine",
    "china", "japan", "south korea", "india", "pakistan", "indonesia", "thailand", "vietnam", "malaysia",
    "singapore", "australia", "new zealand", "egypt", "morocco", "south africa", "kenya", "tanzania",
    "saudi arabia", "iran", "iraq", "israel", "jordan", "nepal", "kazakhstan", "kyrgyzstan", "mongolia",
]


# Curated mapping of high-frequency subnational provinces/states (ADMIN1) to (country, division)
# Modeled after Picarta's ADMIN1 filtering and GeoSpy's administrative state hierarchy
SUBNATIONAL_DIVISIONS: Dict[str, Tuple[str, str]] = {
    # Pakistan
    "gilgit-baltistan": ("Pakistan", "Gilgit-Baltistan"),
    "gilgit baltistan": ("Pakistan", "Gilgit-Baltistan"),
    "khyber pakhtunkhwa": ("Pakistan", "Khyber Pakhtunkhwa"),
    "kp": ("Pakistan", "Khyber Pakhtunkhwa"),
    "kpk": ("Pakistan", "Khyber Pakhtunkhwa"),
    "punjab": ("Pakistan", "Punjab"),
    "balochistan": ("Pakistan", "Balochistan"),
    "sindh": ("Pakistan", "Sindh"),
    "azad kashmir": ("Pakistan", "Azad Kashmir"),
    "ajk": ("Pakistan", "Azad Kashmir"),
    "islamabad": ("Pakistan", "Islamabad Capital Territory"),
    "murree": ("Pakistan", "Punjab"),
    "swat": ("Pakistan", "Khyber Pakhtunkhwa"),
    "hunza": ("Pakistan", "Gilgit-Baltistan"),
    "skardu": ("Pakistan", "Gilgit-Baltistan"),
    # Europe
    "bavaria": ("Germany", "Bavaria"),
    "bayern": ("Germany", "Bavaria"),
    "baden-wurttemberg": ("Germany", "Baden-Württemberg"),
    "saxony": ("Germany", "Saxony"),
    "hesse": ("Germany", "Hesse"),
    "tyrol": ("Austria", "Tyrol"),
    "tirol": ("Austria", "Tyrol"),
    "salzburg": ("Austria", "Salzburg"),
    "carinthia": ("Austria", "Carinthia"),
    "styria": ("Austria", "Styria"),
    "valais": ("Switzerland", "Valais"),
    "wallis": ("Switzerland", "Valais"),
    "bern": ("Switzerland", "Bern"),
    "graubunden": ("Switzerland", "Graubünden"),
    "ticino": ("Switzerland", "Ticino"),
    "tuscany": ("Italy", "Tuscany"),
    "toscana": ("Italy", "Tuscany"),
    "lombardy": ("Italy", "Lombardy"),
    "sicily": ("Italy", "Sicily"),
    "sardinia": ("Italy", "Sardinia"),
    "piedmont": ("Italy", "Piedmont"),
    "veneto": ("Italy", "Veneto"),
    "highlands": ("United Kingdom", "Scottish Highlands"),
    "scottish highlands": ("United Kingdom", "Scottish Highlands"),
    "wales": ("United Kingdom", "Wales"),
    "scotland": ("United Kingdom", "Scotland"),
    # Americas
    "california": ("United States", "California"),
    "texas": ("United States", "Texas"),
    "colorado": ("United States", "Colorado"),
    "washington": ("United States", "Washington"),
    "oregon": ("United States", "Oregon"),
    "florida": ("United States", "Florida"),
    "alaska": ("United States", "Alaska"),
    "hawaii": ("United States", "Hawaii"),
    "arizona": ("United States", "Arizona"),
    "utah": ("United States", "Utah"),
    "british columbia": ("Canada", "British Columbia"),
    "alberta": ("Canada", "Alberta"),
    "ontario": ("Canada", "Ontario"),
    "quebec": ("Canada", "Quebec"),
    # Middle East & Gulf
    "dhofar": ("Oman", "Dhofar"),
    "muscat": ("Oman", "Muscat"),
    "asir": ("Saudi Arabia", "Asir"),
    "hejaz": ("Saudi Arabia", "Hejaz"),
    "dubai": ("United Arab Emirates", "Dubai"),
    "abu dhabi": ("United Arab Emirates", "Abu Dhabi"),
    # East & South Asia
    "hokkaido": ("Japan", "Hokkaido"),
    "okinawa": ("Japan", "Okinawa"),
    "kyoto": ("Japan", "Kyoto"),
    "tokyo": ("Japan", "Tokyo"),
    "ladakh": ("India", "Ladakh"),
    "himachal pradesh": ("India", "Himachal Pradesh"),
    "uttarakhand": ("India", "Uttarakhand"),
    "rajasthan": ("India", "Rajasthan"),
    "kerala": ("India", "Kerala"),
    "bagmati": ("Nepal", "Bagmati Province"),
    "gandaki": ("Nepal", "Gandaki Province"),
    "koshi": ("Nepal", "Koshi Province"),
}


class HintParser:
    """Extracts geographic regions, season cues, and landmarks from free-form user hint text."""

    def parse(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {}

        cleaned = text.lower()
        extracted: Dict[str, Any] = {
            "raw_text": text,
            "countries": [],
            "continents": [],
            "season": None,
            "landmarks": [],
            "subnational": [],
            "radius_km": None,
            "center_coords": None,
        }

        # 1. Season detection
        for word, season in SEASONS.items():
            if re.search(rf"\b{word}\b", cleaned):
                extracted["season"] = season
                break

        # 2. Continent detection
        for key, continent in CONTINENTS.items():
            if re.search(rf"\b{key}\b", cleaned):
                if continent not in extracted["continents"]:
                    extracted["continents"].append(continent)

        # 3. Country detection (with negative exclusion awareness)
        negative_country_matches = re.findall(
            r"\b(?:not|exclude|except|never)\s+(?:in\s+)?([a-zA-Z\s]+?)(?:[,.]|\band\b|$)",
            cleaned,
        )
        excluded_raw = [m.strip() for m in negative_country_matches]
        extracted["excluded_countries"] = []

        for country in COMMON_COUNTRIES:
            is_excluded = any(country in exc for exc in excluded_raw)
            pattern = rf"\b{re.escape(country)}\b"
            if re.search(pattern, cleaned):
                standard_name = "United States" if country in ("usa", "united states") else (
                    "United Kingdom" if country in ("uk", "united kingdom") else country.title()
                )
                if is_excluded:
                    if standard_name not in extracted["excluded_countries"]:
                        extracted["excluded_countries"].append(standard_name)
                else:
                    if standard_name not in extracted["countries"]:
                        extracted["countries"].append(standard_name)

        # 3b. Subnational Division / State / Province Detection (Picarta ADMIN1 & GeoSpy state)
        for sub_term, (c_name, div_name) in SUBNATIONAL_DIVISIONS.items():
            pattern = rf"\b{re.escape(sub_term)}\b"
            if re.search(pattern, cleaned):
                extracted["subnational"].append({
                    "term": sub_term,
                    "country": c_name,
                    "division": div_name,
                })
                # Auto-promote country if not explicitly excluded
                if c_name not in extracted["excluded_countries"] and c_name not in extracted["countries"]:
                    extracted["countries"].append(c_name)

        # 3c. Radius detection (e.g., "within 50 km", "radius of 25 km", "100 km radius")
        radius_match = re.search(r"\b(?:within|radius(?:\s+of)?)\s+(\d{1,4})\s*(?:km|kilometers|miles)?\b", cleaned)
        if not radius_match:
            radius_match = re.search(r"\b(\d{1,4})\s*(?:km|kilometers)\s+radius\b", cleaned)
        if radius_match:
            try:
                extracted["radius_km"] = float(radius_match.group(1))
            except ValueError:
                pass

        # 3d. Coordinate extraction (e.g., "around 33.9, 73.4" or "coordinates 47.5, 11.2")
        coord_match = re.search(r"(-?\d{1,2}\.\d{2,6})\s*,\s*(-?\d{1,3}\.\d{2,6})", text)
        if coord_match:
            try:
                extracted["center_coords"] = (float(coord_match.group(1)), float(coord_match.group(2)))
            except ValueError:
                pass

        # 4. Terrain filter detection
        terrain_match = re.search(r"\b(mountain|desert|urban|coast|coastal|beach|forest|farmland|rural)\b", cleaned)
        if terrain_match:
            t_word = terrain_match.group(1)
            extracted["terrain_filter"] = "coast" if t_word in ("coastal", "beach") else t_word

        # 5. Landmark indicators ("near X", "by X", "around X")
        landmark_matches = re.findall(r"\b(?:near|around|close to|by|at)\s+([A-Z][a-zA-Z\s]+?)(?:[,.]|\band\b|\bin\b|\bduring\b|$)", text)
        for lm in landmark_matches:
            cand = lm.strip()
            for s in SEASONS.keys():
                cand = re.sub(rf"\s+\b{s}\b.*$", "", cand, flags=re.IGNORECASE).strip()
            if cand and cand.lower() not in CONTINENTS and cand.lower() not in COMMON_COUNTRIES and cand.lower() not in SUBNATIONAL_DIVISIONS:
                extracted["landmarks"].append(cand)

        return extracted

