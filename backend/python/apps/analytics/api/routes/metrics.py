from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

_LAST_METRICS: dict | None = None


@router.get("/executive")
async def get_executive_metrics():
    if _LAST_METRICS is None:
        return {"status": "no_run_yet"}
    return _LAST_METRICS
