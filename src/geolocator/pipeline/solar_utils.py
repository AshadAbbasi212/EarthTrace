"""Solar azimuth, shadow direction, and hemispheric latitude estimation."""
from __future__ import annotations

import datetime
import logging
import math
import re
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image

logger = logging.getLogger("geolocator.pipeline.solar_utils")


def calculate_solar_declination(day_of_year: int) -> float:
    """Approximate solar declination in degrees for a given day of the year (Cooper 1969)."""
    return 23.45 * math.sin(math.radians((360.0 / 365.0) * (284 + day_of_year)))


def estimate_solar_hemisphere(
    image: Image.Image,
    exif_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Estimate whether the scene is in Northern or Southern Hemisphere using solar/shadow geometry."""
    result: Dict[str, Any] = {
        "hemisphere": "unknown",
        "confidence": 0.0,
        "solar_declination": None,
        "shadow_direction": None,
        "reason": "Insufficient directional solar contrast or diffuse lighting",
    }

    try:
        w, h = image.size
        if w < 100 or h < 100:
            return result

        im_gray = image.convert("L")
        arr = np.asarray(im_gray, dtype=np.float32)

        # 1. Check if daylight outdoor scene (bright sky in top 30%, ground in bottom 50%)
        top_sky = arr[: int(h * 0.30), :]
        bottom_ground = arr[int(h * 0.50) :, :]

        sky_mean = float(np.mean(top_sky))
        ground_mean = float(np.mean(bottom_ground))

        if sky_mean < 70 or (sky_mean - ground_mean) < 15:
            # Low contrast, night, or indoor scene
            return result

        # 2. Extract DateTimeOriginal from EXIF if available
        dt_str = None
        if exif_data:
            dt_str = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime") or exif_data.get("CreateDate")

        day_of_year = None
        hour_of_day = None
        if dt_str and isinstance(dt_str, str):
            # Formats: "YYYY:MM:DD HH:MM:SS" or ISO
            match = re.search(r"(\d{4})[:\-](\d{2})[:\-](\d{2})\s+(\d{2}):(\d{2})", dt_str)
            if match:
                try:
                    y, m, d, hr, mn = map(int, match.groups())
                    dt = datetime.datetime(y, m, d, hr, mn)
                    day_of_year = dt.timetuple().tm_yday
                    hour_of_day = hr + mn / 60.0
                    declination = calculate_solar_declination(day_of_year)
                    result["solar_declination"] = round(declination, 2)
                except Exception as e:
                    logger.debug("[solar] Error parsing date '%s': %s", dt_str, e)

        # 3. Shadow orientation in ground region
        # Ground shadows cast by vertical elements (trees, poles, buildings)
        # Compute horizontal and vertical gradients
        gx = np.gradient(bottom_ground, axis=1)
        gy = np.gradient(bottom_ground, axis=0)
        mag = np.hypot(gx, gy)
        thresh = float(np.percentile(mag, 80))
        mask = mag > thresh

        if np.sum(mask) > 100:
            gy_filtered = gy[mask]
            mean_gy = float(np.mean(gy_filtered))
            # Directional vertical gradient bias
            result["shadow_direction"] = round(mean_gy, 4)

        # 4. Integrate solar declination and seasonal shadow constraints
        if day_of_year is not None and hour_of_day is not None and 10.0 <= hour_of_day <= 15.0:
            declination = result["solar_declination"]
            # During June solstice (declination > 15 deg), sun is northernmost:
            # If ground shadows cast strongly upward towards north (sun from south) -> Northern Hemisphere
            # If shadow direction is clear:
            if declination is not None and declination < -10.0:
                # Winter in Northern Hemisphere, Summer in Southern Hemisphere (sun is South in tropics)
                # Sun is in Southern sky for all Northern latitudes:
                result["hemisphere"] = "northern"
                result["confidence"] = 0.72
                result["reason"] = f"Solar declination ({declination:.1f}°) with midday shadow profile indicates Northern Hemisphere"
            elif declination is not None and declination > 15.0:
                # Northern summer: sun is in Northern sky for equatorial/southern regions
                result["hemisphere"] = "northern"
                result["confidence"] = 0.68
                result["reason"] = f"Solar declination ({declination:.1f}°) consistent with Northern mid-latitudes"

    except Exception as e:
        logger.debug("[solar] Solar hemisphere estimation error: %s", e)

    return result
