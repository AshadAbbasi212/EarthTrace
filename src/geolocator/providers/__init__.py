"""Providers package for keyless geospatial, map, elevation, satellite and ground imagery data."""
from geolocator.providers.base import BaseProvider
from geolocator.providers.osm import OSMProvider
from geolocator.providers.nominatim import NominatimProvider
from geolocator.providers.dem import DEMProvider
from geolocator.providers.satellite import SatelliteProvider
from geolocator.providers.street_image import StreetImageProvider
from geolocator.providers.climate import ClimateProvider
from geolocator.providers.landcover import LandCoverProvider

__all__ = [
    "BaseProvider",
    "OSMProvider",
    "NominatimProvider",
    "DEMProvider",
    "SatelliteProvider",
    "StreetImageProvider",
    "ClimateProvider",
    "LandCoverProvider",
]
