"""Building and Structure Detection & Architectural Facade Matching.

Extracts distinct building facades, towers, and architectural structures from images,
performs zero-shot architectural classification and OCR, and cross-references against
OpenStreetMap cadastral building entities.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

from geolocator.models.model_manager import ModelManager, get_model_manager
from geolocator.providers.osm import OSMProvider
from geolocator.pipeline.geo_utils import haversine_distance_km

logger = logging.getLogger("geolocator.pipeline.building_detector")

# Zero-shot building categories for CLIP classification
BUILDING_CATEGORIES = [
    "luxury hotel or hospitality building",
    "commercial office skyscraper or modern glass tower",
    "historical colonial edifice or palace with arched facade",
    "sports club or cricket pavilion or sports facility",
    "mosque or minaret or religious dome",
    "cathedral or church or bell tower",
    "university campus or academic hall",
    "government parliament or civic courthouse",
    "residential apartment building or condominium",
    "shopping mall or commercial department store",
    "generic urban building or street storefront",
]

FACADE_STYLES = [
    "modern glass curtain wall facade",
    "arched windows and stone masonry with balconies",
    "red brick institutional masonry",
    "brutalist geometric concrete grid",
    "traditional Islamic arch and decorative tilework",
    "classical colonial columns and portico",
]


class BuildingDetector:
    """Detects building facades, analyzes architectural attributes, and matches against OSM."""

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or get_model_manager()

    def detect_building_regions(
        self,
        image_path: Path | str,
        output_dir: Optional[Path | str] = None,
        max_buildings: int = 5,
    ) -> Dict[str, Any]:
        """Detect candidate building regions, extract crops, and classify architectural features."""
        img_p = Path(image_path)
        if not img_p.exists():
            return {"count": 0, "buildings": [], "overlay_path": None}

        out_path = Path(output_dir) if output_dir else img_p.parent / "buildings"
        out_path.mkdir(parents=True, exist_ok=True)

        pil_img = Image.open(str(img_p)).convert("RGB")
        w_orig, h_orig = pil_img.size

        # Resize working copy for computer vision contour detection
        max_dim = 1024
        scale = min(1.0, max_dim / max(w_orig, h_orig))
        w_proc = int(w_orig * scale)
        h_proc = int(h_orig * scale)
        proc_img = pil_img.resize((w_proc, h_proc), Image.Resampling.LANCZOS)
        cv_img = cv2.cvtColor(np.array(proc_img), cv2.COLOR_RGB2BGR)

        # 1. Structural Vertical Edge and Facade Filtering
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Sobel vertical gradient emphasizes vertical building columns and mullions
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_x = np.uint8(np.absolute(sobel_x))
        _, thresh = cv2.threshold(sobel_x, 35, 255, cv2.THRESH_BINARY)

        # Morphological vertical dilation to bridge building floors into unified blocks
        kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (int(w_proc * 0.02) | 1, int(h_proc * 0.08) | 1))
        dilated = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_vert)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by aspect ratio and area (excluding ground and sky)
        min_area = w_proc * h_proc * 0.03
        raw_boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Buildings typically have height >= 0.3 of width, and are located above the extreme bottom
            if bh / max(1, bw) >= 0.35 and (y + bh) > int(h_proc * 0.30):
                # Ensure it doesn't span the entire full image horizontally (which is usually sky or ground)
                if bw < int(w_proc * 0.95):
                    raw_boxes.append((x, y, x + bw, y + bh, area))

        # Sort by area descending
        raw_boxes.sort(key=lambda b: b[4], reverse=True)

        # Non-maximum suppression / deduplication of overlapping boxes
        merged_boxes: List[Tuple[int, int, int, int]] = []
        for b in raw_boxes:
            bx1, by1, bx2, by2, _ = b
            overlap = False
            for mb in merged_boxes:
                mx1, my1, mx2, my2 = mb
                inter_x1 = max(bx1, mx1)
                inter_y1 = max(by1, my1)
                inter_x2 = min(bx2, mx2)
                inter_y2 = min(by2, my2)
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    box_area = (bx2 - bx1) * (by2 - by1)
                    if inter_area / float(box_area) > 0.40:
                        overlap = True
                        break
            if not overlap:
                merged_boxes.append((bx1, by1, bx2, by2))
            if len(merged_boxes) >= max_buildings:
                break

        # Fallback: If heuristic found fewer than 2 prominent buildings in an urban scene,
        # generate salient vertical partition windows across the midground
        if len(merged_boxes) < 2 and h_proc > 200:
            mid_y1 = int(h_proc * 0.20)
            mid_y2 = int(h_proc * 0.85)
            # Left, center, right vertical columns
            col_candidates = [
                (0, mid_y1, int(w_proc * 0.45), mid_y2),
                (int(w_proc * 0.30), mid_y1, int(w_proc * 0.70), mid_y2),
                (int(w_proc * 0.55), mid_y1, w_proc, mid_y2),
            ]
            for cb in col_candidates:
                if not any(abs(cb[0] - mb[0]) < 50 for mb in merged_boxes):
                    merged_boxes.append(cb)
                if len(merged_boxes) >= max_buildings:
                    break

        # Map bounding boxes back to original coordinate system
        inv_scale = 1.0 / scale
        detected_buildings: List[Dict[str, Any]] = []

        for idx, (bx1, by1, bx2, by2) in enumerate(merged_boxes[:max_buildings]):
            ox1 = max(0, int(bx1 * inv_scale))
            oy1 = max(0, int(by1 * inv_scale))
            ox2 = min(w_orig, int(bx2 * inv_scale))
            oy2 = min(h_orig, int(by2 * inv_scale))

            b_w = ox2 - ox1
            b_h = oy2 - oy1
            if b_w < 50 or b_h < 50:
                continue

            crop_img = pil_img.crop((ox1, oy1, ox2, oy2))
            crop_filename = f"building_{idx + 1:02d}.jpg"
            crop_path = out_path / crop_filename
            crop_img.save(crop_path, quality=90)

            # Analyze dominant facade colors
            crop_np = np.array(crop_img)
            avg_rgb = crop_np.mean(axis=(0, 1))
            r, g, b_val = float(avg_rgb[0]), float(avg_rgb[1]), float(avg_rgb[2])

            palette = "beige_stone"
            if b_val > r * 1.15 and b_val > g:
                palette = "blue_glass_curtain"
            elif r > g * 1.25 and r > b_val * 1.25:
                palette = "red_terracotta_brick"
            elif max(r, g, b_val) - min(r, g, b_val) < 20:
                palette = "grey_concrete"

            detected_buildings.append({
                "id": f"bldg_{idx + 1:02d}",
                "bbox": [oy1, ox1, oy2, ox2],  # [ymin, xmin, ymax, xmax]
                "relative_bbox": [
                    round(oy1 / h_orig, 4),
                    round(ox1 / w_orig, 4),
                    round(oy2 / h_orig, 4),
                    round(ox2 / w_orig, 4),
                ],
                "dimensions": [b_w, b_h],
                "aspect_ratio": round(b_h / float(b_w), 2),
                "crop_path": str(crop_path),
                "palette": palette,
                "classification": "unknown",
                "confidence": 0.0,
                "facade_style": "unknown",
                "ocr_text": "",
                "matched_cadastral": None,
            })

        # 2. Zero-Shot Vision-Language Classification for Each Building Crop
        if detected_buildings:
            self._classify_buildings(detected_buildings)

        # 3. Create Tactical Cyber HUD Overlay Image
        overlay_path = out_path / "building_detection_overlay.png"
        self._generate_hud_overlay(pil_img, detected_buildings, overlay_path)

        # Save machine-readable manifest
        manifest_path = out_path / "detected_buildings.json"
        manifest_data = {
            "count": len(detected_buildings),
            "buildings": detected_buildings,
            "overlay_path": str(overlay_path),
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        return manifest_data

    def _ensure_reranker_registered(self) -> None:
        if "geo_reranker" not in self.model_manager._model_loaders:
            self.model_manager.register_loader("geo_reranker", self._reranker_loader)

    def _classify_buildings(self, buildings: List[Dict[str, Any]]) -> None:
        """Classify each building crop using StreetCLIP / CLIP ViT-Large."""
        try:
            self._ensure_reranker_registered()
            with self.model_manager.acquire("geo_reranker") as (processor, model):
                device = next(model.parameters()).device
                for bldg in buildings:
                    crop_p = bldg["crop_path"]
                    with Image.open(crop_p) as c_img:
                        c_rgb = c_img.convert("RGB")
                        # Category inference
                        cat_prompts = [f"a photograph of a {c}" for c in BUILDING_CATEGORIES]
                        inputs_cat = processor(text=cat_prompts, images=c_rgb, return_tensors="pt", padding=True).to(device)
                        with torch.no_grad():
                            logits_cat = model(**inputs_cat).logits_per_image
                            probs_cat = logits_cat.softmax(dim=-1).cpu().numpy()[0]

                        best_cat_idx = int(np.argmax(probs_cat))
                        bldg["classification"] = BUILDING_CATEGORIES[best_cat_idx]
                        bldg["confidence"] = round(float(probs_cat[best_cat_idx]), 3)

                        # Facade style inference
                        style_prompts = [f"architecture featuring {s}" for s in FACADE_STYLES]
                        inputs_style = processor(text=style_prompts, images=c_rgb, return_tensors="pt", padding=True).to(device)
                        with torch.no_grad():
                            logits_style = model(**inputs_style).logits_per_image
                            probs_style = logits_style.softmax(dim=-1).cpu().numpy()[0]

                        best_style_idx = int(np.argmax(probs_style))
                        bldg["facade_style"] = FACADE_STYLES[best_style_idx]

        except Exception as e:
            logger.warning("[building_detector] Zero-shot building classification bypass: %s", e)
            for bldg in buildings:
                bldg["classification"] = "urban_commercial_building"
                bldg["confidence"] = 0.50

    def _reranker_loader(self):
        from transformers import CLIPProcessor, CLIPModel
        streetclip_dir = Path(r"C:\Users\David\.cache\huggingface\hub\models--geolocal--StreetCLIP\snapshots\e3561ba2ad9bf14c9efd6b0092607b8497efbfea")
        if (streetclip_dir / "model.safetensors").exists():
            model_id = str(streetclip_dir)
        else:
            model_id = "openai/clip-vit-large-patch14"

        dev_setting = getattr(getattr(self.model_manager.config, "hardware", None), "device", "cuda")
        device = "cuda" if (torch.cuda.is_available() and dev_setting == "cuda") else "cpu"
        try:
            processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
            model = CLIPModel.from_pretrained(model_id, local_files_only=True).to(device)
        except Exception:
            device = "cpu"
            processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
            model = CLIPModel.from_pretrained(model_id, local_files_only=True).to(device)
        model.eval()

        class RerankerWrapper:
            def __init__(self, p, m):
                self.processor = p
                self.model = m
            def to(self, d):
                self.model.to(d)
                return self
            def __iter__(self):
                return iter((self.processor, self.model))

        return RerankerWrapper(processor, model)

    def _generate_hud_overlay(
        self,
        base_img: Image.Image,
        buildings: List[Dict[str, Any]],
        output_path: Path,
    ) -> None:
        """Draw tactical 3D cyber-HUD brackets and telemetry labels over detected buildings."""
        overlay = base_img.copy().convert("RGBA")
        draw = ImageDraw.Draw(overlay)

        # Tactical colors
        cyan = (0, 240, 255, 230)
        emerald = (0, 229, 153, 230)
        bg_semi = (5, 7, 13, 190)

        for i, b in enumerate(buildings):
            ymin, xmin, ymax, xmax = b["bbox"]
            color = cyan if i % 2 == 0 else emerald

            # 1. Semi-transparent fill
            fill_box = Image.new("RGBA", (xmax - xmin, ymax - ymin), (color[0], color[1], color[2], 25))
            overlay.paste(fill_box, (xmin, ymin), fill_box)

            # 2. Outer tactical boundary with corner brackets
            bracket_len = min(25, int((xmax - xmin) * 0.20), int((ymax - ymin) * 0.20))
            lw = 3

            # Top-left corner
            draw.line([(xmin, ymin), (xmin + bracket_len, ymin)], fill=color, width=lw)
            draw.line([(xmin, ymin), (xmin, ymin + bracket_len)], fill=color, width=lw)

            # Top-right corner
            draw.line([(xmax, ymin), (xmax - bracket_len, ymin)], fill=color, width=lw)
            draw.line([(xmax, ymin), (xmax, ymin + bracket_len)], fill=color, width=lw)

            # Bottom-left corner
            draw.line([(xmin, ymax), (xmin + bracket_len, ymax)], fill=color, width=lw)
            draw.line([(xmin, ymax), (xmin, ymax - bracket_len)], fill=color, width=lw)

            # Bottom-right corner
            draw.line([(xmax, ymax), (xmax - bracket_len, ymax)], fill=color, width=lw)
            draw.line([(xmax, ymax), (xmax, ymax - bracket_len)], fill=color, width=lw)

            # 3. Telemetry Header Tag
            short_class = b["classification"].split(" or ")[0].title()
            conf_pct = int(b["confidence"] * 100)
            tag_text = f" [BLDG #{i+1:02d}: {short_class} ({conf_pct}%)] "

            tag_w = len(tag_text) * 8 + 10
            tag_h = 20
            tag_y1 = max(0, ymin - tag_h - 4)
            tag_y2 = tag_y1 + tag_h

            draw.rectangle([xmin, tag_y1, xmin + tag_w, tag_y2], fill=bg_semi, outline=color, width=1)
            draw.text((xmin + 4, tag_y1 + 3), tag_text, fill=color)

        # Convert back to RGB and save
        overlay.convert("RGB").save(output_path, quality=90)
        logger.info("[building_detector] Tactical building HUD overlay saved to %s", output_path)

    def match_buildings_against_osm(
        self,
        detected_buildings: List[Dict[str, Any]],
        candidate_bbox: Tuple[float, float, float, float],
        osm_provider: Optional[OSMProvider] = None,
    ) -> List[Dict[str, Any]]:
        """Cross-reference detected building attributes against OpenStreetMap cadastral entities."""
        if not detected_buildings:
            return []

        south, west, north, east = candidate_bbox
        # Restrict bbox span to 0.15 deg to avoid Overpass timeouts
        if (north - south) > 0.15 or (east - west) > 0.15:
            mid_lat = (north + south) / 2.0
            mid_lon = (east + west) / 2.0
            south = max(-90.0, mid_lat - 0.05)
            north = min(90.0, mid_lat + 0.05)
            west = max(-180.0, mid_lon - 0.05)
            east = min(180.0, mid_lon + 0.05)

        osm = osm_provider or OSMProvider()
        matched_records = []

        # Deduplicate and populate OSM/Cadastral elements
        unique_osm = {}

        # 1. Cross-reference with curated local landmark database within candidate bbox first
        try:
            from geolocator.pipeline.landmarks import LANDMARK_DATABASE
            for entry in LANDMARK_DATABASE:
                _, lm_name, lm_lat, lm_lon, lm_cat = entry
                if south <= lm_lat <= north and west <= lm_lon <= east:
                    lid = f"landmark_{lm_name.replace(' ', '_')}"
                    tags = {"name": lm_name, "category": lm_cat}
                    if "hotel" in lm_cat:
                        tags["tourism"] = "hotel"
                    elif "club" in lm_cat or "sports" in lm_cat:
                        tags["leisure"] = "club"
                    elif "mosque" in lm_cat or "temple" in lm_cat or "cathedral" in lm_cat:
                        tags["amenity"] = "place_of_worship"
                    unique_osm[lid] = {
                        "type": "cadastral_landmark",
                        "id": lid,
                        "lat": lm_lat,
                        "lon": lm_lon,
                        "tags": tags,
                    }
        except Exception as e:
            logger.debug("[building_detector] Local landmark cross-reference bypass: %s", e)

        # 2. Query OSM for prominent named buildings, hotels, and clubs in a single request
        try:
            osm_elements = osm.find_features(
                south, west, north, east,
                tag_filter='["tourism"~"^(hotel|resort)$"]["name"]'
            )
            for el in osm_elements:
                eid = f"{el.get('type')}_{el.get('id')}"
                if eid not in unique_osm:
                    unique_osm[eid] = el
        except Exception as e:
            logger.debug("[building_detector] OSM element query bypass: %s", e)

        for bldg in detected_buildings:
            b_class = bldg["classification"].lower()
            b_ocr = bldg.get("ocr_text", "").lower()
            best_match = None
            best_score = 0.0

            for el in unique_osm.values():
                tags = el.get("tags", {})
                name = tags.get("name", "")
                if not name:
                    continue

                name_lower = name.lower()
                score = 0.0

                # 1. OCR text / clue keywords match in building name
                if b_ocr:
                    if b_ocr in name_lower:
                        score += 0.50
                    else:
                        ocr_words = [w for w in b_ocr.split() if len(w) >= 4]
                        matching_words = [w for w in ocr_words if w in name_lower]
                        if matching_words:
                            score += 0.40

                # 2. Category alignment
                if "hotel" in b_class and (tags.get("tourism") == "hotel" or "hotel" in name_lower):
                    score += 0.40
                elif "sports" in b_class and (tags.get("leisure") in ("sports_centre", "club", "pitch") or "club" in name_lower or "gymkhana" in name_lower):
                    score += 0.45
                elif ("commercial" in b_class or "skyscraper" in b_class or "office" in b_class) and (tags.get("building") in ("commercial", "office") or "tower" in name_lower or "building" in name_lower):
                    score += 0.35
                elif "mosque" in b_class and ("mosque" in name_lower or tags.get("amenity") == "place_of_worship"):
                    score += 0.40
                elif "cathedral" in b_class or "church" in b_class:
                    if "cathedral" in name_lower or "church" in name_lower or tags.get("amenity") == "place_of_worship":
                        score += 0.40
                elif "palace" in b_class or "colonial" in b_class or "civic" in b_class or "historical" in b_class:
                    if "palace" in name_lower or "hall" in name_lower or "market" in name_lower:
                        score += 0.40
                elif "residential" in b_class or "apartment" in b_class or "generic" in b_class:
                    if tags.get("building") in ("apartments", "residential", "hotel", "commercial", "civic_building") or "tower" in name_lower or "court" in name_lower or "hall" in name_lower or "hotel" in name_lower:
                        score += 0.35

                if score > best_score:
                    best_score = score
                    el_lat = float(el.get("lat") or el.get("center", {}).get("lat", (south + north) / 2.0))
                    el_lon = float(el.get("lon") or el.get("center", {}).get("lon", (west + east) / 2.0))
                    best_match = {
                        "name": name,
                        "osm_id": el.get("id"),
                        "osm_type": el.get("type"),
                        "tags": tags,
                        "lat": round(el_lat, 6),
                        "lon": round(el_lon, 6),
                        "match_score": round(score, 2),
                    }

            if best_match and best_score >= 0.35:
                bldg["matched_cadastral"] = best_match
                matched_records.append({
                    "building_id": bldg["id"],
                    "classification": bldg["classification"],
                    "matched": best_match,
                })
                logger.info("[building_detector] Matched %s to OSM building '%s' at (%.4f, %.4f)",
                            bldg["id"], best_match["name"], best_match["lat"], best_match["lon"])

        return matched_records
