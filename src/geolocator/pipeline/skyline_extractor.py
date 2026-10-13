"""Skyline Extractor: Extracts mountain/terrain horizon contours from photos."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger("geolocator.pipeline.skyline_extractor")


class SkylineExtractor:
    """Extracts 1D ridgeline / horizon elevation profile from photographs."""

    def __init__(self, target_width: int = 256):
        self.target_width = target_width

    def extract_from_image(
        self,
        image_input: Image.Image | str | Path,
        save_overlay_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Extract normalized skyline profile [y(x) in range 0..1] from image."""
        if isinstance(image_input, (str, Path)):
            im = Image.open(str(image_input)).convert("RGB")
        else:
            im = image_input.convert("RGB")

        orig_w, orig_h = im.size
        # Resize for fast, robust contour analysis
        w = self.target_width
        h = max(128, int(orig_h * (w / orig_w)))
        im_resized = im.resize((w, h), Image.Resampling.BILINEAR)

        rgb = np.asarray(im_resized, dtype=np.float32)
        gray = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

        # Detect sky vs terrain boundary per column
        # Sky is usually in the top half to two-thirds and brighter/smoother
        # Vertical gradient: dI/dy (from top to bottom)
        grad_y = np.diff(gray, axis=0)  # shape (h-1, w)

        horizon_rows = np.zeros(w, dtype=np.int32)
        search_min_row = int(h * 0.05)
        search_max_row = int(h * 0.85)

        for col in range(w):
            col_grad = np.abs(grad_y[search_min_row:search_max_row, col])
            # Combine edge magnitude with brightness difference
            col_gray = gray[search_min_row:search_max_row, col]
            
            # Contrast score: sky above is brighter than terrain below
            diff_score = np.zeros_like(col_grad)
            window = 10
            for r in range(window, len(col_gray) - window):
                mean_above = np.mean(col_gray[max(0, r - window):r])
                mean_below = np.mean(col_gray[r:min(len(col_gray), r + window)])
                diff_score[r] = max(0.0, mean_above - mean_below)

            combined_strength = col_grad * 0.4 + diff_score * 0.6
            if np.max(combined_strength) > 0:
                best_idx = int(np.argmax(combined_strength))
            else:
                best_idx = len(combined_strength) // 2

            horizon_rows[col] = search_min_row + best_idx

        # Smooth the extracted ridge contour using a 1D median & moving average filter
        kernel_size = 7
        smoothed = np.copy(horizon_rows).astype(np.float32)
        for i in range(w):
            start = max(0, i - kernel_size // 2)
            end = min(w, i + kernel_size // 2 + 1)
            smoothed[i] = np.median(horizon_rows[start:end])

        # Moving average
        window = 5
        final_ridge = np.convolve(smoothed, np.ones(window) / window, mode="same")

        # Inverted normalized elevation profile: higher in the image -> higher elevation angle
        # Normalized to [0.0, 1.0] where 1.0 is peak altitude and 0.0 is base
        ridge_inverted = (h - final_ridge) / float(h)
        # Normalize curve so mean is 0, std is 1 for cross-correlation matching
        std_val = float(np.std(ridge_inverted))
        contrast_val = float(np.max(ridge_inverted) - np.min(ridge_inverted)) if len(ridge_inverted) > 0 else 0.0
        is_non_flat = bool(std_val >= 0.02 and contrast_val >= 0.07)
        norm_curve = (ridge_inverted - np.mean(ridge_inverted)) / (std_val if std_val > 1e-4 else 1.0)

        # Sample color below contour for terracotta / red roof tiles & brick architecture
        red_count = 0
        total_samples = 0
        for col in range(w):
            r_idx = int(horizon_rows[col])
            sample_row = min(h - 1, r_idx + 5)
            if sample_row < h:
                pixel = rgb[sample_row, col]
                r_c, g_c, b_c = float(pixel[0]), float(pixel[1]), float(pixel[2])
                mean_gb = (g_c + b_c) / 2.0
                if r_c > 1.25 * mean_gb and r_c > 75.0:
                    red_count += 1
                total_samples += 1

        red_roof_fraction = float(red_count / max(1, total_samples))
        is_manmade_roofline = bool(red_roof_fraction >= 0.20)
        roofline_reason = (
            f"Prominent red roof tile / terracotta architectural roofline ({red_roof_fraction:.1%}) detected below contour"
            if is_manmade_roofline
            else ""
        )
        if is_manmade_roofline:
            is_non_flat = False

        # Generate visual overlay if requested
        overlay_saved = False
        if save_overlay_path is not None:
            save_overlay_path = Path(save_overlay_path)
            save_overlay_path.parent.mkdir(parents=True, exist_ok=True)
            overlay_im = im_resized.copy()
            draw = ImageDraw.Draw(overlay_im)
            pts = [(col, int(final_ridge[col])) for col in range(w)]
            for i in range(len(pts) - 1):
                # Glowing HUD style line (dark outline + bright neon red center)
                draw.line([pts[i], pts[i + 1]], fill=(0, 0, 0), width=4)
                draw.line([pts[i], pts[i + 1]], fill=(255, 40, 40), width=2)
            overlay_im.save(save_overlay_path)
            overlay_saved = True

        return {
            "samples": w,
            "horizon_rows": [int(r) for r in final_ridge],
            "normalized_profile": [round(float(v), 4) for v in norm_curve],
            "raw_elevations": [round(float(v), 4) for v in ridge_inverted],
            "std_elevation": round(std_val, 4),
            "contrast": round(contrast_val, 4),
            "is_non_flat": is_non_flat,
            "is_manmade_roofline": is_manmade_roofline,
            "roofline_reason": roofline_reason,
            "red_roof_fraction": round(red_roof_fraction, 4),
            "overlay_saved": overlay_saved,
            "overlay_path": str(save_overlay_path) if overlay_saved else None,
        }
