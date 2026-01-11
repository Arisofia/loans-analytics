"""Raw artifact archiving (v2 scaffold)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


@dataclass(frozen=True)
class ArchiveResult:
    path: Path
    sha256: str


def write_raw_json(archive_dir: Path, name: str, obj: Any) -> ArchiveResult:
    archive_dir.mkdir(parents=True, exist_ok=True)
    sha = sha256_json(obj)
    out = archive_dir / f"{name}.{sha}.json"
    out.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    return ArchiveResult(path=out, sha256=sha)


def archive_file(archive_dir: Path, src: Path) -> ArchiveResult:
    """Copy a source file into the archive dir with a content hash in the filename."""

    archive_dir.mkdir(parents=True, exist_ok=True)
    payload = src.read_bytes()
    sha = sha256_bytes(payload)
    out = archive_dir / f"{src.stem}.{sha}{src.suffix}"
    out.write_bytes(payload)
    return ArchiveResult(path=out, sha256=sha)
