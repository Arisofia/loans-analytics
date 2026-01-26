"""Endpoint registry helpers (v2 scaffold)."""

from __future__ import annotations  # noqa: E402

from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str


def load_endpoints(cfg: dict) -> list[Endpoint]:
    endpoints_cfg = cfg.get("endpoints") or {}
    endpoints: list[Endpoint] = []
    for name, path in endpoints_cfg.items():
        endpoints.append(Endpoint(name=str(name), path=str(path)))
    return endpoints
