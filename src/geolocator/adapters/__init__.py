"""Adapters wrapping vendored scripts and local OCR engines."""
from geolocator.adapters.exif_adapter import extract_exif
from geolocator.adapters.imgprep_adapter import generate_edge_crops, create_resized_copy
from geolocator.adapters.clues_adapter import (
    lookup_plate,
    lookup_driving_side,
    lookup_calling_code,
    lookup_territory,
    detect_script,
    detect_tld,
    detect_calling_code,
    extract_candidate_place_phrases,
    GEO_PHONETIC_SYNONYMS,
    COMMON_STOP_WORDS,
    country_to_iso,
)
from geolocator.adapters.ocr_adapter import get_ocr, LocalOCR

__all__ = [
    "extract_exif",
    "generate_edge_crops",
    "create_resized_copy",
    "lookup_plate",
    "lookup_driving_side",
    "lookup_calling_code",
    "lookup_territory",
    "detect_script",
    "detect_tld",
    "detect_calling_code",
    "extract_candidate_place_phrases",
    "GEO_PHONETIC_SYNONYMS",
    "COMMON_STOP_WORDS",
    "country_to_iso",
    "get_ocr",
    "LocalOCR",
]

