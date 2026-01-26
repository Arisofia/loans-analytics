# Docker (Local)

This repo contains multiple services. The simplest local stack is:

- **Frontend**: Next.js app in `apps/web`
- **Backend**: Streamlit dashboard in `dashboard`

## Prereqs

- Docker Desktop

## Configure env

1. Copy `.env.example` → `.env`
2. Fill at least:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Run

- `docker compose -f docker-compose.yml up --build`

## Development (hot reload)

- `docker compose -f docker-compose.dev.yml up`

This uses bind mounts for `apps/web` and `dashboard` and runs dev commands.

## Optional local Postgres

- `docker compose -f docker-compose.yml --profile db up --build`

This starts a local Postgres container (for local testing only).

## URLs

- Frontend: <http://localhost:3000>
- Dashboard (Streamlit): <http://localhost:8000>
- Dashboard health check: <http://localhost:8000/?page=health>
