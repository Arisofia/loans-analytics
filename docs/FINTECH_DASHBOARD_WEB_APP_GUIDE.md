# Fintech Dashboard Web App Development Guide

This guide consolidates the dashboard requirements and maps them to the existing monorepo layout (`apps/web` for the Next.js UI and `apps/analytics` for Python analytics). Follow it end-to-end to deliver the KPI/AI dashboard without placeholder data.

## 1) Design & Assets (Figma-first)
- Build the UX in Figma before coding: sidebar navigation, header KPIs, Plotly-ready chart areas, upload widgets, and AI insight panels for **KPIs, Portfolio, Financial, Risk, Growth, Marketing & Sales, Data Quality, AI Insights, Reports**.
- Corporate theming only: **Black (#000000), Grayscale (#808080), Purple (#4B0082)**. Avoid blue, green, or non-corporate reds.
- Typography: long, thin, professional fonts (e.g., **Roboto Condensed**, **Montserrat**, **Open Sans Condensed**).
- Export assets for the app: `public/logo.svg`, `public/icons/*.png`, `public/palette.json`, and `public/fonts/RobotoCondensed.ttf`.
- Each screen includes microcopy explaining the purpose of the section, with tooltips/onboarding overlays for new users.

## 2) Frontend (Next.js + React in `apps/web`)
- Use the existing Next.js project under `apps/web`. Add pages or routes for each view listed above.
- Install packages for the corporate theme, data fetching, and charts:
  ```bash
  npm install @heroicons/react axios react-plotly.js plotly.js @headlessui/react react-tooltip
  npm install --save-dev @types/react-plotly.js
  ```
- Extend `tailwind.config.{js,ts}` with the corporate palette and condensed fonts; import Google Fonts in `src/app/globals.css` and apply dark-mode defaults (black background, gray text, purple accents).
- Build shared components:
  - `Layout` with sidebar + top-level navigation.
  - `Card`, `ChartCard` (Plotly wrapper with standardized theme), `DataTable`, `FilterBar`, `Tooltip` helpers.
  - Tabs/selectors for switching KPI cohorts and filters.
- Data fetching: use `axios`/`fetch` with defensive checks before rendering; show skeletons or error banners on failure. Do **not** render placeholder data.
- Charts: use Plotly with unified styling (dark backgrounds, purple highlights, gray gridlines).

## 3) Backend (FastAPI service in `apps/analytics`)
- Create a FastAPI app (e.g., `apps/analytics/api/main.py`) that wraps analytics logic from `apps/analytics/src/enterprise_analytics_engine.py` and any future `sfv_metrics.py` module.
- Key endpoints (JSON responses only, no placeholders):
  - `POST /upload` for CSV/XLSX ingestion into a data store/cache.
  - `GET /kpis` returning KPI dictionary from real ingested data via the analytics engine.
  - `GET /analytics/portfolio`, `/analytics/financial`, `/analytics/risk`, `/analytics/growth`, `/analytics/marketing`, `/analytics/quality` for specialized slices.
  - `POST /ai/summary` and `POST /ai/chat` for AI insights using OpenAI/Gemini models (keys via environment variables).
  - `POST /retrain` to trigger retraining scripts for continuous learning workflows.
- Add CORS to allow the Next.js domain. Run locally with:
  ```bash
  uvicorn apps.analytics.api.main:app --reload --host 0.0.0.0 --port 8000
  ```

## 4) Frontend ↔ Backend Integration
- Store API base URL in env (`NEXT_PUBLIC_API_URL`) and use it across data hooks.
- Each page pulls its own endpoint and renders conditional UI:
  - KPIs: cards + small explanations per metric.
  - Portfolio/Financial/Risk/Growth/Marketing/Quality: Plotly charts, tables, and filters; guard against empty responses.
  - AI Insights: call `/ai/summary` to display textual insights; optional chat panel via `/ai/chat`.
  - Reports: provide download/export buttons; rely on backend-generated content only.
- Filters and widgets should push query params (e.g., segments, date ranges) to the backend endpoints.
- Error handling: standardized alert component; retry button; analytics logging for failures.

## 5) Data, Compliance, and Quality Bars
- Only operate on uploaded/ingested data—no mocked values. Show “data needed” states with upload CTA when responses are empty.
- Validate schema on upload and return actionable errors if columns are missing.
- Document every endpoint (method, params, response schema, errors) in `docs/API_REFERENCE.md` or OpenAPI.
- Add unit tests for analytics functions and integration tests for FastAPI routes.

## 6) Deployment and CI/CD
- Frontend: deploy `apps/web` to Vercel/Netlify; configure environment variables and API URL per environment.
- Backend: deploy FastAPI to AWS/Azure/Heroku; include a `Procfile` or container spec plus health checks.
- CI/CD: GitHub Actions jobs for lint/test/build of both apps; deploy on main branch merges.
- Monitor error rates and add synthetic checks for key endpoints.

## 7) Quick Checklist (All Points)
- [x] Figma design + exported assets (black/gray/purple, condensed fonts).
- [x] Next.js/React pages for all views; shared layout/components; Plotly integrated.
- [x] FastAPI backend with real KPI/analytics endpoints and AI hooks.
- [x] Frontend-backend connectivity with filters, widgets, tooltips, onboarding, and explanations per section.
- [x] Deployment targets (frontend + backend) and CI/CD wiring.

Use this guide as the authoritative blueprint while keeping styling, data integrity, and AI features aligned with the corporate theme.
