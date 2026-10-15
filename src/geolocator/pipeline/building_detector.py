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
    "commercial office skyscraper, glass tower, or blue glass curtain facade",
    "historical colonial edifice or palace with arched facade",
    "sports club or cricket pavilion or sports facility",
    "mosque or minaret or religious dome",
    "cathedral or church or bell tower",
    "university campus or academic hall",
    "government parliament or civic courthouse",
    "residential apartment building or condominium",
    "red brick masonry building, house, or hotel facade",
    "shopping mall or commercial department store",
    "generic urban building or street storefront",
]

NON_BUILDING_CATEGORIES = [
    "an airplane, fighter jet, or aircraft monument",
    "a statue, sculpture, or non-building monument",
    "trees, forest, foliage, or natural vegetation",
    "a vehicle, car, bus, or truck",
    "empty open sky or asphalt road with no architecture",
    "outdoor park, open field, or recreation ground without buildings",
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

    def has_prominent_buildings(self, image: Image.Image | Path | str) -> bool:
        """Fast zero-shot verification to ensure scene genuinely features architectural building facades."""
        try:
            if isinstance(image, (str, Path)):
                p = Path(image)
                if not p.exists():
                    return False
                with Image.open(p) as img_file:
                    pil_img = img_file.convert("RGB")
                    return self.has_prominent_buildings(pil_img)

            self._ensure_reranker_registered()
            with self.model_manager.acquire("geo_reranker") as (processor, model):
                device = next(model.parameters()).device
                prompts = [
                    "architectural buildings, skyscrapers, houses, or city facades",
                    "an airplane, vehicle, monument, or natural terrain without buildings",
                ]
                inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True).to(device)
                with torch.no_grad():
                    probs = model(**inputs).logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                has_bldg = float(probs[0]) >= 0.40
                logger.info("[building_detector] Building presence check: bldg=%.3f, non_bldg=%.3f -> %s", probs[0], probs[1], has_bldg)
                return has_bldg
        except Exception as e:
            logger.debug("[building_detector] Building presence check bypass: %s", e)
            return True

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

        # Zero-shot gating: If image does not feature prominent building facades, bypass immediately!
        if not self.has_prominent_buildings(pil_img):
            logger.info("[building_detector] Bypassing detection: image does not contain prominent building facades.")
            manifest_path = out_path / "detected_buildings.json"
            manifest_data = {
                "count": 0,
                "buildings": [],
                "overlay_path": None,
                "status": "not_applicable",
                "reason": "No prominent architectural building facades detected in scene.",
            }
            manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            return manifest_data

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

        # Morphological vertical dilation to bridge building floors and columns into unified blocks
        kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (int(w_proc * 0.06) | 1, int(h_proc * 0.08) | 1))
        dilated = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_vert)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by aspect ratio and area (excluding ground and sky)
        min_area = w_proc * h_proc * 0.02
        raw_boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Check contour area or bounding box area
            effective_area = max(area, bw * bh * 0.40)
            if effective_area < min_area:
                continue
            # Buildings typically have height >= 0.3 of width, and are located above the extreme bottom
            if bh / max(1, bw) >= 0.35 and (y + bh) > int(h_proc * 0.30):
                # Ensure it doesn't span the entire full image horizontally (which is usually sky or ground)
                if bw < int(w_proc * 0.95):
                    raw_boxes.append((x, y, x + bw, y + bh, effective_area))

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

        # If no genuine building contours isolated, do not hallucinate buildings!
        if not merged_boxes:
            logger.info("[building_detector] No prominent structural building contours isolated.")
            manifest_path = out_path / "detected_buildings.json"
            manifest_data = {
                "count": 0,
                "buildings": [],
                "overlay_path": None,
                "status": "not_applicable",
                "reason": "No prominent architectural building facades detected in scene.",
            }
            manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            return manifest_data

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
                "is_building": True,
            })

        # 2. Zero-Shot Vision-Language Classification for Each Building Crop
        if detected_buildings:
            self._classify_buildings(detected_buildings)
            # Filter out non-building crops (e.g. aircraft, vehicles, trees, ground)
            detected_buildings = [b for b in detected_buildings if b.get("is_building", True)]

        if not detected_buildings:
            logger.info("[building_detector] All candidate crops classified as non-building objects.")
            manifest_path = out_path / "detected_buildings.json"
            manifest_data = {
                "count": 0,
                "buildings": [],
                "overlay_path": None,
                "status": "not_applicable",
                "reason": "No prominent architectural building facades detected in scene.",
            }
            manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            return manifest_data

        # 3. Create Tactical Cyber HUD Overlay Image
        overlay_path = out_path / "building_detection_overlay.png"
        self._generate_hud_overlay(pil_img, detected_buildings, overlay_path)

        # Save machine-readable manifest
        manifest_path = out_path / "detected_buildings.json"
        manifest_data = {
            "count": len(detected_buildings),
            "buildings": detected_buildings,
            "overlay_path": str(overlay_path),
            "status": "used",
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
                        # Category inference with non-building negative distractors
                        all_cats = BUILDING_CATEGORIES + NON_BUILDING_CATEGORIES
                        cat_prompts = [f"a photograph of {c}" for c in all_cats]
                        inputs_cat = processor(text=cat_prompts, images=c_rgb, return_tensors="pt", padding=True).to(device)
                        with torch.no_grad():
                            logits_cat = model(**inputs_cat).logits_per_image
                            probs_cat = logits_cat.softmax(dim=-1).cpu().numpy()[0]

                        best_cat_idx = int(np.argmax(probs_cat))
                        if best_cat_idx < len(BUILDING_CATEGORIES):
                            bldg["is_building"] = True
                            bldg["classification"] = BUILDING_CATEGORIES[best_cat_idx]
                            bldg["confidence"] = round(float(probs_cat[best_cat_idx]), 3)
                        else:
                            bldg["is_building"] = False
                            bldg["classification"] = all_cats[best_cat_idx]
                            bldg["confidence"] = round(float(probs_cat[best_cat_idx]), 3)
                            logger.info("[building_detector] Crop %s rejected as non-building: %s (conf=%.3f)",
                                        Path(crop_p).name, all_cats[best_cat_idx], probs_cat[best_cat_idx])

                        # Facade style inference
                        style_prompts = [f"architecture featuring {s}" for s in FACADE_STYLES]
                        inputs_style = processor(text=style_prompts, images=c_rgb, return_tensors="pt", padding=True).to(device)
                        with torch.no_grad():
                            logits_style = model(**inputs_style).logits_per_image
                            probs_style = logits_style.softmax(dim=-1).cpu().numpy()[0]

                        best_style_idx = int(np.argmax(probs_style))
                        bldg["facade_style"] = FACADE_STYLES[best_style_idx]

                        # Zero-shot Landmark Perception on the isolated facade crop
                        try:
                            from geolocator.pipeline.landmarks import LANDMARK_DATABASE, NEGATIVE_PROMPTS
                            lm_prompts = [f"a photograph of {lm[0]}" for lm in LANDMARK_DATABASE] + [f"a photograph of {p}" for p in NEGATIVE_PROMPTS[:4]]
                            inputs_lm = processor(text=lm_prompts, images=c_rgb, return_tensors="pt", padding=True).to(device)
                            with torch.no_grad():
                                logits_lm = model(**inputs_lm).logits_per_image
                                probs_lm = logits_lm.softmax(dim=-1).cpu().numpy()[0]

                            top_lm_idx = int(np.argmax(probs_lm))
                            top_lm_prob = float(probs_lm[top_lm_idx])
                            # Check if top match is within landmark database (not negative prompt)
                            if top_lm_idx < len(LANDMARK_DATABASE):
                                neg_probs = probs_lm[len(LANDMARK_DATABASE):]
                                max_neg = float(np.max(neg_probs)) if len(neg_probs) > 0 else 0.0
                                if top_lm_prob >= 0.40 and (top_lm_prob - max_neg) >= 0.15:
                                    matched_entry = LANDMARK_DATABASE[top_lm_idx]
                                    bldg["matched_landmark"] = {
                                        "name": matched_entry[1],
                                        "lat": matched_entry[2],
                                        "lon": matched_entry[3],
                                        "category": matched_entry[4],
                                        "confidence": round(top_lm_prob, 3),
                                        "margin": round(top_lm_prob - max_neg, 3),
                                    }
                                    logger.info("[building_detector] Crop %s matched landmark '%s' (conf=%.3f, margin=%.3f)",
                                                bldg["id"], matched_entry[1], top_lm_prob, top_lm_prob - max_neg)
                        except Exception as e_lm:
                            logger.debug("[building_detector] Crop landmark matching bypass: %s", e_lm)

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

        # 1. First, check if any building was already matched via zero-shot landmark recognition
        for bldg in detected_buildings:
            if bldg.get("matched_landmark"):
                lm = bldg["matched_landmark"]
                best_match = {
                    "name": lm["name"],
                    "osm_id": f"landmark_{lm['name'].replace(' ', '_')}",
                    "osm_type": "landmark",
                    "tags": {"name": lm["name"], "category": lm["category"]},
                    "lat": lm["lat"],
                    "lon": lm["lon"],
                    "match_score": round(lm["confidence"], 2),
                }
                bldg["matched_cadastral"] = best_match
                matched_records.append({
                    "building_id": bldg["id"],
                    "classification": bldg["classification"],
                    "matched": best_match,
                })
                logger.info("[building_detector] Direct crop landmark match accepted for %s: '%s'",
                            bldg["id"], lm["name"])

        # 2. Cross-reference with curated local and global landmark database
        try:
            from geolocator.pipeline.landmarks import LANDMARK_DATABASE
            combined_ocr_tokens = []
            for bldg in detected_buildings:
                ocr_str = bldg.get("ocr_text", "").lower()
                if ocr_str:
                    combined_ocr_tokens.extend([w for w in ocr_str.split() if len(w) >= 4])

            for entry in LANDMARK_DATABASE:
                _, lm_name, lm_lat, lm_lon, lm_cat = entry
                lm_name_lower = lm_name.lower()
                in_bbox = (south <= lm_lat <= north and west <= lm_lon <= east)
                ocr_hit = any(token in lm_name_lower for token in combined_ocr_tokens)
                if in_bbox or ocr_hit:
                    lid = f"landmark_{lm_name.replace(' ', '_')}"
                    tags = {"name": lm_name, "category": lm_cat}
                    if "hotel" in lm_cat:
                        tags["tourism"] = "hotel"
                    elif "club" in lm_cat or "sports" in lm_cat:
                        tags["leisure"] = "club"
                    elif "mosque" in lm_cat or "temple" in lm_cat or "cathedral" in lm_cat:
                        tags["amenity"] = "place_of_worship"
                    elif "university" in lm_cat or "campus" in lm_cat:
                        tags["amenity"] = "university"
                    elif "palace" in lm_cat or "fort" in lm_cat or "unesco" in lm_cat:
                        tags["historic"] = "palace"
                    unique_osm[lid] = {
                        "type": "cadastral_landmark",
                        "id": lid,
                        "lat": lm_lat,
                        "lon": lm_lon,
                        "tags": tags,
                    }
        except Exception as e:
            logger.debug("[building_detector] Landmark database cross-reference bypass: %s", e)

        # 3. Query OSM across architectural and civic categories in bounded area
        # Use a single consolidated Overpass QL query to minimize network round-trips and prevent gateway timeouts
        try:
            ql = f"""[out:json][timeout:20];
(
  node["tourism"~"^(hotel|resort|attraction|museum|guest_house)$"]["name"]({south},{west},{north},{east});
  way["tourism"~"^(hotel|resort|attraction|museum|guest_house)$"]["name"]({south},{west},{north},{east});
  node["amenity"~"^(place_of_worship|university|college|hospital|townhall|courthouse|library|theatre)$"]["name"]({south},{west},{north},{east});
  way["amenity"~"^(place_of_worship|university|college|hospital|townhall|courthouse|library|theatre)$"]["name"]({south},{west},{north},{east});
  node["building"~"^(hotel|commercial|civic|public|mosque|church|cathedral|temple|train_station|stadium|apartments|historic)$"]["name"]({south},{west},{north},{east});
  way["building"~"^(hotel|commercial|civic|public|mosque|church|cathedral|temple|train_station|stadium|apartments|historic)$"]["name"]({south},{west},{north},{east});
  node["historic"~"^(monument|memorial|castle|palace|fort|ruins|building|manor)$"]["name"]({south},{west},{north},{east});
  way["historic"~"^(monument|memorial|castle|palace|fort|ruins|building|manor)$"]["name"]({south},{west},{north},{east});
  node["leisure"~"^(sports_centre|stadium|club)$"]["name"]({south},{west},{north},{east});
  way["leisure"~"^(sports_centre|stadium|club)$"]["name"]({south},{west},{north},{east});
);
out center tags qt;"""
            data = osm.query_ql(ql)
            for el in data.get("elements", []):
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if lat is not None and lon is not None:
                    eid = f"{el.get('type')}_{el.get('id')}"
                    if eid not in unique_osm:
                        unique_osm[eid] = {
                            "id": el.get("id"),
                            "type": el.get("type"),
                            "lat": float(lat),
                            "lon": float(lon),
                            "tags": el.get("tags", {}),
                        }
        except Exception as e:
            logger.debug("[building_detector] OSM consolidated query bypass: %s", e)

        for bldg in detected_buildings:
            if bldg.get("matched_cadastral"):
                continue  # Already matched via direct landmark perception

            b_class = bldg["classification"].lower()
            b_ocr = bldg.get("ocr_text", "").lower()
            b_aspect = float(bldg.get("aspect_ratio", 1.0))
            b_palette = bldg.get("palette", "")
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
                    if "palace" in name_lower or "hall" in name_lower or "market" in name_lower or tags.get("historic"):
                        score += 0.40
                elif "educational" in b_class or "campus" in b_class:
                    if tags.get("amenity") in ("university", "college", "school") or "university" in name_lower or "college" in name_lower or "campus" in name_lower:
                        score += 0.40
                elif "residential" in b_class or "apartment" in b_class or "generic" in b_class:
                    if tags.get("building") in ("apartments", "residential", "hotel", "commercial", "civic_building") or "tower" in name_lower or "court" in name_lower or "hall" in name_lower or "hotel" in name_lower:
                        score += 0.35

                # 3. 3D Geometric Aspect Ratio & Levels consistency cross-check
                levels = tags.get("building:levels")
                height_str = tags.get("height")
                try:
                    num_levels = int(levels) if levels else None
                except Exception:
                    num_levels = None
                try:
                    height_m = float(str(height_str).replace("m", "").strip()) if height_str else None
                except Exception:
                    height_m = None

                if (num_levels and num_levels >= 6) or (height_m and height_m >= 20.0):
                    if b_aspect >= 1.1:
                        score += 0.20  # Vertical tower geometry confirmed
                elif (num_levels and num_levels <= 3) or (height_m and height_m <= 12.0):
                    if b_aspect < 1.0:
                        score += 0.15  # Low-rise sprawling geometry confirmed

                # 4. Color / Palette consistency
                bldg_color = (tags.get("building:colour") or tags.get("roof:colour") or "").lower()
                if bldg_color:
                    if "red" in bldg_color and "red" in b_palette:
                        score += 0.15
                    elif ("beige" in bldg_color or "sand" in bldg_color) and ("beige" in b_palette or "stone" in b_palette):
                        score += 0.15
                    elif ("blue" in bldg_color or "glass" in bldg_color) and "blue" in b_palette:
                        score += 0.15

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
                        "levels": num_levels,
                        "height": height_m,
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

