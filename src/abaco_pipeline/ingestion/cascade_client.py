"""Cascade API client (v2 scaffold).

Expected capabilities:
- httpx-based requests
- retry/backoff
- auth token handling

This module is a placeholder for the full implementation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CascadeClient:
    base_url: str
    token: str | None

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ValueError("base_url is required")

    def get(self, path: str) -> dict:
        raise NotImplementedError("CascadeClient.get() is not implemented in the scaffold")
