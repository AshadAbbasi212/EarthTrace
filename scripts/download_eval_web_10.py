import sys
from pathlib import Path
import csv
from PIL import Image

sys.path.insert(0, str(Path("src").resolve()))
from geolocator.providers.street_image import StreetImageProvider

out_dir = Path("eval/photos_web_10")
out_dir.mkdir(parents=True, exist_ok=True)

targets = [
    {"id": "web_01", "name": "Shibuya Crossing, Tokyo", "country": "Japan", "lat": 35.6595, "lon": 139.7005},
    {"id": "web_02", "name": "Colosseum, Rome", "country": "Italy", "lat": 41.8902, "lon": 12.4922},
    {"id": "web_03", "name": "Lake Louise, Banff", "country": "Canada", "lat": 51.4254, "lon": -116.1773},
    {"id": "web_04", "name": "Giza Pyramids, Cairo", "country": "Egypt", "lat": 29.9792, "lon": 31.1342},
    {"id": "web_05", "name": "Sydney Opera House", "country": "Australia", "lat": -33.8568, "lon": 151.2153},
    {"id": "web_06", "name": "Sugarloaf Mountain, Rio", "country": "Brazil", "lat": -22.9492, "lon": -43.1545},
    {"id": "web_07", "name": "Vik Black Beach", "country": "Iceland", "lat": 63.4044, "lon": -19.0494},
    {"id": "web_08", "name": "Table Mountain, Cape Town", "country": "South Africa", "lat": -33.9628, "lon": 18.4098},
    {"id": "web_09", "name": "Taj Mahal, Agra", "country": "India", "lat": 27.1751, "lon": 78.0421},
    {"id": "web_10", "name": "Machu Picchu, Cusco", "country": "Peru", "lat": -13.1631, "lon": -72.5450},
]

provider = StreetImageProvider()
downloaded = []

for t in targets:
    lat, lon = t["lat"], t["lon"]
    print(f"Searching images near {t['name']} ({lat}, {lon})...")
    images = provider.find_nearby_images(lat=lat, lon=lon, radius_m=2500, limit=5)
    if not images:
        print(f"  No image found for {t['name']}, expanding radius...")
        images = provider.find_nearby_images(lat=lat, lon=lon, radius_m=8000, limit=5)
    
    if images:
        best_img_info = images[0]
        url = best_img_info["image_url"]
        img = provider.fetch_image(url)
        if img:
            clean_name = t["name"].replace(" ", "_").replace(",", "").replace("/", "_")
            fname = f"{t['id']}_{clean_name}.jpg"
            fpath = out_dir / fname
            img.save(fpath, format="JPEG", quality=90)
            
            entry = {
                "id": t["id"],
                "name": t["name"],
                "country": t["country"],
                "true_lat": t["lat"],
                "true_lon": t["lon"],
                "photo_title": best_img_info.get("title", ""),
                "url": url,
                "filename": fname,
                "filepath": str(fpath),
            }
            downloaded.append(entry)
            print(f"  -> Successfully downloaded {fname} ({img.size[0]}x{img.size[1]})")
        else:
            print(f"  -> Failed to fetch image bytes from {url}")
    else:
        print(f"  -> No Wikimedia images found near {t['name']}")

manifest_path = Path("eval/manifest_web_10.csv")
with open(manifest_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "country", "true_lat", "true_lon", "photo_title", "url", "filename", "filepath"])
    writer.writeheader()
    writer.writerows(downloaded)

print(f"\nSaved manifest to {manifest_path} with {len(downloaded)} verified entries.")
