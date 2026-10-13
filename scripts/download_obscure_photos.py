"""Download 10 authentic obscure photos from Wikipedia geosearch and strip all EXIF."""
import csv
import io
import json
import logging
from pathlib import Path
import urllib.parse
import urllib.request
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("download_obscure")

output_dir = Path("eval/photos_obscure")
output_dir.mkdir(parents=True, exist_ok=True)

# Clean out any old dummy files (< 50 KB)
for f in output_dir.glob("*.jpg"):
    if f.stat().st_size < 50000:
        f.unlink()
        logger.info("Deleted dummy: %s", f.name)

coords = [
    ("obs_01", "Somero, Finland", "Finland", "Europe", "rural_town", 60.6333, 23.5167),
    ("obs_02", "Datil, New Mexico", "USA", "North America", "desert_junction", 34.1422, -107.8425),
    ("obs_03", "Moros, Zaragoza", "Spain", "Europe", "provincial_town", 41.4000, -1.8167),
    ("obs_04", "Sawama Station", "Japan", "Asia", "mountain_rail", 35.1247, 138.1344),
    ("obs_05", "Pirai River", "Brazil", "South America", "rural_river", -24.7500, -50.0833),
    ("obs_06", "Narrabri", "Australia", "Oceania", "outback_town", -30.3167, 149.7667),
    ("obs_07", "Haripur Countryside", "Pakistan", "Asia", "rural_foothills", 33.9942, 72.9333),
    ("obs_08", "Ouarzazate", "Morocco", "Africa", "arid_clay_village", 30.9167, -6.9167),
    ("obs_09", "Brecon", "UK", "Europe", "river_valley", 51.9480, -3.3910),
    ("obs_10", "Nanyuki", "Kenya", "Africa", "highland_town", 0.0167, 37.0667),
]

headers = {
    "User-Agent": "GlobalPhotoGeolocator/1.0 (Academic Geolocation Research Benchmark; contact geoloc@test.org)"
}
manifest_rows = []

for cid, name, country, continent, category, lat, lon in coords:
    safe_country = country.lower().replace(" ", "_")
    filename = f"{cid}_{safe_country}_{category}.jpg"
    photo_path = output_dir / filename

    if photo_path.exists() and photo_path.stat().st_size >= 50000:
        logger.info("%s already downloaded and verified (%d bytes)", cid, photo_path.stat().st_size)
        manifest_rows.append({
            "id": cid,
            "name": name,
            "category": category,
            "country": country,
            "continent": continent,
            "true_lat": lat,
            "true_lon": lon,
            "filename": filename,
            "filepath": str(photo_path),
        })
        continue

    params = {
        "action": "query",
        "generator": "geosearch",
        "ggscoord": f"{lat:.4f}|{lon:.4f}",
        "ggsradius": "10000",
        "ggslimit": "10",
        "prop": "coordinates|pageimages",
        "piprop": "thumbnail",
        "pithumbsize": "800",
        "format": "json",
    }
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read())
    pages = data.get("query", {}).get("pages", {})

    downloaded = False
    for pid, p in pages.items():
        thumb = p.get("thumbnail", {}).get("source")
        if thumb and not any(k in thumb for k in (".svg", "Flag", "Coat", "Map", "Locator", "Icon", "Emblem")):
            try:
                treq = urllib.request.Request(thumb, headers=headers)
                with urllib.request.urlopen(treq, timeout=15) as tr:
                    raw_bytes = tr.read()

                # Cleanly strip EXIF by saving pure RGB pixel buffer
                im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                im.save(photo_path, format="JPEG", quality=92)
                c = p.get("coordinates", [{}])[0]
                t_lat = float(c.get("lat", lat))
                t_lon = float(c.get("lon", lon))
                t_title = p.get("title", name)
                size = photo_path.stat().st_size
                logger.info("%s: Saved %s (%s) -> %d bytes (%0.4f, %0.4f)", cid, filename, t_title, size, t_lat, t_lon)
                manifest_rows.append({
                    "id": cid,
                    "name": t_title,
                    "category": category,
                    "country": country,
                    "continent": continent,
                    "true_lat": t_lat,
                    "true_lon": t_lon,
                    "filename": filename,
                    "filepath": str(photo_path),
                })
                downloaded = True
                break
            except Exception as e:
                logger.warning("Download error for %s: %s", cid, e)

    if not downloaded:
        logger.error("%s: FAILED to download photo!", cid)

manifest_csv = Path("eval/manifest_obscure.csv")
with open(manifest_csv, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
    writer.writeheader()
    writer.writerows(manifest_rows)

logger.info("Manifest updated with %d valid photos at %s", len(manifest_rows), manifest_csv)
