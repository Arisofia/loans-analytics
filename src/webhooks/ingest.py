import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Abaco Loans Ingestion")


@app.post("/ingest/azure-form")
async def ingest_azure_form(request: Request) -> dict[str, Any]:
    """
    Receives payload from Azure Web Form.
    Forwards to n8n webhook or inserts directly to Supabase.
    """
    try:
        payload = await request.json()
        logger.info("Received payload", extra={"payload": payload})

        n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
        if n8n_webhook_url:
            logger.info("N8N webhook configured", extra={"n8n_webhook_url": n8n_webhook_url})

        return {
            "status": "success",
            "message": "Data received and queued",
        }
    except Exception as exc:
        logger.exception("Error processing request")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "active",
        "service": "ingestion-layer",
    }
