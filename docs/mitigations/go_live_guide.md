# Go-Live Execution Manual (Secure Next.js + Nginx + Data Processor)
This document captures the step-by-step commands and verification steps to put the secure Next.js deployment "en vivo" (Linux/Docker-based environment).
## Prerequisites
- Linux (Ubuntu/Debian preferred)
- Docker & Docker Compose
- Git
- Repository cloned locally and updated
## Phase 1: Repo & Security
1. Clone repo and checkout branch
```bash
git clone <repo-url>
cd abaco-loans-analytics
git checkout -b secure-deploy
```
2. Add secret to repository (example using `gh`):
```bash
export MIDDLEWARE_SHARED_SECRET="<your-secret>"
gh secret set MIDDLEWARE_SHARED_SECRET -R <org/repo> --body "$MIDDLEWARE_SHARED_SECRET"
```
## Phase 2: Nginx configuration
- The config at `nginx-conf/default.conf` strips the exploit header and logs request fields for monitoring.
## Phase 3: Build & Run (Docker Compose)
1. Build and start
```bash
# Choose the compose file variant (override includes nginx + data processor)
docker compose -f docker-compose.yml -f docker-compose.override.yml up --build -d
```
2. Verify containers
```bash
docker compose ps
```
## Phase 4: Verify the Fix
1. Attempt the exploit (local)
```bash
curl -I -H "x-middleware-subrequest: middleware:middleware:middleware" http://localhost/admin
```
Expected: Nginx should drop the header and the app should not see it. App logs should NOT show the middleware 'Blocked' message. If app responds 403 with "Security Violation", it indicates Nginx bypass or missing secret.
2. Inspect logs
```bash
docker logs nginx_proxy --tail 200
docker logs nextjs_secure --tail 200
```
Look for `$http_x_middleware_subrequest` values in Nginx logs and absence in app logs.
## Phase 5: Observability
- Forward Nginx logs into your observability pipeline (e.g., Grafana Alloy, Datadog). Include the `x_middleware_subrequest` field in the log_line for security metrics.
## Phase 6: Post-Deployment
- Rotate `MIDDLEWARE_SHARED_SECRET` periodically, and document rotation steps in `docs/mitigations/rotate_secrets.md`.
- Run the `Deploy verification` workflow and attach the run logs to the PR.
---
If you'd like, I can open a PR with these files and a short checklist in `docs/mitigations` referencing the deploy-verify workflow and the production rollout checklist.