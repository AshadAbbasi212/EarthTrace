"""Precompute CLIP text embeddings for the multi-city landmark database.
Runs offline once, saving normalized tensor embeddings to data/landmarks/landmarks_embeddings.pt
and prompt index metadata to data/landmarks/landmarks_index.json.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import torch
from transformers import CLIPModel, CLIPProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("precompute_embeddings")

DATA_DIR = Path("data/landmarks")
ALL_LANDMARKS_FILE = DATA_DIR / "all_landmarks.json"
OUT_EMBEDDINGS_FILE = DATA_DIR / "landmarks_embeddings.pt"
OUT_INDEX_FILE = DATA_DIR / "landmarks_index.json"

NEGATIVE_PROMPTS = [
    "ordinary city street without famous landmarks",
    "generic highway road asphalt trees",
    "typical residential houses and suburb",
    "unremarkable office buildings street corner",
    "regular farmland agricultural fields dirt road",
    "empty countryside rural green pasture",
    "generic shopping market vegetables fruit vendors",
    "crowded public bus stop asphalt road",
    "modern commercial storefronts glass windows generic",
    "regular hospital emergency driveway cars parked",
    "ordinary apartment building balcony windows",
    "flat arid desert plain without mountains",
    "pine forest nature path without structures",
    "water reservoir dam lake with no buildings",
    "general university parking lot cars trees",
]

def precompute():
    if not ALL_LANDMARKS_FILE.exists():
        raise FileNotFoundError(f"{ALL_LANDMARKS_FILE} not found. Run build_comprehensive_landmarks.py first.")

    records = json.loads(ALL_LANDMARKS_FILE.read_text(encoding="utf-8"))
    logger.info("Loaded %d landmark records from %s", len(records), ALL_LANDMARKS_FILE)

    prompts = []
    metadata = []

    # 1. Collect all prompts for landmarks
    for rec in records:
        rec_prompts = rec.get("prompts", [])
        if not rec_prompts:
            rec_prompts = [f"{rec['name']}, {rec.get('city', '')}, {rec.get('country', '')}"]
        for p in rec_prompts:
            prompts.append(p)
            metadata.append({
                "type": "landmark",
                "name": rec["name"],
                "city": rec.get("city", ""),
                "country": rec.get("country", ""),
                "category": rec.get("category", "landmark"),
                "latitude": rec["lat"],
                "longitude": rec["lon"],
                "radius_km": rec.get("radius_km", 0.05),
                "prompt": p,
            })

    num_landmarks_prompts = len(prompts)
    logger.info("Collected %d landmark prompts across %d landmarks.", num_landmarks_prompts, len(records))

    # 2. Append negative background prompts
    for neg_p in NEGATIVE_PROMPTS:
        prompts.append(neg_p)
        metadata.append({
            "type": "negative",
            "name": "Negative Background",
            "city": "",
            "country": "",
            "category": "negative_background",
            "latitude": 0.0,
            "longitude": 0.0,
            "radius_km": 0.0,
            "prompt": neg_p,
        })

    logger.info("Total prompts to encode (landmarks + negatives): %d", len(prompts))

    # 3. Load CLIP text encoder
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading CLIP model on device: %s", device)
    model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
    model.eval()

    # 4. Encode in safe batches of 32 to guarantee zero TDR timeouts
    batch_size = 32
    all_feats = []
    with torch.no_grad():
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i + batch_size]
            tokens = processor(text=batch_prompts, padding=True, truncation=True, return_tensors="pt").to(device)
            out = model.get_text_features(**tokens)
            pool = out.pooler_output if hasattr(out, "pooler_output") else out
            norm_feats = torch.nn.functional.normalize(pool, dim=1).cpu()
            all_feats.append(norm_feats)
            if (i // batch_size) % 5 == 0 or (i + batch_size) >= len(prompts):
                logger.info("Encoded batch %d/%d (prompts %d-%d)",
                            i // batch_size + 1, (len(prompts) + batch_size - 1) // batch_size,
                            i, min(i + batch_size, len(prompts)))

    embeddings = torch.cat(all_feats, dim=0)
    logger.info("Finished encoding. Embeddings shape: %s (float32)", embeddings.shape)

    # 5. Save embeddings tensor and metadata index
    torch.save(embeddings, OUT_EMBEDDINGS_FILE)
    logger.info("Saved embeddings tensor to %s (%d bytes)", OUT_EMBEDDINGS_FILE, OUT_EMBEDDINGS_FILE.stat().st_size)

    index_data = {
        "model": "openai/clip-vit-large-patch14",
        "num_prompts": len(prompts),
        "num_landmarks_prompts": num_landmarks_prompts,
        "num_negatives": len(NEGATIVE_PROMPTS),
        "metadata": metadata,
    }
    OUT_INDEX_FILE.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved metadata index to %s", OUT_INDEX_FILE)
    print("\nPrecomputation complete! Vector store ready for ultra-fast local search.")

if __name__ == "__main__":
    precompute()
