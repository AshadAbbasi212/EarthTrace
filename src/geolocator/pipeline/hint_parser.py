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

        # 3. Country detection
        for country in COMMON_COUNTRIES:
            pattern = rf"\b{re.escape(country)}\b"
            if re.search(pattern, cleaned):
                # Standardize
                standard_name = "United States" if country in ("usa", "united states") else (
                    "United Kingdom" if country in ("uk", "united kingdom") else country.title()
                )
                if standard_name not in extracted["countries"]:
                    extracted["countries"].append(standard_name)

        # 4. Landmark indicators ("near X", "by X", "around X")
        landmark_matches = re.findall(r"\b(?:near|around|close to|by|at)\s+([A-Z][a-zA-Z\s]+?)(?:[,.]|\band\b|\bin\b|\bduring\b|$)", text)
        for lm in landmark_matches:
            cand = lm.strip()
            # Clean trailing prepositions or season words
            for s in SEASONS.keys():
                cand = re.sub(rf"\s+\b{s}\b.*$", "", cand, flags=re.IGNORECASE).strip()
            if cand and cand.lower() not in CONTINENTS and cand.lower() not in COMMON_COUNTRIES:
                extracted["landmarks"].append(cand)

        return extracted
