"""Adapters wrapping vendored scripts and local OCR engines."""
from geolocator.adapters.exif_adapter import extract_exif
from geolocator.adapters.imgprep_adapter import generate_edge_crops, create_resized_copy
from geolocator.adapters.clues_adapter import lookup_plate, lookup_driving_side, lookup_calling_code, lookup_territory
from geolocator.adapters.ocr_adapter import get_ocr, LocalOCR

__all__ = [
    "extract_exif",
    "generate_edge_crops",
    "create_resized_copy",
    "lookup_plate",
    "lookup_driving_side",
    "lookup_calling_code",
    "lookup_territory",
    "get_ocr",
    "LocalOCR",
]
