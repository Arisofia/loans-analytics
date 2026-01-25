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

## Configuration

Set the following environment variables in your runtime:

- `N8N_WEBHOOK_URL`: the n8n webhook endpoint that should receive payloads.
- `N8N_HOST`, `N8N_USER`, `N8N_PASS`: used by the docker-compose service for the n8n UI.

When `N8N_WEBHOOK_URL` is set, the ingestion service logs that the webhook is
ready for forwarding. The forwarding implementation is intentionally minimal so
that you can wire in a request client (for example, `httpx`) or a Supabase client
based on your deployment requirements.
