"""Optional Online Co-Pilot for Global Photo Geolocation.

Supports free-tier Google AI Studio Gemini API (Gemini 2.5 Flash / 1.5 Flash).
When an API key is configured or provided per-run, this provider performs
cloud-scale multimodal forensic analysis to locate the photo anywhere in the world.
When no API key is provided, this module is completely bypassed, ensuring 100%
local, offline operation without errors.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image

from geolocator.pipeline.board import CandidateBoard

logger = logging.getLogger("geolocator.online_copilot")


class OnlineCoPilotProvider:
    """Optional online intelligence co-pilot using free-tier API services."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def is_enabled(self, runtime_key: Optional[str] = None) -> bool:
        """Check if an API key is available in environment, config, or runtime."""
        key = runtime_key or self.api_key or os.getenv("GEMINI_API_KEY")
        return bool(key and key.strip())

    def _prepare_image_base64(self, image_path: Path, max_dim: int = 1024) -> Tuple[str, str]:
        """Load and resize image if necessary, returning (base64_str, mime_type)."""
        image_path = Path(image_path)
        with Image.open(image_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                new_w, new_h = int(w * scale), int(h * scale)
                im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

            import io
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=85)
            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
            return b64_str, "image/jpeg"

    def analyze_photo(
        self,
        image_path: Path,
        user_hint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Query Gemini multimodal API to predict location, coordinates, and forensic clues."""
        key = api_key or self.api_key or os.getenv("GEMINI_API_KEY")
        if not key or not key.strip():
            logger.debug("[online_copilot] No API key configured. Skipping online co-pilot.")
            return None

        b64_data, mime_type = self._prepare_image_base64(image_path)

        prompt = (
            "You are an elite Open-Source Intelligence (OSINT) and photo geolocation expert.\n"
            "Carefully examine this photograph to determine where on Earth it was taken.\n"
            "Analyze all visible features:\n"
            "- Architecture, construction styles, masonry, roofing, windows\n"
            "- Vegetation, endemic tree/plant species, biome, climate, soil\n"
            "- Topography, mountain ridges, horizon curvature, bodies of water\n"
            "- Road infrastructure, lane markings, signage, utility poles, bollards\n"
            "- Languages, scripts, brand logos, vehicle registration plates\n\n"
        )
        if user_hint and user_hint.strip():
            prompt += f"USER CONTEXT HINT: \"{user_hint.strip()}\"\nRespect this context if consistent with visual features.\n\n"

        prompt += (
            "Output your findings as strict JSON with this exact structure:\n"
            "{\n"
            '  "location_name": "<Specific place name, landmark, mountain, village, or street>",\n'
            '  "country": "<Country name>",\n'
            '  "state_or_province": "<Subnational state, province, or region>",\n'
            '  "city_or_district": "<City, district, or valley>",\n'
            '  "latitude": <approximate or exact latitude as float>,\n'
            '  "longitude": <approximate or exact longitude as float>,\n'
            '  "confidence_tier": "<T1 (<100m) | T2 (<5km) | T3 (<25km) | T4 (<150km)>",\n'
            '  "error_radius_km": <estimated error radius in km as float>,\n'
            '  "supporting_clues": ["<visual clue 1>", "<visual clue 2>", "<visual clue 3>"],\n'
            '  "uncertain_factors": ["<confounding factor if any>"],\n'
            '  "forensic_rationale": "<Concise explanation of identifying clues>"\n'
            "}\n"
            "Return valid JSON only. Do not wrap in markdown or backticks."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        # Try gemini-2.5-flash first, then fallback to gemini-1.5-flash
        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        headers = {"Content-Type": "application/json"}

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key.strip()}"
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                raw_text = parts[0]["text"].strip()
                                # Clean markdown wrapper if present
                                if raw_text.startswith("```"):
                                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                                    raw_text = re.sub(r"\s*```$", "", raw_text)
                                parsed = json.loads(raw_text)
                                logger.info(
                                    "[online_copilot] Successfully geolocated via %s: %s (%s, %s)",
                                    model_name,
                                    parsed.get("location_name"),
                                    parsed.get("latitude"),
                                    parsed.get("longitude"),
                                )
                                parsed["provider"] = "google_gemini"
                                parsed["model"] = model_name
                                return parsed
                    elif resp.status_code == 404:
                        logger.debug("[online_copilot] Model %s not found on endpoint, trying next...", model_name)
                        continue
                    else:
                        logger.warning(
                            "[online_copilot] API request returned status %d: %s",
                            resp.status_code,
                            resp.text[:200],
                        )
                        # If unauthorized or invalid key, don't keep trying
                        if resp.status_code in (400, 401, 403):
                            break
            except Exception as e:
                logger.warning("[online_copilot] Request error with %s: %s", model_name, e)

        return None

    def process(
        self,
        job_dir: Path,
        board: CandidateBoard,
        working_image_path: Path,
        user_hint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Run online co-pilot analysis and integrate verified candidates into board."""
        if not self.is_enabled(api_key):
            return None

        job_dir = Path(job_dir)
        job_dir.mkdir(parents=True, exist_ok=True)
        analysis = self.analyze_photo(working_image_path, user_hint=user_hint, api_key=api_key)
        if not analysis:
            return None

        # Write analysis artifact
        artifact_path = job_dir / "online_copilot_results.json"
        artifact_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

        lat = analysis.get("latitude")
        lon = analysis.get("longitude")
        loc_name = analysis.get("location_name") or "Identified Landmark"
        country = analysis.get("country")
        province = analysis.get("state_or_province")
        radius_km = float(analysis.get("error_radius_km") or 5.0)
        tier = analysis.get("confidence_tier") or "T2"

        if lat is not None and lon is not None:
            cand_name = f"Online Vision: {loc_name}"
            # Add point candidate with calibrated prior
            board.add_candidate(
                name=cand_name,
                level="point",
                lat=float(lat),
                lon=float(lon),
                prior=12.0,
                metadata={
                    "online_copilot": True,
                    "provider": analysis.get("provider", "gemini"),
                    "model": analysis.get("model", "gemini-2.5-flash"),
                    "country": country,
                    "subnational_division": province,
                    "radius_km": radius_km,
                    "tier": tier,
                    "rationale": analysis.get("forensic_rationale", ""),
                },
            )

            # Also seed country and province if given
            if country:
                board.add_candidate(name=country, level="country", prior=8.0)
            if province and country:
                board.add_candidate(name=f"{province}, {country}", level="area", prior=6.0)

            # Add evidence clue to the board
            clue_text = (
                f"Multimodal vision OSINT identification: {loc_name} "
                f"({country or ''}) [Coordinates: {lat:.4f}, {lon:.4f}]"
            )
            cid = board.add_clue(
                text=clue_text,
                kind="online_vision_copilot",
                status="observed",
                source="gemini_api",
                confidence=0.98,
            )

            board.add_evidence(
                clue_id=cid,
                candidate_weights={cand_name: 25.0},
                rationale=analysis.get("forensic_rationale") or f"Cloud multimodal recognition identified {loc_name}",
                artifact_path=str(artifact_path),
            )

            # Attach supporting clues to clues.json if present
            clues_file = job_dir / "clues.json"
            if clues_file.exists():
                try:
                    c_data = json.loads(clues_file.read_text(encoding="utf-8"))
                    sup = c_data.setdefault("supporting_clues", [])
                    for sc in analysis.get("supporting_clues", []):
                        if sc not in sup:
                            sup.append(f"[Online Vision] {sc}")
                    if analysis.get("forensic_rationale") and not c_data.get("interpretation"):
                        c_data["interpretation"] = analysis["forensic_rationale"]
                    clues_file.write_text(json.dumps(c_data, indent=2), encoding="utf-8")
                except Exception:
                    pass

            board.data.setdefault("stages_run", []).append("online_copilot")
            board.save()
            logger.info("[online_copilot] Successfully seeded high-confidence candidate '%s' onto board", cand_name)

        return analysis
