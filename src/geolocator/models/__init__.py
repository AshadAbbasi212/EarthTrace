"""Models package for local vision, CLIP, DINOv2 and geolocation inference."""
from geolocator.models.model_manager import ModelManager, get_model_manager

__all__ = ["ModelManager", "get_model_manager"]
