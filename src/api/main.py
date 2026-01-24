import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Rely on PYTHONPATH or test runner configuration for local imports. If you need to run this module directly,
# set PYTHONPATH or run from project root. Avoid modifying sys.path at module import time.
from src.config.paths import Paths
from src.config.settings import settings

try:
    from apps.analytics.risk_model import LoanRiskModel
except ImportError:
    LoanRiskModel = None

try:
    from agents.gen_ai_kpi import KPIQuestionAnsweringAgent
except ImportError:
    KPIQuestionAnsweringAgent = None

logger = logging.getLogger(__name__)

app = FastAPI(title="Abaco Analytics API v2.0")

# Redis-based Rate Limiting (Sliding Window)
try:
    r = redis.from_url(settings.redis_url)
except Exception:
    r = None

# Global Model Instances (Lazy loaded)
_risk_model = None
_kpi_agent = None


class RiskRequest(BaseModel):
    amount: float = 0.0
    interest_rate: float = 0.0
    term_months: int = 12
    dpd_0_7_usd: float = 0.0
    dpd_30_60_usd: float = 0.0


class QueryRequest(BaseModel):
    query: str


def is_rate_limited(client_ip: str, limit: int = 100, window: int = 60) -> bool:
    if not r:
        return False

    now = time.time()
    key = f"rate_limit:{client_ip}"

    # Remove old requests from window
    r.zremrangebyscore(key, 0, now - window)

    # Count requests in window
    count = r.zcard(key)

    if count >= limit:
        return True

    # Add current request
    r.zadd(key, {str(now): now})
    r.expire(key, window)
    return False


def _sanitize_and_resolve(path: str, base_dir: Path) -> Path:
    """
    Sanitize and resolve a path to prevent directory traversal.
    """
    # Ensure path is not absolute
    p = Path(path)
    if p.is_absolute():
        raise ValueError(f"Absolute paths not allowed: {path}")

    # Resolve full path
    resolved_base = base_dir.resolve()
    full_path = (resolved_base / p).resolve()

    # Check if it's still inside base_dir
    if not str(full_path).startswith(str(resolved_base)):
        raise ValueError(f"Path traversal detected: {path}")

    return full_path


def get_latest_metrics_file() -> Optional[Path]:
    metrics_dir = Paths.metrics_dir()
    if not metrics_dir.exists():
        return None
    files = list(metrics_dir.glob("*_metrics.json"))
    if not files:
        return None
    # Sort by modification time
    return sorted(files, key=lambda p: p.stat().st_mtime)[-1]


def get_risk_model():
    global _risk_model
    if _risk_model is None and LoanRiskModel:
        _risk_model = LoanRiskModel("models/loan_risk_model.pkl")
        try:
            _risk_model.load()
        except Exception:
            logger.warning("Could not load risk model. Predictions will fail if not trained.")
    return _risk_model


def get_kpi_agent():
    global _kpi_agent
    if _kpi_agent is None and KPIQuestionAnsweringAgent:
        _kpi_agent = KPIQuestionAnsweringAgent()
    return _kpi_agent


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        return JSONResponse(status_code=429, content={"error": "Too Many Requests"})
    return await call_next(request)


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0"}


@app.get("/metrics/summary")
def get_metrics_summary():
    # Placeholder for actual metrics retrieval from Polars/DB
    return {"aum": 15200000.0, "npl": 0.035, "rotation": 4.6}


@app.get("/kpis/latest")
def get_latest_kpis():
    metrics_file = get_latest_metrics_file()
    if not metrics_file:
        raise HTTPException(status_code=404, detail="No KPI metrics found.")
    try:
        data = json.loads(metrics_file.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/risk")
def predict_risk(request: RiskRequest):
    model = get_risk_model()
    if not model:
        raise HTTPException(status_code=503, detail="Risk model not available.")

    if not model.model:
        raise HTTPException(status_code=503, detail="Risk model not trained.")

    df = pd.DataFrame([request.model_dump()])
    try:
        result_df = model.predict(df)
        return {
            "default_probability": float(result_df["default_probability"].iloc[0]),
            "risk_score": int(result_df["risk_score"].iloc[0]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
def ask_kpi_agent(request: QueryRequest):
    agent = get_kpi_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Gen AI Agent not available.")

    # Get context from latest metrics
    metrics_file = get_latest_metrics_file()
    if not metrics_file:
        # Fallback to dummy context
        context = {"info": "No recent KPI data available."}
    else:
        try:
            raw_metrics = json.loads(metrics_file.read_text())
            # Flatten context
            context = {}
            for k, v in raw_metrics.items():
                if isinstance(v, dict) and "value" in v:
                    context[k] = v["value"]
                else:
                    context[k] = v
        except Exception:
            context = {"error": "Failed to load metrics."}

    answer = agent.answer_query(request.query, context)
    return {"query": request.query, "answer": answer}


if __name__ == "__main__":
    # Helpful when running this file directly for local dev (not for production).
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))
    print("Run this application with a proper ASGI server, e.g., 'uvicorn src.api.main:app'")
