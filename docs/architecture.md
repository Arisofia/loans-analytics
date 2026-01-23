# ABACO LOANS ANALYTICS - SYSTEM ARCHITECTURE

**Status**: ✅ OPERATIONAL (Updated January 5, 2026)
**Owner**: Engineering / Data Team
**Last Updated**: 2026-01-05

---

## 1. OVERVIEW

The Abaco Loans Analytics platform is a unified system for ingesting loan tape data, transforming it for analysis, calculating key performance indicators (KPIs), and visualizing results through an interactive dashboard.

## 2. COMPONENT ARCHITECTURE

### 2.1. Analytics Pipeline (Python Backend)
The core logic resides in a modular Python pipeline that follows a 4-phase execution model:
1.  **Ingestion**: Supports CSV files (local/Azure Blob) and Looker exports.
2.  **Transformation**: Normalization, PII masking, outlier detection, and data quality checks.
3.  **Calculation**: KPI computation using `KPIEngineV2` and custom composite logic.
4.  **Output**: Generates Parquet, CSV, and JSON artifacts with full audit trails and lineage.

**Key Files**:
- `src/pipeline/orchestrator.py`: Main execution flow.
- `src/pipeline/config.py`: Centralized configuration management.
- `src/kpi_engine_v2.py`: Reusable KPI calculation engine.

### 2.2. API Service (FastAPI)
Exposes pipeline functionality and metrics to the frontend.
- **Location**: `apps/analytics/api/main.py`
- **Endpoints**:
    - `GET /api/kpis/latest`: Fetches results from the most recent pipeline run.
    - `POST /api/pipeline/trigger`: Triggers a new pipeline execution.

### 2.3. Frontend Dashboard (Next.js)
A modern web interface for visualising portfolio health and risk metrics.
- **Location**: `apps/web`
- **Tech Stack**: Next.js 15+, React 18+, Tailwind CSS, Playwright (E2E).
- **Integration**: Proxies requests to the Python API via `apps/web/src/app/api/kpis/latest`.

## 3. DATA ARCHITECTURE

### 3.1. Storage Layers
- **Raw Data**: Stored in `data/raw/` or Azure Blob Storage.
- **Artifacts**: Each pipeline run generates a timestamped directory in `logs/runs/` containing:
    - Processed data (Parquet/CSV)
    - KPI results (JSON manifest)
    - Compliance/Audit reports
- **Metadata**: Lineage and data quality scores are embedded in the run manifests.

### 3.2. Configuration
- **Master Config**: `config/pipeline.yml` (Single source of truth).
- **Business Rules**: `config/business_rules.yaml` (Statuses, buckets, constants).
- **KPI Definitions**: `config/kpis/kpi_definitions.yaml`.

---

## 4. FUTURE ROADMAP

### 4.1. Planned Enhancements
- **Kotlin Services**: Migration of high-throughput ingestion logic to Kotlin-based microservices.
- **Advanced Agents**: Integration of specialized AI agents for automated risk narratives and growth projections.
- **Supabase Integration**: Persistence of historical KPIs into a structured database for long-term trend analysis.
- **Real-time Ingestion**: Transition from batch processing to event-driven updates via webhooks.

### 4.2. Tooling Upgrades
- Transition to **PapaParse** for robust client-side CSV handling.
- Implementation of **Great Expectations** for advanced data validation.
- Enhanced observability with **OpenTelemetry** and centralized logging.
