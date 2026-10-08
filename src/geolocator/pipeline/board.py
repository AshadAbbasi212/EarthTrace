"""Candidate Board: Manages candidates, clues, evidence likelihood ratios, and strict exclusions."""
from __future__ import annotations

import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("geolocator.pipeline.board")

LEVELS = ["country", "region", "admin1", "admin2", "city", "district", "area", "cell", "road", "point"]
STATUSES = ["observed", "read", "inferred", "computed"]

# Likelihood ratio bounds per status type
LR_CAPS = {
    "inferred": 3.0,
    "observed": 5.0,
    "read": 50.0,
    "computed": 50.0,
}


class CandidateBoard:
    """Per-job candidate board tracking hypotheses, clues, and evidentiary scores."""

    def __init__(self, photo_path: str | Path, board_path: Optional[str | Path] = None):
        self.photo_path = str(photo_path)
        self.board_path = Path(board_path) if board_path else None
        self.data: Dict[str, Any] = {
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "photo": self.photo_path,
            "fast_path_gps": None,
            "candidates": {},
            "clues": {},
            "evidence": [],
            "exclusions": [],
            "stages_run": [],
        }

    def save(self, path: Optional[str | Path] = None) -> Path:
        """Persist candidate board to disk as JSON."""
        target = Path(path) if path else self.board_path
        if not target:
            raise ValueError("No target path specified to save candidate board")
        target.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated"] = datetime.now().isoformat()
        target.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "CandidateBoard":
        """Load candidate board from JSON file."""
        target = Path(path)
        data = json.loads(target.read_text(encoding="utf-8"))
        board = cls(photo_path=data.get("photo", ""), board_path=target)
        board.data = data
        return board

    def add_candidate(
        self,
        name: str,
        level: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        bbox: Optional[List[float]] = None,
        parent: Optional[str] = None,
        prior: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add or update a candidate location/region on the board."""
        if level not in LEVELS:
            raise ValueError(f"Invalid level '{level}'. Must be one of {LEVELS}")

        candidate = {
            "name": name,
            "level": level,
            "lat": lat,
            "lon": lon,
            "bbox": bbox,
            "parent": parent,
            "score": float(prior),
            "log_score": math.log(max(0.001, prior)),
            "excluded": False,
            "metadata": metadata or {},
        }
        self.data["candidates"][name] = candidate
        return candidate

    def add_clue(
        self,
        text: str,
        kind: str,
        status: str,
        file_ref: Optional[str] = None,
        source: str = "pipeline",
        confidence: float = 1.0,
    ) -> str:
        """Record an observed, read, inferred, or computed clue."""
        if status not in STATUSES:
            raise ValueError(f"Invalid clue status '{status}'. Must be one of {STATUSES}")

        clue_id = f"K{len(self.data['clues']) + 1}"
        clue = {
            "id": clue_id,
            "text": text,
            "kind": kind,
            "status": status,
            "source": source,
            "confidence": confidence,
            "file_ref": file_ref,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["clues"][clue_id] = clue
        return clue_id

    def add_evidence(
        self,
        clue_id: str,
        candidate_weights: Dict[str, float],
        rationale: str,
        artifact_path: Optional[str] = None,
    ) -> None:
        """Apply a clue's likelihood ratio to candidates.
        
        Likelihood ratios > 1.0 support, < 1.0 oppose.
        Values are clamped strictly according to the clue's status type.
        """
        clue = self.data["clues"].get(clue_id)
        if not clue:
            raise ValueError(f"Clue '{clue_id}' does not exist on board")

        status = clue["status"]
        max_lr = LR_CAPS.get(status, 3.0)
        min_lr = 1.0 / max_lr

        clamped_weights = {}
        for cand_name, weight in candidate_weights.items():
            if cand_name in self.data["candidates"]:
                clamped = max(min_lr, min(max_lr, float(weight)))
                clamped_weights[cand_name] = clamped
                cand = self.data["candidates"][cand_name]
                cand["score"] *= clamped
                cand["log_score"] += math.log(clamped)

        record = {
            "clue_id": clue_id,
            "status": status,
            "weights": clamped_weights,
            "rationale": rationale,
            "artifact_path": artifact_path,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["evidence"].append(record)

    def exclude_candidate(
        self,
        candidate_name: str,
        clue_id: str,
        computed_artifact: str,
        rationale: str,
    ) -> bool:
        """Exclude a candidate.
        
        Strict rule: Exclusions REQUIRE a computed artifact file and a read/computed clue.
        Inferences cannot exclude.
        """
        clue = self.data["clues"].get(clue_id)
        if not clue or clue["status"] not in ("read", "computed"):
            logger.warning("Exclusion rejected: clue '%s' is not read or computed", clue_id)
            return False

        if not Path(computed_artifact).exists() and not computed_artifact.startswith("artifact:"):
            logger.warning("Exclusion rejected: artifact '%s' does not exist", computed_artifact)
            return False

        if candidate_name in self.data["candidates"]:
            cand = self.data["candidates"][candidate_name]
            cand["excluded"] = True
            cand["exclusion_reason"] = rationale
            self.data["exclusions"].append({
                "candidate": candidate_name,
                "clue_id": clue_id,
                "artifact": computed_artifact,
                "rationale": rationale,
                "timestamp": datetime.now().isoformat(),
            })
            return True
        return False

    def rank(self) -> List[Dict[str, Any]]:
        """Return non-excluded candidates ranked by log score."""
        active = [c for c in self.data["candidates"].values() if not c.get("excluded", False)]
        return sorted(active, key=lambda c: c.get("log_score", -999.0), reverse=True)

    def mark_stage_run(self, stage_name: str) -> None:
        """Log pipeline stage execution."""
        if stage_name not in self.data["stages_run"]:
            self.data["stages_run"].append(stage_name)
