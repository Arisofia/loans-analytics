# OWNER_MAP

Ownership by folder so each change has a clear responsible area.

## Product Domains

- `python/apps/analytics/api/` -> API Platform owner
- `python/kpis/` + `config/kpis/` -> KPI & Finance Analytics owner
- `python/multi_agent/` -> Agent Platform owner
- `src/pipeline/` -> Data Pipeline owner
- `streamlit_app/` -> Analytics UI owner
- `tests/` + `python/tests/` -> QA owner
- `.github/workflows/` -> DevSecOps owner
- `infra/` + `db/migrations/` -> Cloud/Infra owner
- `scripts/maintenance/` -> Platform Reliability owner
- `scripts/monitoring/` + `grafana/` + `config/prometheus.yml` -> Observability owner

## Change Routing Rule

- API contract change -> API Platform + QA
- KPI formula change -> KPI & Finance Analytics + QA
- Agent prompt/protocol/tracing change -> Agent Platform + QA
- Deployment/security workflow change -> DevSecOps + Cloud/Infra
- Monitoring/alerts/dashboards change -> Observability + DevSecOps
