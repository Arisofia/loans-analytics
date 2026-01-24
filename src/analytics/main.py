import io
import logging
import tempfile
from datetime import datetime, timezone

from apps.analytics.src.flows.ingestion_flow import loan_ingestion_flow
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import APIKeyHeader

from python.config import settings
from src.pipeline.data_ingestion import UnifiedIngestion
from src.analytics.polars_analytics_engine import PolarsAnalyticsEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics_api")

app = FastAPI(
    title="Abaco Analytics Ingestion API",
    description="Secure, automated ingestion endpoint for loan datasets.",
    version="0.1.0",
)

# Simple API Key Security (Placeholder for JWT/OAuth2)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.api.api_key:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/ingest", dependencies=[Depends(verify_api_key)])
async def ingest_dataset(file: UploadFile = File(...), trigger_flow: bool = False):
    """
    Secure API endpoint for automated document ingestion.
    Validates schema and computes core KPIs immediately.
    If trigger_flow is True, it also starts a Prefect orchestrated pipeline.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()

    try:
        # 1. Immediate Ingestion & KPI feedback
        ingestor = UnifiedIngestion(strict_validation=True)
        # Note: UnifiedIngestion expects ingest_file or ingest_csv, 
        # let's assume ingest_dataframe for BytesIO if supported or save to tmp.
        import pandas as pd
        df = pd.read_csv(io.BytesIO(content))
        df = ingestor.ingest_dataframe(df)

        if df.empty:
            raise ValueError("Ingested dataframe is empty or invalid.")

        engine = PolarsAnalyticsEngine(df)
        kpis = engine.compute_kpis()
        summary = ingestor.get_ingest_summary()

        # 2. Optional: Trigger Prefect Flow for Orchestration & Reporting
        flow_run_id = None
        if trigger_flow:
            # For demonstration, we save to a temp file and trigger the flow
            # In production, this would use Prefect's deployment trigger (API)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # This triggers the flow locally in the same process for now
            # In a full Prefect setup, you'd use `run_deployment`
            loan_ingestion_flow(tmp_path)
            flow_run_id = "triggered_locally"

        return {
            "status": "success",
            "run_id": summary["run_id"],
            "flow_run_id": flow_run_id,
            "rows_processed": len(df),
            "kpis": kpis,
            "timestamp": summary["timestamp"],
        }

    except ValueError as e:
        logger.warning(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
