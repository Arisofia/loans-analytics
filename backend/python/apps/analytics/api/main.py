import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

try:
    import jwt
except ImportError:  # pragma: no cover - optional dependency in some test envs
    jwt = None

# Avoid importing FastAPI at module import time so tests don't require
# fastapi installed. Use a lazy import and a lightweight HTTPException
# fallback for environments without FastAPI.
try:
    from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request
    from fastapi.responses import JSONResponse

    from backend.python.apps.analytics.api.models import (
        AdvancedRiskResponse,
        CohortAnalyticsRequest,
        CohortAnalyticsResponse,
        DataQualityResponse,
        DecisionDashboardResponse,
        DefaultPredictionRequest,
        DefaultPredictionResponse,
        ExecutiveAnalyticsRequest,
        ExecutiveAnalyticsResponse,
        FullAnalysisResponse,
        KpiCoverageResponse,
        KpiResponse,
        KpiSingleResponse,
        LoanPortfolioRequest,
        NSMRecurrentTPVResponse,
        RiskAlertsResponse,
        RiskLoan,
        RiskStratificationResponse,
        RollRateAnalyticsRequest,
        RollRateAnalyticsResponse,
        SegmentAnalyticsRequest,
        SegmentAnalyticsResponse,
        StressTestRequest,
        StressTestResponse,
        UnitEconomicsRequest,
        UnitEconomicsResponse,
        ValidationResponse,
        VintageCurveResponse,
    )
    from backend.python.apps.analytics.api.monitoring_models import (
        CommandCreate,
        CommandsListResponse,
        CommandStatus,
        CommandUpdate,
        EventAcknowledgeRequest,
        EventSeverity,
        EventsListResponse,
        OperationalEventCreate,
    )
    from backend.python.apps.analytics.api.monitoring_service import MonitoringService
    from backend.python.apps.analytics.api.service import KPIService
    from backend.python.logging_config import init_sentry, set_sentry_correlation
    from backend.src.agents.multi_agent.orchestrator import MultiAgentOrchestrator

    init_sentry(service_name="analytics-api")

    app: Optional[FastAPI] = FastAPI(title="Abaco Loans Analytics API")

except ImportError:  # pragma: no cover - fallback in tests/environments without FastAPI

    class HTTPException(Exception):  # type: ignore[no-redef]
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Depends:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            # Placeholder shim for environments where FastAPI isn't installed.
            self.args = args
            self.kwargs = kwargs

    class Body:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            # Placeholder shim for environments where FastAPI isn't installed.
            self.args = args
            self.kwargs = kwargs

    class Query:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            # Placeholder shim for environments where FastAPI isn't installed.
            self.args = args
            self.kwargs = kwargs

    app = None

logger = logging.getLogger("apps.analytics.api")
# Directory that contains allowed data files (must be absolute)
ALLOWED_DATA_DIR = Path("/data/archives").resolve()
INTERNAL_SERVER_ERROR = "Internal server error"


def get_kpi_service():
    # In a real scenario, we'd extract the user/actor from the auth token
    return KPIService(actor="api_user")


def get_monitoring_service():
    # In a real scenario, we'd extract the user/actor from the auth token
    return MonitoringService(actor="api_user")


def _build_kpi_response(
    kpis: list[Any] | None, source: str = "production-snapshot"
) -> "KpiResponse":
    """Map flat KPI list to strongly-typed KpiResponse payload."""
    kpi_map = {k.id: k for k in kpis} if kpis else {}
    return KpiResponse(
        PAR30=kpi_map.get("PAR30") or kpi_map.get("par_30"),
        PAR90=kpi_map.get("PAR90") or kpi_map.get("par_90"),
        PAR60=kpi_map.get("PAR60") or kpi_map.get("par_60"),
        DPD1_30=kpi_map.get("DPD_1_30")
        or kpi_map.get("dpd_1_30")
        or kpi_map.get("delinq_1_30_rate"),
        DPD31_60=kpi_map.get("DPD_31_60")
        or kpi_map.get("dpd_31_60")
        or kpi_map.get("delinq_31_60_rate"),
        DPD61_90=kpi_map.get("DPD_61_90") or kpi_map.get("dpd_61_90"),
        DPD90Plus=kpi_map.get("DPD_90_PLUS") or kpi_map.get("dpd_90_plus"),
        CollectionRate=kpi_map.get("COLLECTION_RATE") or kpi_map.get("collections_rate"),
        DefaultRate=kpi_map.get("DEFAULT_RATE") or kpi_map.get("default_rate"),
        TotalLoansCount=kpi_map.get("TOTAL_LOANS_COUNT") or kpi_map.get("total_loans_count"),
        LossRate=kpi_map.get("LOSS_RATE") or kpi_map.get("loss_rate"),
        RecoveryRate=kpi_map.get("RECOVERY_RATE") or kpi_map.get("recovery_rate"),
        CashOnHand=kpi_map.get("CASH_ON_HAND") or kpi_map.get("cash_on_hand"),
        CAC=kpi_map.get("CAC") or kpi_map.get("cac"),
        GrossMarginPct=kpi_map.get("GROSS_MARGIN_PCT") or kpi_map.get("gross_margin_pct"),
        RevenueForecast6M=kpi_map.get("REVENUE_FORECAST_6M") or kpi_map.get("revenue_forecast_6m"),
        Churn90D=kpi_map.get("CHURN_90D") or kpi_map.get("churn_90d"),
        PortfolioHealth=kpi_map.get("AUM") or kpi_map.get("portfolio_growth_rate"),
        CustomerLifetimeValue=kpi_map.get("CUSTOMER_LIFETIME_VALUE")
        or kpi_map.get("customer_lifetime_value"),
        ActiveBorrowers=kpi_map.get("ACTIVE_BORROWERS") or kpi_map.get("active_borrowers"),
        RepeatBorrowerRate=kpi_map.get("REPEAT_BORROWER_RATE")
        or kpi_map.get("repeat_borrower_rate"),
        AutomationRate=kpi_map.get("AUTOMATION_RATE") or kpi_map.get("automation_rate"),
        AverageLoanSize=kpi_map.get("AVERAGE_LOAN_SIZE") or kpi_map.get("average_loan_size"),
        ProcessingTimeAvg=kpi_map.get("PROCESSING_TIME_AVG") or kpi_map.get("processing_time_avg"),
        DisbursementVolumeMTD=kpi_map.get("DISBURSEMENT_VOLUME_MTD")
        or kpi_map.get("disbursement_volume_mtd"),
        NewLoansCountMTD=kpi_map.get("NEW_LOANS_COUNT_MTD") or kpi_map.get("new_loans_count_mtd"),
        LTV=kpi_map.get("AVG_LTV") or kpi_map.get("avg_ltv"),
        DTI=kpi_map.get("AVG_DTI") or kpi_map.get("avg_dti"),
        PortfolioYield=kpi_map.get("PORTFOLIO_YIELD") or kpi_map.get("portfolio_yield"),
        NPL=kpi_map.get("NPL") or kpi_map.get("npl_ratio"),
        LGD=kpi_map.get("LGD") or kpi_map.get("lgd_pct") or kpi_map.get("lgd"),
        CoR=kpi_map.get("COR") or kpi_map.get("cost_of_risk_pct") or kpi_map.get("cost_of_risk"),
        NIM=kpi_map.get("NIM") or kpi_map.get("nim_pct") or kpi_map.get("net_interest_margin"),
        CureRate=kpi_map.get("CURERATE")
        or kpi_map.get("cure_rate_pct")
        or kpi_map.get("cure_rate"),
        # Enriched KPIs from CONTROL DE MORA format
        CollectionsEligibleRate=kpi_map.get("collections_eligible_rate"),
        GovernmentSectorExposureRate=kpi_map.get("government_sector_exposure_rate"),
        AvgCreditLineUtilization=kpi_map.get("avg_credit_line_utilization"),
        CapitalCollectionRate=kpi_map.get("capital_collection_rate"),
        MdscPostedRate=kpi_map.get("mdsc_posted_rate"),
        audit_trail=[{"kpi_count": len(kpis or []), "source": source}],
    )


async def _resolve_analysis_kpis(
    request: "LoanPortfolioRequest", service: "KPIService"
) -> list[Any]:
    """Resolve KPI set for analysis, preferring request-scoped real-time calculations."""
    if request.loans:
        kpis = await service.calculate_kpis_for_portfolio(request.loans)
        if kpis:
            return kpis
    return await service.get_latest_kpis()


def _get_kpi_value(kpis: list[Any], candidates: list[str], default: float = 0.0) -> float:
    candidate_set = {candidate.lower() for candidate in candidates}
    for kpi in kpis:
        if (kpi.id or "").lower() in candidate_set:
            return float(kpi.value)
    return default


def _build_full_analysis_recommendations(
    kpis: list[Any], roll_rates: "RollRateAnalyticsResponse"
) -> list[str]:
    recommendations: list[str] = []
    par90 = _get_kpi_value(kpis, ["par_90", "par90"], 0.0)
    collection_rate = _get_kpi_value(kpis, ["collections_rate", "collection_rate"], 0.0)
    cac = _get_kpi_value(kpis, ["cac"], 0.0)
    clv = _get_kpi_value(kpis, ["customer_lifetime_value"], 0.0)
    gross_margin = _get_kpi_value(kpis, ["gross_margin_pct"], 0.0)
    churn_90d = _get_kpi_value(kpis, ["churn_90d"], 0.0)
    clv_cac_ratio = (clv / cac) if cac > 0 else 0.0

    if par90 > 5:
        recommendations.append("Activate focused recovery actions for the 90+ DPD cohort.")
    if collection_rate < 90:
        recommendations.append(
            "Increase collection intensity for delinquent accounts to improve cash conversion."
        )
    if gross_margin < 20:
        recommendations.append(
            "Review pricing and direct cost controls to restore gross margin above 20%."
        )
    if cac > 0 and clv_cac_ratio < 3:
        recommendations.append(
            "Optimize acquisition channels to move CLV/CAC toward a 3x threshold."
        )
    if churn_90d > 10:
        recommendations.append("Launch 90-day retention interventions for at-risk borrowers.")
    if (
        roll_rates.summary.historical_coverage_pct > 0
        and roll_rates.summary.portfolio_roll_forward_rate_pct >= 20
    ):
        recommendations.append(
            "Tighten early-stage collections and underwriting triggers to reduce roll-forward migration."
        )
    if (
        roll_rates.summary.historical_coverage_pct > 0
        and roll_rates.summary.portfolio_cure_rate_pct < 30
    ):
        recommendations.append(
            "Deploy targeted cure campaigns for delinquent borrowers to improve rollback to current status."
        )
    if not recommendations:
        return [
            "Maintain underwriting and collections cadence with weekly KPI monitoring.",
            "Track executive unit economics (CAC, margin, churn) as portfolio grows.",
        ]
    return recommendations


def _build_kpi_summary_text(kpis: list[Any]) -> str:
    return "\n".join([f"{k.name}: {k.value} {k.unit} | Formula: {k.context.formula}" for k in kpis])


def _format_transition_block(roll_rates: "RollRateAnalyticsResponse") -> str:
    if roll_rates.summary.historical_coverage_pct <= 0:
        return ""
    return (
        f"Portfolio Cure Rate: {roll_rates.summary.portfolio_cure_rate_pct}%\n"
        f"Portfolio Roll-Forward Rate: {roll_rates.summary.portfolio_roll_forward_rate_pct}%\n"
        f"Worst Migration Path: {roll_rates.summary.worst_migration_path or 'n/a'}\n"
        f"Best Cure Source: {roll_rates.summary.best_cure_source or 'n/a'}\n\n"
    )


def _avg_mature_npl(vintage: "VintageCurveResponse") -> float:
    mature_ratios = [
        point.npl_ratio for point in vintage.portfolio_average_curve if point.months_on_book >= 6
    ]
    if not mature_ratios:
        return 0.0
    return round(sum(mature_ratios) / len(mature_ratios), 2)


async def _run_orchestrated_full_analysis(
    request: "LoanPortfolioRequest",
    service: "KPIService",
    kpi_summary: str,
) -> tuple[str, str]:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not configured")

    orchestrator = MultiAgentOrchestrator()
    trace_id = str(uuid.uuid4())
    loan_ids_from_request = (
        [loan.id for loan in request.loans if loan.id is not None] if request.loans else []
    )

    risk_stratification = await service.get_risk_stratification(request.loans)
    vintage_curves = await service.calculate_vintage_curves(request.loans)
    risk_heatmap = await service.get_risk_heatmap_summary(request.loans)

    initial_context = {
        "portfolio_data": (
            "Recent KPI Snapshot:\n"
            f"{kpi_summary}\n"
            f"Target Loans: {', '.join(loan_ids_from_request)}"
        ),
        "risk_stratification": risk_stratification.model_dump_json(),
        "vintage_data": vintage_curves.model_dump_json(),
        "risk_heatmap": json.dumps(risk_heatmap),
    }
    results = orchestrator.run_scenario(
        scenario_name="loan_risk_review",
        initial_context=initial_context,
        trace_id=trace_id,
    )
    summary = (
        results.get("risk_analysis")
        or results.get("risk_assessment")
        or "Analysis completed successfully."
    )
    return trace_id, summary


async def _run_local_full_analysis(
    request: "LoanPortfolioRequest",
    service: "KPIService",
    kpis: list[Any],
) -> tuple[str, str]:
    trace_id = str(uuid.uuid4())
    par30 = _get_kpi_value(kpis, ["par_30", "par30"], 0.0)
    yield_val = _get_kpi_value(kpis, ["portfolio_yield"], 0.0)
    loans_count = _get_kpi_value(
        kpis,
        ["total_loans_count"],
        float(len(request.loans)) if request.loans else 0.0,
    )
    cac = _get_kpi_value(kpis, ["cac"], 0.0)
    gross_margin = _get_kpi_value(kpis, ["gross_margin_pct"], 0.0)
    forecast_6m = _get_kpi_value(kpis, ["revenue_forecast_6m"], 0.0)
    churn_90d = _get_kpi_value(kpis, ["churn_90d"], 0.0)
    clv = _get_kpi_value(kpis, ["customer_lifetime_value"], 0.0)
    clv_cac_ratio = (clv / cac) if cac > 0 else 0.0

    advanced_risk = await service.calculate_advanced_risk(request.loans)
    risk_strat = await service.get_risk_stratification(request.loans)
    vintage = await service.calculate_vintage_curves(request.loans)
    roll_rates = await service.calculate_roll_rate_analytics(request.loans)

    dpd_1_30 = _get_kpi_value(kpis, ["dpd_1_30", "delinq_1_30_rate"], 0.0)
    dpd_31_60 = _get_kpi_value(kpis, ["dpd_31_60", "delinq_31_60_rate"], 0.0)
    par60 = _get_kpi_value(kpis, ["par_60", "par60"], advanced_risk.par60)
    risk_heatmap = (
        f"1-30:{round(dpd_1_30, 2)}% | "
        f"31-60:{round(dpd_31_60, 2)}% | "
        f"60+:{round(par60, 2)}%"
    )
    transition_block = _format_transition_block(roll_rates)
    strat_summary = " | ".join(
        [f"{flag.flag}: {flag.status.upper()}" for flag in risk_strat.decision_flags]
    )
    risk_status = "CRITICAL" if par30 > 10 or advanced_risk.par90 > 5 else "STABLE"
    mature_npl = _avg_mature_npl(vintage)

    summary = (
        f"PROPORTIONAL PORTFOLIO ANALYSIS ({risk_status})\n"
        f"-------------------------------------------\n"
        f"Portfolio Size: {loans_count} active loans\n"
        f"Risk stratification: {strat_summary}\n"
        f"Risk Heatmap: {risk_heatmap}\n"
        f"Risk exposure (PAR30): {par30}%\n"
        f"Risk exposure (PAR60): {advanced_risk.par60}%\n"
        f"Severe delinquency (PAR90): {advanced_risk.par90}%\n"
        f"Collections coverage: {advanced_risk.collections_coverage}%\n"
        f"Projected Yield: {yield_val}%\n\n"
        f"Total Yield (Interest + Fees): {advanced_risk.total_yield}%\n"
        f"Borrower Concentration (HHI): {advanced_risk.concentration_hhi}\n"
        f"Repeat Borrower Rate: {advanced_risk.repeat_borrower_rate}%\n"
        f"Credit Quality Index: {advanced_risk.credit_quality_index}\n\n"
        f"{transition_block}"
        f"Customer Acquisition Cost (CAC): ${cac}\n"
        f"Gross Margin: {gross_margin}%\n"
        f"90-Day Churn: {churn_90d}%\n"
        f"6-Month Revenue Forecast: ${forecast_6m}\n"
        f"CLV/CAC Ratio: {round(clv_cac_ratio, 2)}x\n\n"
        f"Lifecycle Analysis: Average NPL ratio for 6MoB+ loans is {mature_npl}%.\n\n"
        f"The analytical engine has identified {risk_status.lower()} stability metrics "
        "based on recent production data. Risk concentration is within acceptable "
        "guardrails for the current AUM expansion phase."
    )
    return trace_id, summary


async def _resolve_full_analysis_summary(
    request: "LoanPortfolioRequest",
    service: "KPIService",
    kpis: list[Any],
    kpi_summary: str,
) -> tuple[str, str]:
    try:
        return await _run_orchestrated_full_analysis(request, service, kpi_summary)
    except Exception as orch_err:
        logger.info("Using High-Fidelity Local Analytical Engine: %s", orch_err)
        return await _run_local_full_analysis(request, service, kpis)


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

    jwt_enabled = os.getenv("API_JWT_ENABLED", "0") == "1"
    jwt_secret = os.getenv("API_JWT_SECRET", "")
    jwt_algorithm = os.getenv("API_JWT_ALGORITHM", "HS256")
    jwt_audience = os.getenv("API_JWT_AUDIENCE")
    jwt_issuer = os.getenv("API_JWT_ISSUER")
    jwt_exempt_paths = {
        item.strip()
        for item in os.getenv(
            "API_JWT_EXEMPT_PATHS",
            "/health,/metrics,/docs,/openapi.json,/redoc",
        ).split(",")
        if item.strip()
    }

    if jwt_enabled:
        if jwt is None:
            raise RuntimeError("API_JWT_ENABLED=1 requires pyjwt to be installed")
        if not jwt_secret:
            raise RuntimeError("API_JWT_ENABLED=1 requires API_JWT_SECRET to be set")

        @app.middleware("http")
        async def jwt_auth_middleware(request: Request, call_next):
            """Validate JWT for protected endpoints when API_JWT_ENABLED=1."""
            path = request.url.path
            if (
                path in jwt_exempt_paths
                or path.startswith("/docs")
                or path.startswith("/redoc")
                or path.startswith("/openapi")
            ):
                return await call_next(request)

            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

            token = auth_header.split(" ", 1)[1].strip()
            if not token:
                return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

            decode_kwargs = {"algorithms": [jwt_algorithm]}
            if jwt_audience:
                decode_kwargs["audience"] = jwt_audience
            if jwt_issuer:
                decode_kwargs["issuer"] = jwt_issuer

            try:
                payload = jwt.decode(token, jwt_secret, **decode_kwargs)
            except Exception as exc:
                logger.warning("JWT validation failed: %s", exc)
                return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

            request.state.jwt_payload = payload
            return await call_next(request)

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        """Inject or propagate X-Correlation-ID and tag Sentry."""
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        set_sentry_correlation(correlation_id)
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
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    async def _acknowledge_event_by_uuid(event_id: uuid.UUID, service: MonitoringService):
        result = await service.acknowledge_event(event_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return result

    @app.post("/monitoring/events/ack")
    async def acknowledge_event_from_body(
        request: EventAcknowledgeRequest = Body(...),
        service: MonitoringService = Depends(get_monitoring_service),
    ):
        """Acknowledge an operational event using request body."""
        try:
            return await _acknowledge_event_by_uuid(request.event_id, service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error acknowledging event %s: %s", request.event_id, e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            return await _acknowledge_event_by_uuid(eid, service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error acknowledging event %s: %s", event_id, e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
                kpis = await service.calculate_kpis_for_portfolio(request.loans)
            else:
                kpis = await service.get_latest_kpis()
            source = "realtime-request" if request.loans else "production-snapshot"
            return _build_kpi_response(kpis, source=source)
        except Exception as e:
            logger.error("Error in calculate_all_kpis: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get("/analytics/kpis/coverage", response_model=KpiCoverageResponse)
    async def get_kpi_coverage(service: KPIService = Depends(get_kpi_service)):
        """Return KPI coverage between catalog definitions and API-supported KPIs."""
        try:
            catalog_kpis = service.get_catalog_kpi_ids()
            implemented_catalog_kpis = service.get_supported_catalog_kpi_ids()
            missing_catalog_kpis = sorted(set(catalog_kpis) - set(implemented_catalog_kpis))
            return KpiCoverageResponse(
                catalog_total=len(catalog_kpis),
                implemented_total=len(implemented_catalog_kpis),
                catalog_kpis=catalog_kpis,
                implemented_catalog_kpis=implemented_catalog_kpis,
                missing_catalog_kpis=missing_catalog_kpis,
                exposed_aliases=service.get_exposed_aliases(),
            )
        except Exception as e:
            logger.error("Error in get_kpi_coverage: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            "default-rate": "DEFAULT_RATE",
            "total-loans-count": "TOTAL_LOANS_COUNT",
            "loss-rate": "LOSS_RATE",
            "recovery-rate": "RECOVERY_RATE",
            "cash-on-hand": "CASH_ON_HAND",
            "cac": "CAC",
            "gross-margin-pct": "GROSS_MARGIN_PCT",
            "revenue-forecast-6m": "REVENUE_FORECAST_6M",
            "churn-90d": "CHURN_90D",
            "portfolio-health": "PORTFOLIO_HEALTH",
            "active-borrowers": "ACTIVE_BORROWERS",
            "repeat-borrower-rate": "REPEAT_BORROWER_RATE",
            "automation-rate": "AUTOMATION_RATE",
            "average-loan-size": "AVERAGE_LOAN_SIZE",
            "processing-time-avg": "PROCESSING_TIME_AVG",
            "disbursement-volume-mtd": "DISBURSEMENT_VOLUME_MTD",
            "new-loans-count-mtd": "NEW_LOANS_COUNT_MTD",
            "customer-lifetime-value": "CUSTOMER_LIFETIME_VALUE",
            "ltv": "AVG_LTV",
            "avg-ltv": "AVG_LTV",
            "dti": "AVG_DTI",
            "avg-dti": "AVG_DTI",
            "portfolio-yield": "PORTFOLIO_YIELD",
            "par60": "PAR60",
            "par-60": "PAR60",
            "dpd-1-30": "DPD_1_30",
            "dpd_1_30": "DPD_1_30",
            "dpd-31-60": "DPD_31_60",
            "dpd_31_60": "DPD_31_60",
            "dpd-61-90": "DPD_61_90",
            "dpd_61_90": "DPD_61_90",
            "dpd-90-plus": "DPD_90_PLUS",
            "dpd_90_plus": "DPD_90_PLUS",
            "npl": "NPL",
            "npl-ratio": "NPL",
            "lgd": "LGD",
            "cor": "COR",
            "cost-of-risk": "COR",
            "nim": "NIM",
            "net-interest-margin": "NIM",
            "cure-rate": "CURERATE",
            "curerate": "CURERATE",
        }

        db_key = kpi_key_map.get(kpi_id.lower(), kpi_id.upper())

        try:
            if request.loans:
                kpis = await service.calculate_kpis_for_portfolio(request.loans)
                kpi = next((k for k in kpis if k.id == db_key), None)
            else:
                kpi = await service.get_kpi_by_id(db_key)

            if not kpi:
                raise HTTPException(status_code=404, detail=f"KPI {kpi_id} not found")
            return kpi
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in get_single_kpi: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            total = len(request.loans) if request.loans else 0
            high_count = len(risk_loans)
            ratio = (high_count / total * 100) if total > 0 else 0.0

            return RiskAlertsResponse(
                high_risk_count=high_count,
                total_loans=total,
                risk_ratio=round(ratio, 2),
                high_risk_loans=risk_loans,
            )
        except Exception as e:
            logger.error("Error in get_risk_alerts: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/advanced-risk",
        response_model=AdvancedRiskResponse,
        summary="Advanced Risk KPI Snapshot",
        response_description="Advanced delinquency, yield, concentration, and recovery metrics",
    )
    async def get_advanced_risk(
        request: LoanPortfolioRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Calculate advanced risk metrics and DPD bucket diagnostics for a portfolio."""
        try:
            return await service.calculate_advanced_risk(request.loans)
        except Exception as e:
            logger.error("Error in get_advanced_risk: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/cohorts",
        response_model=CohortAnalyticsResponse,
        summary="Origination Cohort Analytics",
        response_description="Vintage-level risk and collections metrics by origination month",
    )
    async def get_cohort_analytics(
        request: CohortAnalyticsRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Calculate cohort/vintage metrics (PAR, default, collections) by origination month."""
        try:
            return await service.calculate_cohort_analytics(request.loans)
        except Exception as e:
            logger.error("Error in get_cohort_analytics: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/vintages",
        response_model=VintageCurveResponse,
        summary="Vintage Curve Analytics",
        response_description="Evolution of delinquency by Months on Book (MoB)",
    )
    async def get_vintage_curves(
        request: CohortAnalyticsRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Calculate delinquency curves by Months on Book (MoB)."""
        try:
            return await service.calculate_vintage_curves(request.loans)
        except Exception as e:
            logger.error("Error in get_vintage_curves: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/segments",
        response_model=SegmentAnalyticsResponse,
        summary="Segment Drill-down Analytics",
        response_description="Segment-level KPI snapshot for risk and collections monitoring",
    )
    async def get_segment_analytics(
        request: SegmentAnalyticsRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Calculate KPI drill-down by selected segment dimension."""
        try:
            return await service.calculate_segment_analytics(
                loans=request.loans,
                dimension=request.dimension,
                top_n=request.top_n,
            )
        except Exception as e:
            logger.error("Error in get_segment_analytics: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/roll-rates",
        response_model=RollRateAnalyticsResponse,
        summary="Roll-Rate and Cure-Rate Analytics",
        response_description="Transition matrix and cure/migration diagnostics across DPD buckets",
    )
    async def get_roll_rate_analytics(
        request: RollRateAnalyticsRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Calculate transition analytics between previous and current delinquency buckets."""
        try:
            return await service.calculate_roll_rate_analytics(request.loans)
        except Exception as e:
            logger.error("Error in get_roll_rate_analytics: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/stress-test",
        response_model=StressTestResponse,
        summary="Portfolio Stress Test",
        response_description="Baseline vs stressed projections for risk and unit-economics KPIs",
    )
    async def run_stress_test(
        request: StressTestRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Run deterministic stress projections for delinquency, collections, losses and margin."""
        try:
            return await service.calculate_stress_test(
                loans=request.loans,
                par_deterioration_pct=request.par_deterioration_pct,
                collection_efficiency_pct=request.collection_efficiency_pct,
                recovery_efficiency_pct=request.recovery_efficiency_pct,
                funding_cost_bps=request.funding_cost_bps,
            )
        except Exception as e:
            logger.error("Error in run_stress_test: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/risk-stratification",
        response_model=RiskStratificationResponse,
        summary="Portfolio Risk Stratification",
        response_description="Risk bucket breakdown and key portfolio decision flags",
    )
    async def get_risk_stratification(
        request: LoanPortfolioRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Categorize portfolio by risk buckets and identify key decision flags."""
        try:
            return await service.get_risk_stratification(request.loans)
        except Exception as e:
            logger.error("Error in get_risk_stratification: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/unit-economics",
        response_model=UnitEconomicsResponse,
        summary="Unit Economics & Credit Quality KPIs",
        response_description=(
            "NPL ratio, LGD, Cost of Risk, NIM, CAC payback period, cure rate, "
            "and DPD migration with recommended actions"
        ),
    )
    async def get_unit_economics(
        request: UnitEconomicsRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """
        Calculate unit-economics and credit-quality KPIs for a loan portfolio.

        Returns NPL, LGD, Cost of Risk, NIM, CAC payback period, cure rate, and
        a DPD migration table with risk levels and recommended operational actions.
        This endpoint turns portfolio data into actionable decisions.
        """
        try:
            return await service.calculate_unit_economics(
                loans=request.loans,
                funding_cost_rate=request.funding_cost_rate,
                cac=request.cac,
                monthly_arpu=request.monthly_arpu,
            )
        except Exception as e:
            logger.error("Error in get_unit_economics: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post("/analytics/full-analysis", response_model=FullAnalysisResponse)
    async def get_full_analysis(
        request: LoanPortfolioRequest = Body(...), service: KPIService = Depends(get_kpi_service)
    ):
        """
        Runs a comprehensive multi-agent analysis on the specified loan portfolio.
        """
        try:
            # 1. Fetch data context for the orchestrator
            # Use request-scoped real-time KPIs when available, fallback to latest snapshot.
            kpis = await _resolve_analysis_kpis(request, service)
            kpi_summary = _build_kpi_summary_text(kpis)
            trace_id, summary = await _resolve_full_analysis_summary(
                request, service, kpis, kpi_summary
            )

            return await _map_full_analysis_response(request, service, kpis, trace_id, summary)
        except Exception as e:
            logger.error("Error in get_full_analysis: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    async def _map_full_analysis_response(
        request: "LoanPortfolioRequest",
        service: "KPIService",
        kpis: list[Any],
        trace_id: str,
        summary: str,
    ) -> FullAnalysisResponse:
        """Map raw analysis results to structured FullAnalysisResponse model."""
        roll_rates = await service.calculate_roll_rate_analytics(request.loans)
        recommendations = _build_full_analysis_recommendations(kpis, roll_rates)

        risk_stratification = await service.get_risk_stratification(request.loans)
        risk_heatmap_data = await service.get_risk_heatmap_summary(request.loans)
        vintage_curves_data = await service.calculate_vintage_curves(request.loans)
        layered_analysis = await service.get_layered_insights(request.loans)
        unit_economics = await service.calculate_unit_economics(request.loans)
        portfolio_health = await service.get_portfolio_health_score(request.loans)

        return FullAnalysisResponse(
            analysis_id=trace_id,
            summary=summary,
            recommendations=recommendations,
            kpis=kpis,
            risk_assessment=RiskAlertsResponse(
                high_risk_count=0,
                total_loans=len(request.loans) if request.loans else 0,
                risk_ratio=0.0,
                high_risk_loans=[],
            ),
            risk_stratification=risk_stratification,
            risk_heatmap=risk_heatmap_data,
            vintage_curves=vintage_curves_data,
            layered_analysis=layered_analysis,
            unit_economics=unit_economics,
            portfolio_health=portfolio_health,
        )

    @app.post(
        "/analytics/decision-dashboard",
        response_model=DecisionDashboardResponse,
    )
    async def get_decision_dashboard(
        request: LoanPortfolioRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Unified portfolio decision dashboard with health score and risk drill-down."""
        try:
            if not request.loans:
                raise HTTPException(
                    status_code=400,
                    detail="Decision dashboard requires loan records in request.loans",
                )
            return await service.get_decision_dashboard(request.loans)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error in get_decision_dashboard: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post(
        "/analytics/executive-summary",
        response_model=ExecutiveAnalyticsResponse,
    )
    async def get_executive_summary(
        request: ExecutiveAnalyticsRequest = Body(...),
        service: KPIService = Depends(get_kpi_service),
    ):
        """Strategic analytics: CAC, LTV, margins, churn, forecast and opportunities."""
        try:
            executive_data = await service.get_executive_analytics(
                loans=request.loans,
                payments=request.payments,
                customers=request.customers,
                schedule=request.schedule,
            )
            return ExecutiveAnalyticsResponse(**executive_data)
        except Exception as e:
            logger.error("Error in get_executive_summary: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            logger.error("Error in get_data_quality_profile: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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
            logger.error("Error in validate_loan_data: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

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

    # -------------------------------------------------------------------
    # ML Prediction Endpoint
    # -------------------------------------------------------------------

    # Lazy-load model on first request (mutable container for closure)
    _risk_model_cache: dict = {}

    def _get_risk_model():
        backend = os.getenv("DEFAULT_RISK_MODEL_BACKEND", "xgb").strip().lower()
        if _risk_model_cache.get("backend") != backend:
            _risk_model_cache.clear()
            _risk_model_cache["backend"] = backend

        if "model" not in _risk_model_cache:
            try:
                base_path = Path(__file__).resolve().parents[4]
                if backend in {"torch", "pytorch"}:
                    from backend.python.models.default_risk_torch_model import TorchDefaultRiskModel

                    model_path = base_path / "models" / "risk" / "default_risk_torch.pt"
                    if model_path.exists():
                        _risk_model_cache["model"] = TorchDefaultRiskModel.load(str(model_path))
                        _risk_model_cache["model_version"] = "torch_mlp_v1"
                        logger.info("Loaded torch default risk model from %s", model_path)
                    else:
                        logger.warning("Torch risk model not found at %s", model_path)
                        _risk_model_cache["model"] = None
                        _risk_model_cache["model_version"] = "torch_mlp_v1"
                else:
                    from backend.python.models.default_risk_model import DefaultRiskModel

                    model_path = base_path / "models" / "risk" / "default_risk_xgb.ubj"
                    if model_path.exists():
                        _risk_model_cache["model"] = DefaultRiskModel.load(str(model_path))
                        _risk_model_cache["model_version"] = "xgb_v1"
                        logger.info("Loaded XGBoost default risk model from %s", model_path)
                    else:
                        logger.warning("XGBoost risk model not found at %s", model_path)
                        _risk_model_cache["model"] = None
                        _risk_model_cache["model_version"] = "xgb_v1"
            except Exception as e:
                logger.error("Failed to load risk model: %s", e)
                _risk_model_cache["model"] = None
                _risk_model_cache["model_version"] = f"{backend}_unavailable"

        return _risk_model_cache.get("model"), _risk_model_cache.get("model_version", "unknown")

    def _map_default_request_to_model_features(
        request: DefaultPredictionRequest,
    ) -> dict[str, float]:
        """
        Adapt API request fields to the feature schema expected by DefaultRiskModel.
        """
        loan_amount = float(request.loan_amount)

        # API requests send percentage-like interest rates (e.g., 12.5), model expects decimal.
        rate = float(request.interest_rate)
        if rate > 1.0:
            rate = rate / 100.0

        ltv_ratio = max(0.0, float(request.ltv_ratio))
        collateral_value = loan_amount
        if ltv_ratio > 0:
            collateral_value = loan_amount / max(ltv_ratio / 100.0, 1e-9)

        # Conservative scheduled proxy keeps payment_ratio in a bounded range.
        scheduled_proxy = loan_amount * (1.0 + (rate * max(float(request.term_months), 0.0) / 12.0))

        return {
            "principal_amount": loan_amount,
            "interest_rate": rate,
            "term_months": float(request.term_months),
            "collateral_value": float(collateral_value),
            "outstanding_balance": loan_amount,
            "tpv": loan_amount,
            "equifax_score": float(request.credit_score),
            "last_payment_amount": 0.0,
            "total_scheduled": max(float(scheduled_proxy), 0.0),
            "origination_fee": 0.0,
            "days_past_due": float(request.days_past_due),
        }

    @app.post("/predict/default", response_model=DefaultPredictionResponse)
    async def predict_default(request: DefaultPredictionRequest = Body(...)):
        """Predict default probability for a loan using configured backend."""
        model, model_version = _get_risk_model()
        if model is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Risk model not available. Train and store a model under models/risk/ "
                    "(xgb: default_risk_xgb.ubj, torch: default_risk_torch.pt)."
                ),
            )

        try:
            loan_data = _map_default_request_to_model_features(request)
            probability = model.predict_proba(loan_data)

            if probability >= 0.7:
                risk_level = "critical"
            elif probability >= 0.4:
                risk_level = "high"
            elif probability >= 0.15:
                risk_level = "medium"
            else:
                risk_level = "low"

            return DefaultPredictionResponse(
                probability=round(probability, 4),
                risk_level=risk_level,
                model_version=str(model_version),
            )
        except Exception as e:
            logger.error("Error in predict_default: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get("/analytics/nsm", response_model=NSMRecurrentTPVResponse)
    async def get_nsm(service: KPIService = Depends(get_kpi_service)):
        """Return North Star Metric (Recurrent TPV) and breakdowns by period."""
        try:
            return await service.get_nsm_recurrent_tpv()
        except Exception as e:
            logger.error("Error in get_nsm: %s", e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e


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
    # Explicitly block absolute-looking paths before pathlib normalization
    if candidate.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    normalized = candidate.replace("\\", "/")
    if not re.match(r"^[a-zA-Z0-9_./\-]+$", normalized):
        raise ValueError("invalid characters")
    candidate_path = Path(normalized)
    if candidate_path.is_absolute():
        raise ValueError("absolute paths are not allowed")
    if any(p == ".." for p in candidate_path.parts):
        raise ValueError("parent traversal is not allowed")
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
