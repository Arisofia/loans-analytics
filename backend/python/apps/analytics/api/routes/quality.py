from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/quality", tags=["quality"])

_LAST_QUALITY: dict | None = None


@router.get("/current")
async def get_current_quality():
    if _LAST_QUALITY is None:
        return {"status": "no_run_yet"}
    return _LAST_QUALITY
