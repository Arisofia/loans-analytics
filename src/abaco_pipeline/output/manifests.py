"""Manifest model + writer helpers (v2 scaffold)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    created_at: datetime
    inputs: dict[str, str]
    outputs: dict[str, str]


def write_manifest(path: str | Path, manifest: RunManifest) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(manifest)
    payload["created_at"] = manifest.created_at.isoformat()
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p
