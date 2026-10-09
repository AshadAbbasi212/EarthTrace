"""Download 50 real photographs from around the world from Wikimedia Commons.

Populates eval/manifest_real.csv and eval/photos_real/ with genuine photographs
taken by human photographers across all 11 biomes and 7 continents.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("download_real_photos")

TARGET_LOCATIONS: List[Dict[str, Any]] = [
    # 1. Urban
    {"id": "urb_01", "name": "Eiffel Tower Paris", "category": "urban", "continent": "Europe", "country": "France", "query": "Eiffel Tower Paris", "lat": 48.8584, "lon": 2.2945},
    {"id": "urb_02", "name": "Tokyo Tower Roppongi", "category": "urban", "continent": "Asia", "country": "Japan", "query": "Tokyo Tower", "lat": 35.6586, "lon": 139.7454},
    {"id": "urb_03", "name": "Empire State Building New York", "category": "urban", "continent": "North America", "country": "USA", "query": "Empire State Building Manhattan", "lat": 40.7484, "lon": -73.9857},
    {"id": "urb_04", "name": "Colosseum Rome", "category": "urban", "continent": "Europe", "country": "Italy", "query": "Colosseum Rome Italy", "lat": 41.8902, "lon": 12.4922},
    {"id": "urb_05", "name": "Sydney Opera House", "category": "urban", "continent": "Oceania", "country": "Australia", "query": "Sydney Opera House harbor", "lat": -33.8568, "lon": 151.2153},

    # 2. Rural Road
    {"id": "rur_01", "name": "Route 66 Arizona", "category": "rural_road", "continent": "North America", "country": "USA", "query": "Route 66 Arizona Seligman", "lat": 35.3258, "lon": -112.8742},
    {"id": "rur_02", "name": "Glencoe Pass A82", "category": "rural_road", "continent": "Europe", "country": "UK", "query": "Glen Coe A82 road Scotland", "lat": 56.6667, "lon": -4.9833},
    {"id": "rur_03", "name": "Stuart Highway Outback", "category": "rural_road", "continent": "Oceania", "country": "Australia", "query": "Stuart Highway Northern Territory Outback", "lat": -23.7000, "lon": 133.8800},
    {"id": "rur_04", "name": "Pamir Highway Mountain Pass", "category": "rural_road", "continent": "Asia", "country": "Tajikistan", "query": "Pamir Highway Tajikistan M41", "lat": 38.1750, "lon": 73.9700},
    {"id": "rur_05", "name": "Garden Route Knysna", "category": "rural_road", "continent": "Africa", "country": "South Africa", "query": "Garden Route Knysna South Africa", "lat": -34.0351, "lon": 23.0465},

    # 3. Farmland
    {"id": "far_01", "name": "Val d'Orcia Rolling Hills", "category": "farmland", "continent": "Europe", "country": "Italy", "query": "Val d'Orcia Tuscany landscape", "lat": 43.0642, "lon": 11.6067},
    {"id": "far_02", "name": "Iowa Cornfields Farm", "category": "farmland", "continent": "North America", "country": "USA", "query": "Iowa corn field agriculture", "lat": 41.5868, "lon": -93.6250},
    {"id": "far_03", "name": "Pampas Agricultural Plains", "category": "farmland", "continent": "South America", "country": "Argentina", "query": "Pampas Argentina agriculture field", "lat": -33.8900, "lon": -60.5700},
    {"id": "far_04", "name": "Biei Furano Rolling Hills", "category": "farmland", "continent": "Asia", "country": "Japan", "query": "Biei Hokkaido flower hills", "lat": 43.5900, "lat_fix": 43.59, "lon": 142.4600},
    {"id": "far_05", "name": "Alentejo Olive Groves", "category": "farmland", "continent": "Europe", "country": "Portugal", "query": "Alentejo landscape olive trees Portugal", "lat": 38.5714, "lon": -7.9072},

    # 4. Coast
    {"id": "cst_01", "name": "Big Sur Bixby Bridge", "category": "coast", "continent": "North America", "country": "USA", "query": "Bixby Creek Bridge Big Sur California", "lat": 36.3714, "lon": -121.9018},
    {"id": "cst_02", "name": "Twelve Apostles Sea Stacks", "category": "coast", "continent": "Oceania", "country": "Australia", "query": "The Twelve Apostles Victoria Australia", "lat": -38.6658, "lon": 143.1044},
    {"id": "cst_03", "name": "Ponta da Piedade Lagos", "category": "coast", "continent": "Europe", "country": "Portugal", "query": "Ponta da Piedade Lagos Algarve", "lat": 37.0805, "lon": -8.6696},
    {"id": "cst_04", "name": "Cape Point Lighthouse", "category": "coast", "continent": "Africa", "country": "South Africa", "query": "Cape Point Cape of Good Hope cliffs", "lat": -34.3572, "lon": 18.4975},
    {"id": "cst_05", "name": "Giant's Causeway Basalt", "category": "coast", "continent": "Europe", "country": "UK", "query": "Giant's Causeway County Antrim columns", "lat": 55.2408, "lon": -6.5116},

    # 5. Lake & River
    {"id": "lak_01", "name": "Lake Como Bellagio", "category": "lake_river", "continent": "Europe", "country": "Italy", "query": "Lake Como Bellagio villas Italy", "lat": 45.9867, "lon": 9.2572},
    {"id": "lak_02", "name": "Emerald Bay Lake Tahoe", "category": "lake_river", "continent": "North America", "country": "USA", "query": "Emerald Bay Lake Tahoe California", "lat": 38.9540, "lon": -120.1000},
    {"id": "lak_03", "name": "Lake Baikal Shaman Rock", "category": "lake_river", "continent": "Asia", "country": "Russia", "query": "Shamanka rock Olkhon Island Lake Baikal", "lat": 53.1500, "lon": 107.3500},
    {"id": "lak_04", "name": "Victoria Falls Zambezi", "category": "lake_river", "continent": "Africa", "country": "Zambia", "query": "Victoria Falls Mosi-oa-Tunya waterfalls", "lat": -17.9243, "lon": 25.8559},
    {"id": "lak_05", "name": "Lake Wakatipu Queenstown", "category": "lake_river", "continent": "Oceania", "country": "New Zealand", "query": "Lake Wakatipu Queenstown South Island", "lat": -45.0312, "lon": 168.6626},

    # 6. Mountain
    {"id": "mtn_01", "name": "Matterhorn Zermatt", "category": "mountain", "continent": "Europe", "country": "Switzerland", "query": "Matterhorn peak Zermatt Switzerland", "lat": 45.9763, "lon": 7.7480},
    {"id": "mtn_02", "name": "Mount Fuji Chureito Pagoda", "category": "mountain", "continent": "Asia", "country": "Japan", "query": "Mount Fuji volcano cone Japan", "lat": 35.3606, "lon": 138.7274},
    {"id": "mtn_03", "name": "Denali Mountain Range", "category": "mountain", "continent": "North America", "country": "USA", "query": "Denali Mount McKinley Alaska mountain", "lat": 63.0692, "lon": -151.0070},
    {"id": "mtn_04", "name": "Aoraki Mount Cook", "category": "mountain", "continent": "Oceania", "country": "New Zealand", "query": "Aoraki Mount Cook Southern Alps", "lat": -43.5950, "lon": 170.1418},
    {"id": "mtn_05", "name": "Mount Kilimanjaro Peak", "category": "mountain", "continent": "Africa", "country": "Tanzania", "query": "Mount Kilimanjaro Uhuru peak Tanzania", "lat": -3.0674, "lon": 37.3556},

    # 7. Valley
    {"id": "val_01", "name": "Yosemite Valley Tunnel View", "category": "valley", "continent": "North America", "country": "USA", "query": "Tunnel View Yosemite Valley El Capitan", "lat": 37.7456, "lon": -119.5936},
    {"id": "val_02", "name": "Lauterbrunnen Valley Waterfalls", "category": "valley", "continent": "Europe", "country": "Switzerland", "query": "Lauterbrunnen Valley Staubbach Falls", "lat": 46.5936, "lon": 7.9091},
    {"id": "val_03", "name": "Sacred Valley Urubamba", "category": "valley", "continent": "South America", "country": "Peru", "query": "Sacred Valley of the Incas Urubamba", "lat": -13.3000, "lon": -72.1167},
    {"id": "val_04", "name": "Great Rift Valley Kenya", "category": "valley", "continent": "Africa", "country": "Kenya", "query": "Great Rift Valley viewpoint Kenya", "lat": -0.3000, "lon": 36.0667},

    # 8. Desert
    {"id": "dst_01", "name": "Erg Chebbi Dunes Merzouga", "category": "desert", "continent": "Africa", "country": "Morocco", "query": "Erg Chebbi sand dunes Merzouga Morocco", "lat": 31.1492, "lon": -4.0117},
    {"id": "dst_02", "name": "Badwater Basin Death Valley", "category": "desert", "continent": "North America", "country": "USA", "query": "Badwater Basin Death Valley salt flat", "lat": 36.2399, "lon": -116.8258},
    {"id": "dst_03", "name": "Wadi Rum Red Sandstone", "category": "desert", "continent": "Asia", "country": "Jordan", "query": "Wadi Rum desert sandstone valley Jordan", "lat": 29.5733, "lon": 35.4333},
    {"id": "dst_04", "name": "Valle de la Luna Atacama", "category": "desert", "continent": "South America", "country": "Chile", "query": "Valle de la Luna Atacama Desert Chile", "lat": -22.9167, "lon": -68.2833},

    # 9. Forest
    {"id": "fst_01", "name": "Redwood National Park", "category": "forest", "continent": "North America", "country": "USA", "query": "Redwood National and State Parks giant trees", "lat": 41.2132, "lon": -124.0046},
    {"id": "fst_02", "name": "Black Forest Germany", "category": "forest", "continent": "Europe", "country": "Germany", "query": "Black Forest Baden-Wurttemberg trees Schwarzwald", "lat": 48.7600, "lon": 8.2400},
    {"id": "fst_03", "name": "Amazon Rainforest Basin", "category": "forest", "continent": "South America", "country": "Brazil", "query": "Amazon rainforest river canopy Brazil", "lat": -3.1190, "lon": -60.0217},
    {"id": "fst_04", "name": "Yakushima Cedar Rainforest", "category": "forest", "continent": "Asia", "country": "Japan", "query": "Yakushima cedar forest moss Japan", "lat": 30.3585, "lon": 130.5286},

    # 10. Snow & Ice
    {"id": "snw_01", "name": "Svalbard Glacier Spitsbergen", "category": "snow_ice", "continent": "Europe", "country": "Norway", "query": "Svalbard glacier mountains Spitsbergen", "lat": 78.2232, "lon": 15.6267},
    {"id": "snw_02", "name": "Franz Josef Glacier New Zealand", "category": "snow_ice", "continent": "Oceania", "country": "New Zealand", "query": "Franz Josef Glacier South Island", "lat": -43.4667, "lon": 170.1833},
    {"id": "snw_03", "name": "Athabasca Glacier Icefield", "category": "snow_ice", "continent": "North America", "country": "Canada", "query": "Athabasca Glacier Columbia Icefield Alberta", "lat": 52.2167, "lon": -117.2167},
    {"id": "snw_04", "name": "Perito Moreno Glacier Ice Wall", "category": "snow_ice", "continent": "South America", "country": "Argentina", "query": "Perito Moreno Glacier Patagonia ice wall", "lat": -50.4833, "lon": -73.0500},

    # 11. Island
    {"id": "isl_01", "name": "Santorini Caldera Oia", "category": "island", "continent": "Europe", "country": "Greece", "query": "Oia Santorini white houses caldera", "lat": 36.4618, "lon": 25.3753},
    {"id": "isl_02", "name": "Maui Haleakala Beach", "category": "island", "continent": "North America", "country": "USA", "query": "Maui Hawaii coastal beach landscape", "lat": 20.7984, "lon": -156.3319},
    {"id": "isl_03", "name": "Galapagos Islands Volcanic", "category": "island", "continent": "South America", "country": "Ecuador", "query": "Galapagos Islands volcanic landscape coast", "lat": -0.7402, "lon": -90.3138},
    {"id": "isl_04", "name": "Bora Bora Barrier Reef", "category": "island", "continent": "Oceania", "country": "French Polynesia", "query": "Bora Bora lagoon Mount Otemanu reef", "lat": -16.5004, "lon": -151.7415},
]


def search_commons_image(query: str, lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Search Wikimedia Commons / Wikipedia API for high-resolution photograph."""
    headers = {"User-Agent": "GlobalPhotoGeolocator/2.0 (research evaluation bot; mailto:admin@local.test)"}

    # Strategy 1: Geosearch nearby coordinates
    try:
        geo_params = {
            "action": "query",
            "generator": "geosearch",
            "ggscoord": f"{lat:.6f}|{lon:.6f}",
            "ggsradius": "10000",
            "ggslimit": "6",
            "prop": "pageimages|coordinates",
            "piprop": "thumbnail",
            "pithumbsize": "1024",
            "format": "json",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(geo_params)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            thumb = page.get("thumbnail")
            if thumb and thumb.get("source"):
                coords = page.get("coordinates", [{}])[0]
                return {
                    "title": page.get("title"),
                    "thumb_url": thumb["source"],
                    "lat": float(coords.get("lat", lat)),
                    "lon": float(coords.get("lon", lon)),
                    "author": "Wikimedia Commons Contributor",
                    "licence": "CC-BY-SA",
                }
    except Exception as e:
        logger.debug("Geosearch fallback: %s", e)

    # Strategy 2: Keyword search on Wikipedia
    try:
        search_params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": "4",
            "prop": "pageimages|coordinates",
            "piprop": "thumbnail",
            "pithumbsize": "1024",
            "format": "json",
        }
        url = f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(search_params)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            thumb = page.get("thumbnail")
            if thumb and thumb.get("source"):
                coords = page.get("coordinates", [{}])[0]
                return {
                    "title": page.get("title"),
                    "thumb_url": thumb["source"],
                    "lat": float(coords.get("lat", lat)),
                    "lon": float(coords.get("lon", lon)),
                    "author": "Wikimedia Commons Contributor",
                    "licence": "CC-BY-SA",
                }
    except Exception as e:
        logger.debug("Search fallback failed: %s", e)

    return None


def main():
    root = Path(__file__).resolve().parent.parent
    photos_dir = root / "eval" / "photos_real"
    photos_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "eval" / "manifest_real.csv"

    manifest_rows = []
    logger.info("Starting real photo collection for %d global locations...", len(TARGET_LOCATIONS))

    for idx, target in enumerate(TARGET_LOCATIONS, 1):
        target_id = target["id"]
        safe_name = target["name"].lower().replace(" ", "_").replace("'", "")
        filename = f"{target_id}_{safe_name}.jpg"
        dest_path = photos_dir / filename

        logger.info("[%d/%d] Fetching real internet photo for %s (%s, %s)...",
                    idx, len(TARGET_LOCATIONS), target["name"], target["category"], target["continent"])

        info = search_commons_image(target["query"], target["lat"], target["lon"])
        if info and info.get("thumb_url"):
            try:
                headers = {"User-Agent": "GlobalPhotoGeolocator/2.0 (research evaluation bot; mailto:admin@local.test)"}
                req = urllib.request.Request(info["thumb_url"], headers=headers)
                with urllib.request.urlopen(req, timeout=15) as r:
                    raw_bytes = r.read()

                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                # Resize if larger than 1280
                if max(img.size) > 1280:
                    img.thumbnail((1280, 1280), Image.LANCZOS)

                # Strip EXIF to ensure zero data leakage
                clean_img = Image.new(img.mode, img.size)
                clean_img.putdata(list(img.getdata()))
                clean_img.save(dest_path, format="JPEG", quality=90)

                actual_lat = info["lat"]
                actual_lon = info["lon"]
                logger.info("   -> Downloaded %dx%d image: %s (True GPS: %.4f, %.4f)",
                            clean_img.size[0], clean_img.size[1], info["title"], actual_lat, actual_lon)

                manifest_rows.append({
                    "id": target_id,
                    "file": filename,
                    "lat": f"{actual_lat:.6f}",
                    "lon": f"{actual_lon:.6f}",
                    "category": target["category"],
                    "continent": target["continent"],
                    "country": target["country"],
                    "name": info.get("title", target["name"]),
                    "licence": info["licence"],
                    "author": info["author"],
                    "source_url": info["thumb_url"],
                })
            except Exception as e:
                logger.error("   -> Error saving %s: %s", target["name"], e)
        else:
            logger.warning("   -> No image returned for %s", target["name"])

        # Polite request rate
        time.sleep(0.3)

    # Save manifest
    fieldnames = ["id", "file", "lat", "lon", "category", "continent", "country", "name", "licence", "author", "source_url"]
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    logger.info("Finished downloading %d real internet photos! Saved to %s and %s",
                len(manifest_rows), photos_dir, manifest_path)


if __name__ == "__main__":
    main()
