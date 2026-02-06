import logging
import re
from pathlib import Path
from typing import Optional, List

# Avoid importing FastAPI at module import time so tests don't require
# fastapi installed. Use a lazy import and a lightweight HTTPException
# fallback for environments without FastAPI.
try:
    from fastapi import FastAPI, HTTPException, Depends, Body
    from python.apps.analytics.api.models import (
        KpiResponse, 
        KpiSingleResponse, 
        LoanPortfolioRequest,
        RiskAlertsResponse,
        RiskLoan,
        ErrorResponse,
        ValidationErrorResponse
    )
    from python.apps.analytics.api.service import KPIService

    app: Optional[FastAPI] = FastAPI(title="Abaco Loans Analytics API")
except ImportError:  # pragma: no cover - fallback in tests/environments without FastAPI
    class HTTPException(Exception):  # type: ignore[no-redef]
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Depends:
        def __init__(self, *args, **kwargs): pass

    class Body:
        def __init__(self, *args, **kwargs): pass

    app = None

logger = logging.getLogger("apps.analytics.api")
# Directory that contains allowed data files (must be absolute)
ALLOWED_DATA_DIR = Path("/data/archives").resolve()

def get_kpi_service():
    # In a real scenario, we'd extract the user/actor from the auth token
    return KPIService(actor="api_user")

@app.get("/health") if app else lambda f: f
async def health_check():
    return {"status": "ok"}

@app.post("/analytics/kpis", response_model=KpiResponse) if app else lambda f: f
async def calculate_all_kpis(
    request: LoanPortfolioRequest = Body(...),
    service: KPIService = Depends(get_kpi_service)
):
    """
    Get all portfolio KPIs.
    For now, returns the latest pre-calculated KPIs from Supabase.
    """
    try:
        kpis = await service.get_latest_kpis()
        return KpiResponse(kpis=kpis)
    except Exception as e:
        logger.error(f"Error in calculate_all_kpis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/analytics/kpis/{kpi_id}", response_model=KpiSingleResponse) if app else lambda f: f
async def get_single_kpi(
    kpi_id: str,
    request: LoanPortfolioRequest = Body(...),
    service: KPIService = Depends(get_kpi_service)
):
    """
    Get a specific KPI by ID (par30, par90, etc.)
    """
    # Map path-style IDs to DB keys if necessary
    kpi_key_map = {
        "par30": "PAR30",
        "par90": "PAR90",
        "collection-rate": "COLLECTION_RATE",
        "portfolio-health": "PORTFOLIO_HEALTH",
        "ltv": "LTV",
        "dti": "DTI",
        "portfolio-yield": "PORTFOLIO_YIELD"
    }
    
    db_key = kpi_key_map.get(kpi_id.lower(), kpi_id.upper())
    
    try:
        kpi = await service.get_kpi_by_id(db_key)
        if not kpi:
            raise HTTPException(status_code=404, detail=f"KPI {kpi_id} not found")
        return kpi
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_single_kpi: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/analytics/risk-alerts", response_model=RiskAlertsResponse) if app else lambda f: f
async def get_risk_alerts(
    ltv_threshold: float = Body(80.0, embed=True),
    dti_threshold: float = Body(50.0, embed=True),
    service: KPIService = Depends(get_kpi_service)
):
    """
    Identifies high-risk loans based on LTV and DTI thresholds.
    """
    try:
        risk_loans_data = await service.get_risk_alerts(ltv_threshold, dti_threshold)
        risk_loans = [RiskLoan(**loan) for loan in risk_loans_data]
        
        # Determine overall risk level
        risk_level = "low"
        if any(loan.risk_score > 70 for loan in risk_loans):
            risk_level = "high"
        elif any(loan.risk_score > 40 for loan in risk_loans):
            risk_level = "medium"
            
        return RiskAlertsResponse(
            risk_level=risk_level,
            high_risk_loans=risk_loans
        )
    except Exception as e:
        logger.error(f"Error in get_risk_alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Legacy endpoint preserved for backward compatibility
@app.get("/data/{file_path:path}") if app else lambda f: f
def get_data(file_path: str):
    """Return file contents for a path under ALLOWED_DATA_DIR after sanitization."""
    if not file_path or not file_path.strip():
        raise HTTPException(status_code=400, detail="file path cannot be empty")

    try:
        resolved = _sanitize_and_resolve(file_path, ALLOWED_DATA_DIR)
    except ValueError as exc:
        safe_path = _sanitize_for_logging(file_path)
        logger.warning("Invalid data path requested: %s (%s)", safe_path, str(exc))
        raise HTTPException(status_code=400, detail="Invalid path format") from exc

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    
    return {"status": "ok", "path": str(resolved)}

def _sanitize_for_logging(value: str, max_length: int = 200) -> str:
    if not value: return ""
    sanitized = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\x00", "").replace("\x1b", "")
    sanitized = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", sanitized)
    return sanitized[:max_length] + "...[truncated]" if len(sanitized) > max_length else sanitized

def _sanitize_and_resolve(candidate: str, allowed_dir: Path) -> Path:
    if not candidate: raise ValueError("empty path")
    candidate_path = Path(candidate)
    if candidate_path.is_absolute(): raise ValueError("absolute paths are not allowed")
    if any(p == ".." for p in candidate_path.parts): raise ValueError("parent traversal is not allowed")
    if not re.match(r"^[a-zA-Z0-9_./\-]+$", str(candidate_path)): raise ValueError("invalid characters")
    resolved = (allowed_dir / candidate_path).resolve()
    try:
        resolved.relative_to(allowed_dir)
    except ValueError as exc:
        raise ValueError("path outside allowed directory") from exc
    return resolved
