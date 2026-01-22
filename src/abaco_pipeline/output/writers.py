"""Output writers scaffold.

This is intentionally minimal; real implementation will likely target:
- local filesystem
- Azure Blob Storage
- database sinks
"""

from __future__ import annotations

from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
