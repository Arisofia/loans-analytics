# Webhook Ingestion

## Azure → n8n → Supabase Flow

The ingestion layer exposes a FastAPI endpoint that accepts payloads from the
Azure Web Form and hands them off to n8n for orchestration. Use this service as
an integration point before persisting to Supabase or triggering downstream
analytics workflows.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| POST | `/ingest/azure-form` | Receives Azure Web Form payloads. |
| GET | `/health` | Lightweight health check for the ingestion layer. |

## Payload Contract

The ingestion service validates the Azure payload with a Pydantic model. Provide
at least the required fields below:

| Field | Required | Description |
| --- | --- | --- |
| `submission_id` | Yes | Unique submission identifier. |
| `timestamp` | Yes | ISO8601 submission timestamp. |
| `user_email` | No | Applicant email address. |
| `applicant_id` | No | Applicant identifier. |
| `amount` | No | Requested loan amount. |
| `status` | No | Submission status (defaults to `pending`). |

## Configuration

Set the following environment variables in your runtime:

- `N8N_WEBHOOK_URL`: the n8n webhook endpoint that should receive payloads.
- `N8N_HOST`, `N8N_USER`, `N8N_PASS`: used by the docker-compose service for the n8n UI.

When `N8N_WEBHOOK_URL` is set, the ingestion service forwards the payload to n8n
and returns the downstream HTTP status. If it is not set, the service returns a
clear placeholder response indicating that forwarding is disabled.
