"""Pydantic models for Cascade responses (v2 scaffold)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CascadeEnvelope(BaseModel):
    data: Any | None = None
    meta: dict[str, Any] | None = None
