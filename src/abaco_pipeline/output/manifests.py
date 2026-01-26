"""Helpers for writing run manifests and other output artifacts."""

from __future__ import annotations  # noqa: E402

import json  # noqa: E402
from dataclasses import asdict, dataclass  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Dict  # noqa: E402


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
