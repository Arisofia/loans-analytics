# Runbook: Pipeline Failure (GitHub Actions)

**Symptoms**

- Scheduled/dispatch workflows failing (often within seconds).
- No new data landing in `data/raw/` or warehouse outputs.

**Primary goals**

1. Identify which layer failed: install/build vs runtime vs external dependency.
2. Classify the failure: dependency, secret, permission, API outage, DB connectivity.
3. Restore at least one critical pipeline path.

## Triage (5–15 minutes)

1) **Pick one failing workflow and open the first error**

- GitHub → Actions → workflow run → open the first failing step.
- Copy the first ~50 lines around the first exception.

1) **Classify by runtime duration**

- **< 30s**: dependency install/build/config/secrets issue.
- **minutes**: API/DB latency, retries, data volume issues.

1) **Check required secrets exist**
Common secrets referenced by workflows:

- `DATABASE_URL` (Postgres/Supabase)
- `META_SYSTEM_USER_TOKEN` / Meta token(s)
- `HUBSPOT_API_KEY`
- `AZURE_CREDENTIALS` / publish profiles (deploy workflows)

Quick validation:

- Run `python scripts/validate_secrets.py --presence-only` locally, or
- Run the GitHub Actions workflow **Verify Secrets and Integrations**.

## Decision flow

```mermaid
flowchart TD
  A[Pipeline run failed] --> B{Failed during install/build?}
  B -->|Yes| C{Error is 'No matching distribution' / pip install?}
  C -->|Yes| D[Fix requirements pin; push; rerun]
  C -->|No| E{Error is TS compile / tsc?}
  E -->|Yes| F[Exclude test files from build or add missing @types deps]
  E -->|No| G[Check node/python version mismatch; lockfile integrity]

  B -->|No| H{Failed at runtime step?}
  H -->|Yes| I{Missing env/secret? (KeyError/empty var)}
  I -->|Yes| J[Add GitHub secret; rerun]
  I -->|No| K{401/403 from API?}
  K -->|Yes| L[Rotate token; update secret; rerun]
  K -->|No| M{DB connect error?}
  M -->|Yes| N[Verify DATABASE_URL, network, pooler host; retry]
  M -->|No| O[Inspect logs; add targeted retries/backoff; escalate]
```

## Evidence to capture

- Workflow name, run URL, job name, step name.
- First failing error block.
- Secrets referenced by workflow file (names only; never paste secret values).

## Quick mitigations

- Re-run workflow after pushing fixes or adding secrets.
- If an external API is down, disable schedule temporarily and document impact.
- For DB failures, test `DATABASE_URL` from a secure environment (do not log credentials).

## Follow-up hardening

- Add explicit secret checks early in workflows (fail fast with clear message).
- Pin runtimes (Node/Python) and keep dependency pins valid.
- Add retries for transient HTTP failures.
