import logging
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Abaco Loans Ingestion")


class AzureFormPayload(BaseModel):
    submission_id: str = Field(..., description="Unique submission identifier")
    timestamp: str = Field(..., description="ISO8601 submission timestamp")
    user_email: str | None = Field(None, description="Applicant email address")
    applicant_id: str | None = Field(None, description="Applicant identifier")
    amount: float | None = Field(None, description="Requested loan amount")
    status: str | None = Field("pending", description="Submission status")


@app.post("/ingest/azure-form")
async def ingest_azure_form(payload: AzureFormPayload) -> dict[str, Any]:
    """
    Receives payload from Azure Web Form.
    Forwards to n8n webhook or inserts directly to Supabase.
    """
    logger.info(
        "Received Azure form submission",
        extra={
            "submission_id": payload.submission_id,
            "timestamp": payload.timestamp,
        },
    )

    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not n8n_webhook_url:
        logger.warning("N8N webhook not configured; payload not forwarded")
        return {
            "status": "received",
            "forwarded": False,
            "message": "N8N_WEBHOOK_URL not set",
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(n8n_webhook_url, json=payload.model_dump())
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Failed to forward payload to n8n", extra={"n8n_url": n8n_webhook_url})
        raise HTTPException(status_code=502, detail="Failed to forward to n8n webhook") from exc

    logger.info("Forwarded payload to n8n", extra={"n8n_url": n8n_webhook_url})
    return {
        "status": "forwarded",
        "n8n_status": response.status_code,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "active",
        "service": "ingestion-layer",
    }
