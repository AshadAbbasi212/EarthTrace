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
