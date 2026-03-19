# Strategic Analytics Requirements - Delivery Map

This document maps implementation outputs to the strategic requirements:

1. Build predictive models for forecasting, opportunity prioritization, and churn analysis.
2. Develop analytics infrastructure for pricing, LTV, CAC, and margins.
3. Integrate financial + commercial analytics for strategic support.
4. Build executive dashboards and automated reporting.
5. Guarantee data quality and governance.
6. Confirm CAC, LTV, margins, and revenue forecasting.

## Implemented Outputs

- KPI processor: `python/kpis/catalog_processor.py`
  - `revenue_forecast_6m`
  - `opportunity_prioritization`
  - `churn_90d_metrics`
  - `pricing_analytics`
  - `unit_economics` (CAC, LTV, LTV/CAC, gross margin)
  - `data_governance`
  - `strategic_confirmations`
- Streamlit dashboard: `streamlit_app/app.py`, `streamlit_app/components/analytics_tabs.py`
  - Dashboard links section
  - Strategic confirmation badges (CAC/LTV/Margins/Revenue Forecast)
  - Tabs for Forecasting, Opportunity, Churn, Unit Economics, Pricing/Governance
- Automated reporting:
  - Module: `python/kpis/strategic_reporting.py`
  - CLI: `scripts/reporting/generate_strategic_report.py`
  - Make target: `make report-strategic`
  - Outputs: `reports/strategic/strategic_report_latest.json` and `.md`

## Dashboard Links

- Streamlit local: `http://localhost:8000` (canonical port, aligns with API and startup.sh)
- Grafana local: `http://localhost:3001/dashboards`
- Streamlit deployed: `https://abaco-analytics-dashboard.azurewebsites.net`
- Dashboard docs: `docs/analytics/dashboards.md`

## Confirmation Criteria

Use the generated strategic report and verify:

- `summary.confirmations.cac_confirmed == true`
- `summary.confirmations.ltv_confirmed == true`
- `summary.confirmations.margin_confirmed == true`
- `summary.confirmations.revenue_forecast_confirmed == true`

If any field is `false`, regenerate KPI exports and rerun `make report-strategic`.
