"""Convert raw JSON payloads into typed DataFrames (v2 scaffold)."""

from __future__ import annotations

from typing import Any


def to_frames(payload: Any) -> dict[str, Any]:
    """Placeholder: convert JSON to DataFrame-like structures.

    Returns a dict of named tables. Uses Any so this scaffold doesn't force
    pandas as an import-time dependency.
    """
    return {"raw": payload}
