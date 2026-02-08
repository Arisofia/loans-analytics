import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Optional

import sentry_sdk

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        send_default_pii=True,
    )
    logging.getLogger("sentry_sdk").setLevel(logging.ERROR)  # Suppress Sentry debug logs


# Avoid importing FastAPI at module import time so tests don't require
# fastapi installed. Use a lazy import and a lightweight HTTPException
# fallback for environments without FastAPI.
try:
    from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request

    from python.apps.analytics.api.models import (
        DataQualityResponse,
        FullAnalysisResponse,
        KpiResponse,
        KpiSingleResponse,
        LoanPortfolioRequest,
        RiskAlertsResponse,
        RiskLoan,
        ValidationResponse,
    )
    from python.apps.analytics.api.monitoring_models import (
        CommandCreate,
        CommandsListResponse,
        CommandStatus,
        CommandUpdate,
        EventSeverity,
        EventsListResponse,
        OperationalEventCreate,
    )
    from python.apps.analytics.api.monitoring_service import MonitoringService
    from python.apps.analytics.api.service import KPIService
    from python.multi_agent.orchestrator import MultiAgentOrchestrator

    app: Optional[FastAPI] = FastAPI(title="Abaco Loans Analytics API")

except ImportError:  # pragma: no cover - fallback in tests/environments without FastAPI

    class HTTPException(Exception):  # type: ignore[no-redef]
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Depends:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    class Body:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    class Query:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    app = None

logger = logging.getLogger("apps.analytics.api")
# Directory that contains allowed data files (must be absolute)
ALLOWED_DATA_DIR = Path("/data/archives").resolve()


def get_kpi_service():
    # In a real scenario, we'd extract the user/actor from the auth token
    return KPIService(actor="api_user")


def get_monitoring_service():
    # In a real scenario, we'd extract the user/actor from the auth token
    return MonitoringService(actor="api_user")


# ---------------------------------------------------------------------------
# Correlation-ID Middleware
# ---------------------------------------------------------------------------
if app is not None:

    # --- Prometheus metrics (exposes GET /metrics) ---
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator not installed; /metrics disabled")

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        """Inject or propagate X-Correlation-ID and tag Sentry."""
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        sentry_sdk.set_tag("correlation_id", correlation_id)
        sentry_sdk.set_context("monitoring", {"correlation_id": correlation_id})
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    # -------------------------------------------------------------------
    # Monitoring & Command Endpoints
    # -------------------------------------------------------------------

    @app.post("/monitoring/events", response_model=EventsListResponse)
    async def emit_event(
        event: OperationalEventCreate = Body(...),
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """Emit an operational event (pipeline complete, KPI breach, etc.)."""
        try:
            created = await service.emit_event(event)
            return EventsListResponse(events=[created], count=1)
        except Exception as e:
            logger.error("Error emitting event: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/monitoring/events", response_model=EventsListResponse)
    async def list_events(
        severity: Optional[str] = Query(None, description="Filter by severity"),
        source: Optional[str] = Query(None, description="Filter by source"),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """List operational events with optional filters."""
        try:
            sev = EventSeverity(severity) if severity else None
            events = await service.list_events(
                severity=sev, source=source, limit=limit, offset=offset
            )
            return EventsListResponse(events=events, count=len(events))
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {severity}. Must be info, warning, or critical",
            ) from exc
        except Exception as e:
            logger.error("Error listing events: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/monitoring/events/{event_id}/ack")
    async def acknowledge_event(
        event_id: str,
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """Acknowledge an operational event."""
        try:
            eid = uuid.UUID(event_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid event ID format") from exc

        try:
            result = await service.acknowledge_event(eid)
            if result is None:
                raise HTTPException(status_code=404, detail="Event not found")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error acknowledging event %s: %s", event_id, e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/monitoring/commands", response_model=CommandsListResponse)
    async def create_command(
        cmd: CommandCreate = Body(...),
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """Create a new command for n8n or operators to execute."""
        try:
            created = await service.create_command(cmd)
            return CommandsListResponse(commands=[created], count=1)
        except Exception as e:
            logger.error("Error creating command: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/monitoring/commands", response_model=CommandsListResponse)
    async def list_commands(
        status: Optional[str] = Query(None, description="Filter by status"),
        limit: int = Query(50, ge=1, le=500),
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """List commands with optional status filter."""
        try:
            st = CommandStatus(status) if status else None
            commands = await service.list_commands(status=st, limit=limit)
            return CommandsListResponse(commands=commands, count=len(commands))
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be pending, running, completed, or failed",
            ) from exc
        except Exception as e:
            logger.error("Error listing commands: %s", e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.patch("/monitoring/commands/{cmd_id}")
    async def update_command(
        cmd_id: str,
        update: CommandUpdate = Body(...),
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """Update command status and result (used by n8n after execution)."""
        try:
            cid = uuid.UUID(cmd_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid command ID format") from exc

        try:
            result = await service.update_command_status(cid, update)
            if result is None:
                raise HTTPException(status_code=404, detail="Command not found")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error updating command %s: %s", cmd_id, e)
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.post("/analytics/kpis", response_model=KpiResponse)
    async def calculate_all_kpis(
        request: LoanPortfolioRequest = Body(...), service: KPIService = Depends(get_kpi_service)
    ):
        """
        Get all portfolio KPIs.
        If loan data is provided, calculates in real-time. Otherwise, returns latest snapshot.
        """
        try:
            if request.loans:
                # Extract loan_ids from the provided loan records
                loan_ids_from_request = [loan.id for loan in request.loans]
                kpis = await service.calculate_kpis_for_portfolio(loan_ids_from_request)
            else:
                kpis = await service.get_latest_kpis()
            return KpiResponse(kpis=kpis)
        except Exception as e:
            logger.error(f"Error in calculate_all_kpis: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/analytics/kpis/{kpi_id}", response_model=KpiSingleResponse)
    async def get_single_kpi(
        kpi_id: str,
        request: LoanPortfolioRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """
        Get a specific KPI by ID (par30, par90, etc.)
        If loan data is provided, calculates in real-time. Otherwise, returns latest snapshot.
        """
        # Map path-style IDs to DB keys if necessary
        kpi_key_map = {
            "par30": "PAR30",
            "par90": "PAR90",
            "collection-rate": "COLLECTION_RATE",
            "portfolio-health": "PORTFOLIO_HEALTH",
            "ltv": "LTV",
            "dti": "DTI",
            "portfolio-yield": "PORTFOLIO_YIELD",
        }

        db_key = kpi_key_map.get(kpi_id.lower(), kpi_id.upper())

        try:
            if request.loans:
                loan_ids_from_request = [loan.id for loan in request.loans]
                # Calculate all for context and pick the one requested
                kpis = await service.calculate_kpis_for_portfolio(loan_ids_from_request)
                kpi = next((k for k in kpis if k.id == db_key), None)
            else:
                kpi = await service.get_kpi_by_id(db_key)

            if not kpi:
                raise HTTPException(status_code=404, detail=f"KPI {kpi_id} not found")
            return kpi
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_single_kpi: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/analytics/risk-alerts", response_model=RiskAlertsResponse)
    async def get_risk_alerts(
        request: LoanPortfolioRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """
        Identifies high-risk loans based on LTV and DTI thresholds.
        """
        try:
            # Use thresholds from request or defaults
            ltv = request.ltv_threshold if request.ltv_threshold is not None else 80.0
            dti = request.dti_threshold if request.dti_threshold is not None else 50.0

            risk_loans_data = await service.get_risk_alerts(
                loans=request.loans, ltv_threshold=ltv, dti_threshold=dti
            )
            risk_loans = [RiskLoan(**loan) for loan in risk_loans_data]

            # Determine overall risk level
            risk_level = "low"
            if any(loan.risk_score > 70 for loan in risk_loans):
                risk_level = "high"
            elif any(loan.risk_score > 40 for loan in risk_loans):
                risk_level = "medium"

            return RiskAlertsResponse(risk_level=risk_level, high_risk_loans=risk_loans)
        except Exception as e:
            logger.error(f"Error in get_risk_alerts: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/analytics/full-analysis", response_model=FullAnalysisResponse)
    async def get_full_analysis(
        request: LoanPortfolioRequest = Body(...), service: KPIService = Depends(get_kpi_service)
    ):
        """
        Runs a comprehensive multi-agent analysis on the specified loan portfolio.
        """
        try:
            # 1. Fetch data context for the orchestrator
            # For simplicity, we'll fetch latest KPIs as context
            kpis = await service.get_latest_kpis()
            kpi_summary = "\n".join([f"{k.name}: {k.value} {k.unit}" for k in kpis])

            # 2. Initialize Orchestrator
            orchestrator = MultiAgentOrchestrator()

            # 3. Run Scenario
            # We use a synthetic trace_id for this request
            trace_id = str(uuid.uuid4())

            loan_ids_from_request = [loan.id for loan in request.loans] if request.loans else []

            initial_context = {
                "portfolio_data": (
                    "Recent KPI Snapshot:\n"
                    f"{kpi_summary}\n"
                    f"Target Loans: {', '.join(loan_ids_from_request)}"
                )
            }

            results = orchestrator.run_scenario(
                scenario_name="loan_risk_review",
                initial_context=initial_context,
                trace_id=trace_id,
            )

            # 4. Map results to Response Model
            # The loan_risk_review scenario typically ends with a risk assessment
            # We'll parse the results dictionary which contains keys like 'risk_assessment'
            # based on the scenario steps defined in orchestrator.py

            summary = results.get("risk_assessment", "Analysis completed successfully.")

            return FullAnalysisResponse(
                analysis_id=trace_id,
                summary=summary,
                recommendations=[
                    "Monitor high-LTV loans",
                    "Review collection strategy for DPD > 30",
                ],
                risk_assessment=RiskAlertsResponse(
                    risk_level="medium",  # This would ideally be parsed from agent output
                    high_risk_loans=[],
                ),
            )
        except Exception as e:
            logger.error(f"Error in get_full_analysis: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/data-quality/profile", response_model=DataQualityResponse)
    async def get_data_quality_profile(
        request: LoanPortfolioRequest = Body(...), service: KPIService = Depends(get_kpi_service)
    ):
        """
        Generate data quality profile for the provided loan portfolio data.
        """
        try:
            dq_profile = await service.get_data_quality_profile(request.loans)
            return dq_profile
        except Exception as e:
            logger.error(f"Error in get_data_quality_profile: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post(
        "/data-quality/validate",
        response_model=ValidationResponse,
    )
    async def validate_loan_data(
        request: LoanPortfolioRequest = Body(...), service: KPIService = Depends(get_kpi_service)
    ):
        """
        Validate that the provided loan data contains all required
        columns and meets schema requirements.
        """
        try:
            validation_result = await service.validate_loan_portfolio_schema(request.loans)
            return validation_result
        except Exception as e:
            logger.error(f"Error in validate_loan_data: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.get("/data/{file_path:path}")
    def get_data(file_path: str):
        """Return file contents for a path under ALLOWED_DATA_DIR after sanitization."""
        if not file_path or not file_path.strip():
            raise HTTPException(status_code=400, detail="file path cannot be empty")

        try:
            resolved = _sanitize_and_resolve(file_path, ALLOWED_DATA_DIR)
        except ValueError as exc:
            safe_path = _sanitize_for_logging(file_path)
            logger.warning("Invalid data path requested: %s (%s)", safe_path, str(exc))
            raise HTTPException(status_code=400, detail="Invalid path format") from exc

        if not resolved.exists() or not resolved.is_file():
            raise HTTPException(status_code=404, detail="file not found")

        return {"status": "ok", "path": str(resolved)}


def _sanitize_for_logging(value: str, max_length: int = 200) -> str:
    if not value:
        return ""
    sanitized = (
        value.replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace("\x00", "")
        .replace("\x1b", "")
    )
    sanitized = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", sanitized)
    if len(sanitized) > max_length:
        return sanitized[:max_length] + "...[truncated]"
    return sanitized


def _sanitize_and_resolve(candidate: str, allowed_dir: Path) -> Path:
    if not candidate:
        raise ValueError("empty path")
    normalized = candidate.replace("\\", "/")
    candidate_path = Path(normalized)
    if candidate_path.is_absolute():
        raise ValueError("absolute paths are not allowed")
    if any(p == ".." for p in candidate_path.parts):
        raise ValueError("parent traversal is not allowed")
    if not re.match(r"^[a-zA-Z0-9_./\-]+$", str(candidate_path)):
        raise ValueError("invalid characters")
    resolved = (allowed_dir / candidate_path).resolve()
    try:
        resolved.relative_to(allowed_dir.resolve())
    except ValueError as exc:
        raise ValueError("outside the allowed data directory") from exc
    return resolved


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    if app is not None:
        uvicorn.run(app, host=host, port=port)
    else:
        print("FastAPI app not initialized. Check imports.")
        sys.exit(1)
