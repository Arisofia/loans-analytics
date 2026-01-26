"""Output writers scaffold.

This is intentionally minimal; real implementation will likely target:
- local filesystem
- Azure Blob Storage
- database sinks
"""

from __future__ import annotations  # noqa: E402

from pathlib import Path  # noqa: E402


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
