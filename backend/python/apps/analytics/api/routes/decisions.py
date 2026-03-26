from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/decisions", tags=["decisions"])

_LAST_RESULT: dict | None = None


@router.get("/current")
async def get_current_decisions():
    if _LAST_RESULT is None:
        return {"status": "no_run_yet"}
    return _LAST_RESULT
