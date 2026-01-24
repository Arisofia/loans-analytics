"""Helpers for writing run manifests and other output artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


@dataclass
class RunManifest:
    run_id: str
    created_at: datetime
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


def write_manifest(path: Path, manifest: RunManifest) -> Path:
    payload = asdict(manifest)
    # Convert datetime to ISO format
    payload["created_at"] = manifest.created_at.isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
