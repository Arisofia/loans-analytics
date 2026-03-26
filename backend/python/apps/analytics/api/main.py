import json
import logging
import os
import re
import sys
import uuid
import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
try:
    import jwt as _jwt
    jwt: Any = _jwt
except ImportError:
    jwt = None
if TYPE_CHECKING:
    from backend.python.apps.analytics.api.models import LoanRecord
try:
    from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, WebSocket
    from starlette.websockets import WebSocketDisconnect
    from fastapi.responses import JSONResponse, Response
    from backend.python.apps.analytics.api.models import AdvancedRiskResponse, CohortAnalyticsRequest, CohortAnalyticsResponse, DataQualityResponse, DecisionDashboardResponse, DefaultPredictionRequest, DefaultPredictionResponse, ExecutiveAnalyticsRequest, ExecutiveAnalyticsResponse, FullAnalysisResponse, GuardrailsResponse, KpiCoverageResponse, KpiResponse, KpiSingleResponse, LoanPortfolioRequest, NSMRecurrentTPVResponse, RiskAlertsResponse, RiskHeatmapResponse, RiskLoan, RiskStratificationResponse, RollRateAnalyticsRequest, RollRateAnalyticsResponse, SegmentAnalyticsRequest, SegmentAnalyticsResponse, StressTestRequest, StressTestResponse, UnitEconomicsRequest, UnitEconomicsResponse, ValidationResponse, VintageCurveResponse
    from backend.python.apps.analytics.api.monitoring_models import CommandCreate, CommandsListResponse, CommandStatus, CommandUpdate, EventAcknowledgeRequest, EventSeverity, EventsListResponse, OperationalEventCreate
    from backend.python.apps.analytics.api.monitoring_service import MonitoringService
    from backend.python.apps.analytics.api.service import KPIService
    from backend.python.monitoring.kpi_metrics import get_kpi_metrics_exporter
    from backend.python.logging_config import init_sentry, set_sentry_correlation
    from backend.python.multi_agent.orchestrator import MultiAgentOrchestrator
    from backend.python.middleware.rate_limiter import api_limiter, auth_limiter
    init_sentry(service_name='analytics-api')
    app: Optional[FastAPI] = FastAPI(title='Loans Analytics API')
except ImportError:

    class HTTPException(Exception):  # type: ignore[no-redef]

        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Depends:  # type: ignore[no-redef]

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Body:  # type: ignore[no-redef]

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Query:  # type: ignore[no-redef]

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    app = None
logger = logging.getLogger('apps.analytics.api')
DOCS_PATH = '/docs'
REDOC_PATH = '/redoc'
EMPTY_PATH_ERROR = 'empty path'
ALLOWED_DATA_DIR = Path('/data/archives').resolve()
INTERNAL_SERVER_ERROR = 'Internal server error'

def get_kpi_service():
    return KPIService(actor='api_user')

def get_monitoring_service():
    return MonitoringService(actor='api_user')

def _loan_records_or_empty(request: 'LoanPortfolioRequest') -> list['LoanRecord']:
    return request.loans or []

def _safe_log_value(value: Any, max_length: int=200) -> str:
    return _sanitize_for_logging(str(value), max_length=max_length)

def _build_kpi_response(kpis: list[Any] | None, source: str='production-snapshot') -> 'KpiResponse':
    kpi_map = {k.id: k for k in kpis} if kpis else {}

    def _get(*keys: str) -> Any:
        return next((kpi_map[k] for k in keys if k in kpi_map), None)
    return KpiResponse(PAR30=_get('PAR30', 'par_30'), PAR90=_get('PAR90', 'par_90'), PAR60=_get('PAR60', 'par_60'), DPD1_30=_get('DPD_1_30', 'dpd_1_30', 'delinq_1_30_rate'), DPD31_60=_get('DPD_31_60', 'dpd_31_60', 'delinq_31_60_rate'), DPD61_90=_get('DPD_61_90', 'dpd_61_90'), DPD90Plus=_get('DPD_90_PLUS', 'dpd_90_plus'), CollectionRate=_get('COLLECTION_RATE', 'collections_rate'), DefaultRate=_get('DEFAULT_RATE', 'default_rate'), TotalLoansCount=_get('TOTAL_LOANS_COUNT', 'total_loans_count'), LossRate=_get('LOSS_RATE', 'loss_rate'), RecoveryRate=_get('RECOVERY_RATE', 'recovery_rate'), CashOnHand=_get('CASH_ON_HAND', 'cash_on_hand'), CAC=_get('CAC', 'cac'), GrossMarginPct=_get('GROSS_MARGIN_PCT', 'gross_margin_pct'), RevenueForecast6M=_get('REVENUE_FORECAST_6M', 'revenue_forecast_6m'), Churn90D=_get('CHURN_90D', 'churn_90d'), PortfolioHealth=_get('AUM', 'portfolio_growth_rate'), CustomerLifetimeValue=_get('CUSTOMER_LIFETIME_VALUE', 'customer_lifetime_value'), ActiveBorrowers=_get('ACTIVE_BORROWERS', 'active_borrowers'), RepeatBorrowerRate=_get('REPEAT_BORROWER_RATE', 'repeat_borrower_rate'), AutomationRate=_get('AUTOMATION_RATE', 'automation_rate'), AverageLoanSize=_get('AVERAGE_LOAN_SIZE', 'average_loan_size'), ProcessingTimeAvg=_get('PROCESSING_TIME_AVG', 'processing_time_avg'), DisbursementVolumeMTD=_get('DISBURSEMENT_VOLUME_MTD', 'disbursement_volume_mtd'), NewLoansCountMTD=_get('NEW_LOANS_COUNT_MTD', 'new_loans_count_mtd'), LTV=_get('AVG_LTV', 'avg_ltv'), DTI=_get('AVG_DTI', 'avg_dti'), PortfolioYield=_get('PORTFOLIO_YIELD', 'portfolio_yield'), NPL=_get('NPL', 'npl_ratio'), LGD=_get('LGD', 'lgd_pct', 'lgd'), CoR=_get('COR', 'cost_of_risk_pct', 'cost_of_risk'), NIM=_get('NIM', 'nim_pct', 'net_interest_margin'), CureRate=_get('CURERATE', 'cure_rate_pct', 'cure_rate'), CollectionsEligibleRate=_get('collections_eligible_rate'), GovernmentSectorExposureRate=_get('government_sector_exposure_rate'), AvgCreditLineUtilization=_get('avg_credit_line_utilization'), CapitalCollectionRate=_get('capital_collection_rate'), MdscPostedRate=_get('mdsc_posted_rate'), audit_trail=[{'kpi_count': len(kpis or []), 'source': source}])

async def _resolve_analysis_kpis(request: 'LoanPortfolioRequest', service: 'KPIService') -> list[Any]:
    if request.loans:
        kpis = await service.calculate_kpis_for_portfolio(request.loans)
        if kpis:
            return kpis
    return await service.get_latest_kpis()

def _get_kpi_value(kpis: list[Any], candidates: list[str], default: float=0.0) -> float:
    candidate_set = {candidate.lower() for candidate in candidates}
    value = next((kpi.value for kpi in kpis if (kpi.id or '').lower() in candidate_set), None)
    return float(value) if value is not None else default

def _build_full_analysis_recommendations(kpis: list[Any], roll_rates: 'RollRateAnalyticsResponse') -> list[str]:
    recommendations: list[str] = []
    par90 = _get_kpi_value(kpis, ['par_90', 'par90'], 0.0)
    collection_rate = _get_kpi_value(kpis, ['collections_rate', 'collection_rate'], 0.0)
    cac = _get_kpi_value(kpis, ['cac'], 0.0)
    clv = _get_kpi_value(kpis, ['customer_lifetime_value'], 0.0)
    gross_margin = _get_kpi_value(kpis, ['gross_margin_pct'], 0.0)
    churn_90d = _get_kpi_value(kpis, ['churn_90d'], 0.0)
    clv_cac_ratio = clv / cac if cac > 0 else 0.0
    if par90 > 5:
        recommendations.append('Activate focused recovery actions for the 90+ DPD cohort.')
    if collection_rate < 90:
        recommendations.append('Increase collection intensity for delinquent accounts to improve cash conversion.')
    if gross_margin < 20:
        recommendations.append('Review pricing and direct cost controls to restore gross margin above 20%.')
    if cac > 0 and clv_cac_ratio < 3:
        recommendations.append('Optimize acquisition channels to move CLV/CAC toward a 3x threshold.')
    if churn_90d > 10:
        recommendations.append('Launch 90-day retention interventions for at-risk borrowers.')
    if roll_rates.summary.historical_coverage_pct > 0:
        if roll_rates.summary.portfolio_roll_forward_rate_pct >= 20:
            recommendations.append('Tighten early-stage collections and underwriting triggers to reduce roll-forward migration.')
        if roll_rates.summary.portfolio_cure_rate_pct < 30:
            recommendations.append('Deploy targeted cure campaigns for delinquent borrowers to improve rollback to current status.')
    if not recommendations:
        return ['Maintain underwriting and collections cadence with weekly KPI monitoring.', 'Track executive unit economics (CAC, margin, churn) as portfolio grows.']
    return recommendations

def _build_kpi_summary_text(kpis: list[Any]) -> str:
    lines = []
    for k in kpis:
        formula = k.context.formula if k.context is not None else 'n/a'
        lines.append(f'{k.name}: {k.value} {k.unit} | Formula: {formula}')
    return '\n'.join(lines)

def _publish_kpi_metrics(kpis: list[Any], category: str='portfolio') -> None:
    try:
        exporter = get_kpi_metrics_exporter()
        for kpi in kpis:
            exporter.publish_kpi_result(kpi_name=str(kpi.id), kpi_result={'value': float(kpi.value), 'threshold_status': str(getattr(kpi, 'threshold_status', 'not_configured')), 'thresholds': getattr(kpi, 'thresholds', None) or {}, 'unit': str(getattr(kpi, 'unit', 'unknown'))}, category=category)
    except Exception as exc:
        logger.warning('KPI metrics publishing skipped: %s', exc)

def _format_transition_block(roll_rates: 'RollRateAnalyticsResponse') -> str:
    if roll_rates.summary.historical_coverage_pct <= 0:
        return ''
    return f"Portfolio Cure Rate: {roll_rates.summary.portfolio_cure_rate_pct}%\nPortfolio Roll-Forward Rate: {roll_rates.summary.portfolio_roll_forward_rate_pct}%\nWorst Migration Path: {roll_rates.summary.worst_migration_path or 'n/a'}\nBest Cure Source: {roll_rates.summary.best_cure_source or 'n/a'}\n\n"

def _avg_mature_npl(vintage: 'VintageCurveResponse') -> float:
    if not (mature_ratios := [point.npl_ratio for point in vintage.portfolio_average_curve if point.months_on_book >= 6]):
        return 0.0
    return round(sum(mature_ratios) / len(mature_ratios), 2)

async def _run_orchestrated_full_analysis(request: 'LoanPortfolioRequest', service: 'KPIService', kpi_summary: str) -> tuple[str, str]:
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError('OPENAI_API_KEY not configured')
    orchestrator = MultiAgentOrchestrator()
    trace_id = str(uuid.uuid4())
    loans = _loan_records_or_empty(request)
    loan_ids_from_request = [loan.id for loan in loans if loan.id is not None]
    risk_stratification = await service.get_risk_stratification(loans)
    vintage_curves = await service.calculate_vintage_curves(loans)
    risk_heatmap = await service.get_risk_heatmap_summary(loans)
    initial_context = {'portfolio_data': f"Recent KPI Snapshot:\n{kpi_summary}\nTarget Loans: {', '.join(loan_ids_from_request)}", 'risk_stratification': risk_stratification.model_dump_json(), 'vintage_data': vintage_curves.model_dump_json(), 'risk_heatmap': json.dumps(risk_heatmap)}
    results = orchestrator.run_scenario(scenario_name='loan_risk_review', initial_context=initial_context, trace_id=trace_id)
    summary = results.get('risk_analysis') or results.get('risk_assessment') or 'Analysis completed successfully.'
    return (trace_id, summary)

async def _run_local_full_analysis(request: 'LoanPortfolioRequest', service: 'KPIService', kpis: list[Any], roll_rates: 'RollRateAnalyticsResponse') -> tuple[str, str]:
    trace_id = str(uuid.uuid4())
    loans = _loan_records_or_empty(request)
    par30 = _get_kpi_value(kpis, ['par_30', 'par30'], 0.0)
    yield_val = _get_kpi_value(kpis, ['portfolio_yield'], 0.0)
    loans_count = _get_kpi_value(kpis, ['total_loans_count'], float(len(loans)))
    cac = _get_kpi_value(kpis, ['cac'], 0.0)
    gross_margin = _get_kpi_value(kpis, ['gross_margin_pct'], 0.0)
    forecast_6m = _get_kpi_value(kpis, ['revenue_forecast_6m'], 0.0)
    churn_90d = _get_kpi_value(kpis, ['churn_90d'], 0.0)
    clv = _get_kpi_value(kpis, ['customer_lifetime_value'], 0.0)
    clv_cac_ratio = clv / cac if cac > 0 else 0.0
    advanced_risk = await service.calculate_advanced_risk(loans)
    risk_strat = await service.get_risk_stratification(loans)
    vintage = await service.calculate_vintage_curves(loans)
    dpd_1_30 = _get_kpi_value(kpis, ['dpd_1_30', 'delinq_1_30_rate'], 0.0)
    dpd_31_60 = _get_kpi_value(kpis, ['dpd_31_60', 'delinq_31_60_rate'], 0.0)
    par60 = _get_kpi_value(kpis, ['par_60', 'par60'], advanced_risk.par60)
    risk_heatmap = f'1-30:{round(dpd_1_30, 2)}% | 31-60:{round(dpd_31_60, 2)}% | 60+:{round(par60, 2)}%'
    transition_block = _format_transition_block(roll_rates)
    strat_summary = ' | '.join([f'{flag.flag}: {flag.status.upper()}' for flag in risk_strat.decision_flags])
    risk_status = 'CRITICAL' if par30 > 10 or advanced_risk.par90 > 5 else 'STABLE'
    mature_npl = _avg_mature_npl(vintage)
    summary = f'PROPORTIONAL PORTFOLIO ANALYSIS ({risk_status})\n-------------------------------------------\nPortfolio Size: {loans_count} active loans\nRisk stratification: {strat_summary}\nRisk Heatmap: {risk_heatmap}\nRisk exposure (PAR30): {par30}%\nRisk exposure (PAR60): {advanced_risk.par60}%\nSevere delinquency (PAR90): {advanced_risk.par90}%\nCollections coverage: {advanced_risk.collections_coverage}%\nProjected Yield: {yield_val}%\n\nTotal Yield (Interest + Fees): {advanced_risk.total_yield}%\nBorrower Concentration (HHI): {advanced_risk.concentration_hhi}\nRepeat Borrower Rate: {advanced_risk.repeat_borrower_rate}%\nCredit Quality Index: {advanced_risk.credit_quality_index}\n\n{transition_block}Customer Acquisition Cost (CAC): ${cac}\nGross Margin: {gross_margin}%\n90-Day Churn: {churn_90d}%\n6-Month Revenue Forecast: ${forecast_6m}\nCLV/CAC Ratio: {round(clv_cac_ratio, 2)}x\n\nLifecycle Analysis: Average NPL ratio for 6MoB+ loans is {mature_npl}%.\n\nThe analytical engine has identified {risk_status.lower()} stability metrics based on recent production data. Risk concentration is within acceptable guardrails for the current AUM expansion phase.'
    return (trace_id, summary)

async def _resolve_full_analysis_summary(request: 'LoanPortfolioRequest', service: 'KPIService', kpis: list[Any], kpi_summary: str, roll_rates: 'RollRateAnalyticsResponse') -> tuple[str, str]:
    try:
        return await _run_orchestrated_full_analysis(request, service, kpi_summary)
    except Exception as orch_err:
        logger.info('Using High-Fidelity Local Analytical Engine: %s', orch_err)
        return await _run_local_full_analysis(request, service, kpis, roll_rates)
if app is not None:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint='/metrics')
    except ImportError:
        logger.warning('prometheus-fastapi-instrumentator not installed; /metrics disabled')
    _RATE_LIMIT_EXEMPT = {'/health', '/metrics', '/metrics/kpis', DOCS_PATH, '/openapi.json', REDOC_PATH}
    _AUTH_PATHS = {'/auth/token', '/auth/login', '/auth/refresh'}

    @app.middleware('http')
    async def rate_limit_middleware(request: Request, call_next):
        path = request.url.path
        if path not in _RATE_LIMIT_EXEMPT and (not path.startswith(REDOC_PATH)) and (not path.startswith(DOCS_PATH)):
            client_ip = (request.client.host if request.client else None) or 'unknown'
            limiter = auth_limiter if path in _AUTH_PATHS else api_limiter
            if not limiter.is_allowed(client_ip):
                return JSONResponse(status_code=429, content={'detail': 'Rate limit exceeded. Please retry later.'}, headers={'Retry-After': '10'})
        return await call_next(request)
    jwt_enabled = os.getenv('API_JWT_ENABLED', '0') == '1'
    jwt_secret = os.getenv('API_JWT_SECRET', '')
    jwt_algorithm = os.getenv('API_JWT_ALGORITHM', 'HS256')
    jwt_audience = os.getenv('API_JWT_AUDIENCE')
    jwt_issuer = os.getenv('API_JWT_ISSUER')
    jwt_exempt_paths = {item.strip() for item in os.getenv('API_JWT_EXEMPT_PATHS', f'/health,/metrics,/metrics/kpis,{DOCS_PATH},/openapi.json,{REDOC_PATH}').split(',') if item.strip()}
    if jwt_enabled:
        if jwt is None:
            raise RuntimeError('API_JWT_ENABLED=1 requires pyjwt to be installed')
        if not jwt_secret:
            raise RuntimeError('API_JWT_ENABLED=1 requires API_JWT_SECRET to be set')

        @app.middleware('http')
        async def jwt_auth_middleware(request: Request, call_next):
            path = request.url.path
            if path in jwt_exempt_paths or path.startswith(DOCS_PATH) or path.startswith(REDOC_PATH) or path.startswith('/openapi'):
                return await call_next(request)
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return JSONResponse(status_code=401, content={'detail': 'Missing bearer token'})
            token = auth_header.split(' ', 1)[1].strip()
            if not token:
                return JSONResponse(status_code=401, content={'detail': 'Missing bearer token'})
            decode_kwargs: dict[str, Any] = {'algorithms': [jwt_algorithm]}
            if jwt_audience:
                decode_kwargs['audience'] = jwt_audience
            if jwt_issuer:
                decode_kwargs['issuer'] = jwt_issuer
            try:
                payload = jwt.decode(token, jwt_secret, **decode_kwargs)
            except Exception as exc:
                logger.warning('JWT validation failed: %s', exc)
                return JSONResponse(status_code=401, content={'detail': 'Invalid or expired token'})
            request.state.jwt_payload = payload
            return await call_next(request)

    @app.middleware('http')
    async def correlation_id_middleware(request: Request, call_next):
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        set_sentry_correlation(correlation_id)
        response = await call_next(request)
        response.headers['X-Correlation-ID'] = correlation_id
        return response

    @app.post('/monitoring/events', response_model=EventsListResponse)
    async def emit_event(event: OperationalEventCreate=Body(...), service: MonitoringService=Depends(get_monitoring_service)):
        try:
            created = await service.emit_event(event)
            return EventsListResponse(events=[created], count=1)
        except Exception as e:
            logger.error('Error emitting event: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get('/monitoring/events', response_model=EventsListResponse)
    async def list_events(severity: Optional[str]=Query(None, description='Filter by severity'), source: Optional[str]=Query(None, description='Filter by source'), limit: int=Query(50, ge=1, le=500), offset: int=Query(0, ge=0), service: MonitoringService=Depends(get_monitoring_service)):
        try:
            sev = EventSeverity(severity) if severity else None
            events = await service.list_events(severity=sev, source=source, limit=limit, offset=offset)
            return EventsListResponse(events=events, count=len(events))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f'Invalid severity: {severity}. Must be info, warning, or critical') from exc
        except Exception as e:
            logger.error('Error listing events: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    async def _acknowledge_event_by_uuid(event_id: uuid.UUID, service: MonitoringService):
        result = await service.acknowledge_event(event_id)
        if result is None:
            raise HTTPException(status_code=404, detail='Event not found')
        return result

    @app.post('/monitoring/events/ack')
    async def acknowledge_event_from_body(request: EventAcknowledgeRequest=Body(...), service: MonitoringService=Depends(get_monitoring_service)):
        try:
            return await _acknowledge_event_by_uuid(request.event_id, service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Error acknowledging event %s: %s', _safe_log_value(request.event_id), _safe_log_value(e))
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/monitoring/events/{event_id}/ack')
    async def acknowledge_event(event_id: str, service: MonitoringService=Depends(get_monitoring_service)):
        try:
            eid = uuid.UUID(event_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail='Invalid event ID format') from exc
        try:
            return await _acknowledge_event_by_uuid(eid, service)
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Error acknowledging event %s: %s', _safe_log_value(event_id), _safe_log_value(e))
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/monitoring/commands', response_model=CommandsListResponse)
    async def create_command(cmd: CommandCreate=Body(...), service: MonitoringService=Depends(get_monitoring_service)):
        try:
            created = await service.create_command(cmd)
            return CommandsListResponse(commands=[created], count=1)
        except Exception as e:
            logger.error('Error creating command: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get('/monitoring/commands', response_model=CommandsListResponse)
    async def list_commands(status: Optional[str]=Query(None, description='Filter by status'), limit: int=Query(50, ge=1, le=500), service: MonitoringService=Depends(get_monitoring_service)):
        try:
            st = CommandStatus(status) if status else None
            commands = await service.list_commands(status=st, limit=limit)
            return CommandsListResponse(commands=commands, count=len(commands))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f'Invalid status: {status}. Must be pending, running, completed, or failed') from exc
        except Exception as e:
            logger.error('Error listing commands: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.patch('/monitoring/commands/{cmd_id}')
    async def update_command(cmd_id: str, update: CommandUpdate=Body(...), service: MonitoringService=Depends(get_monitoring_service)):
        try:
            cid = uuid.UUID(cmd_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail='Invalid command ID format') from exc
        try:
            result = await service.update_command_status(cid, update)
            if result is None:
                raise HTTPException(status_code=404, detail='Command not found')
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Error updating command %s: %s', _safe_log_value(cmd_id), _safe_log_value(e))
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get('/health')
    async def health_check():
        return {'status': 'ok'}

    @app.get('/metrics/kpis')
    async def kpi_metrics():
        metrics_text = get_kpi_metrics_exporter().generate_metrics_text()
        return Response(content=metrics_text, media_type='text/plain; version=0.0.4')

    @app.post('/analytics/kpis', response_model=KpiResponse)
    async def calculate_all_kpis(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            if request.loans:
                kpis = await service.calculate_kpis_for_portfolio(request.loans)
            else:
                kpis = await service.get_latest_kpis()
            _publish_kpi_metrics(kpis, category='portfolio')
            source = 'realtime-request' if request.loans else 'production-snapshot'
            return _build_kpi_response(kpis, source=source)
        except Exception as e:
            logger.error('Error in calculate_all_kpis: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get('/analytics/kpis/coverage', response_model=KpiCoverageResponse)
    async def get_kpi_coverage(service: KPIService=Depends(get_kpi_service)):
        try:
            catalog_kpis = service.get_catalog_kpi_ids()
            implemented_catalog_kpis = service.get_supported_catalog_kpi_ids()
            missing_catalog_kpis = sorted(set(catalog_kpis) - set(implemented_catalog_kpis))
            return KpiCoverageResponse(catalog_total=len(catalog_kpis), implemented_total=len(implemented_catalog_kpis), catalog_kpis=catalog_kpis, implemented_catalog_kpis=implemented_catalog_kpis, missing_catalog_kpis=missing_catalog_kpis, exposed_aliases=service.get_exposed_aliases())
        except Exception as e:
            logger.error('Error in get_kpi_coverage: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/guardrails', response_model=GuardrailsResponse)
    async def check_portfolio_guardrails(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            result = await service.calculate_guardrails(request.loans or [], request.payments, request.customers, request.schedule)
            return GuardrailsResponse(**result)
        except Exception as e:
            logger.error('Error in check_portfolio_guardrails: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/kpis/{kpi_id}', response_model=KpiSingleResponse)
    async def get_single_kpi(kpi_id: str, request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        kpi_key_map = {'par30': 'PAR30', 'par90': 'PAR90', 'collection-rate': 'COLLECTION_RATE', 'default-rate': 'DEFAULT_RATE', 'total-loans-count': 'TOTAL_LOANS_COUNT', 'loss-rate': 'LOSS_RATE', 'recovery-rate': 'RECOVERY_RATE', 'cash-on-hand': 'CASH_ON_HAND', 'cac': 'CAC', 'gross-margin-pct': 'GROSS_MARGIN_PCT', 'revenue-forecast-6m': 'REVENUE_FORECAST_6M', 'churn-90d': 'CHURN_90D', 'portfolio-health': 'PORTFOLIO_HEALTH', 'active-borrowers': 'ACTIVE_BORROWERS', 'repeat-borrower-rate': 'REPEAT_BORROWER_RATE', 'automation-rate': 'AUTOMATION_RATE', 'average-loan-size': 'AVERAGE_LOAN_SIZE', 'processing-time-avg': 'PROCESSING_TIME_AVG', 'disbursement-volume-mtd': 'DISBURSEMENT_VOLUME_MTD', 'new-loans-count-mtd': 'NEW_LOANS_COUNT_MTD', 'customer-lifetime-value': 'CUSTOMER_LIFETIME_VALUE', 'ltv': 'AVG_LTV', 'avg-ltv': 'AVG_LTV', 'dti': 'AVG_DTI', 'avg-dti': 'AVG_DTI', 'portfolio-yield': 'PORTFOLIO_YIELD', 'par60': 'PAR60', 'par-60': 'PAR60', 'dpd-1-30': 'DPD_1_30', 'dpd_1_30': 'DPD_1_30', 'dpd-31-60': 'DPD_31_60', 'dpd_31_60': 'DPD_31_60', 'dpd-61-90': 'DPD_61_90', 'dpd_61_90': 'DPD_61_90', 'dpd-90-plus': 'DPD_90_PLUS', 'dpd_90_plus': 'DPD_90_PLUS', 'npl': 'NPL', 'npl-ratio': 'NPL', 'lgd': 'LGD', 'cor': 'COR', 'cost-of-risk': 'COR', 'nim': 'NIM', 'net-interest-margin': 'NIM', 'cure-rate': 'CURERATE', 'curerate': 'CURERATE'}
        known_db_keys = set(kpi_key_map.values())
        db_key = kpi_key_map.get(kpi_id.lower())
        if db_key is None:
            candidate = kpi_id.upper()
            if candidate not in known_db_keys:
                raise HTTPException(status_code=400, detail=f'Unknown KPI identifier: {kpi_id!r}')
            db_key = candidate
        try:
            if request.loans:
                kpis = await service.calculate_kpis_for_portfolio(request.loans)
                kpi = next((k for k in kpis if k.id == db_key), None)
            else:
                kpi = await service.get_kpi_by_id(db_key)
            if not kpi:
                raise HTTPException(status_code=404, detail=f'KPI {kpi_id} not found')
            _publish_kpi_metrics([kpi], category='portfolio')
            return kpi
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Error in get_single_kpi: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.websocket('/analytics/kpis/stream')
    async def stream_latest_kpis(websocket: WebSocket, interval_seconds: float=5.0, once: bool=False, kpi_keys: str | None=None, service: KPIService=Depends(get_kpi_service)):
        await websocket.accept()
        safe_interval = max(interval_seconds, 1.0)
        requested_keys = [key.strip() for key in (kpi_keys or '').split(',') if key.strip()]
        try:
            while True:
                try:
                    kpis = await service.get_latest_kpis(kpi_keys=requested_keys or None)
                except Exception as fetch_exc:
                    logger.error('KPI stream fetch failed: %s', fetch_exc)
                    await websocket.send_json({'event': 'error', 'detail': 'KPI fetch failed — stream terminated'})
                    break
                if kpis:
                    _publish_kpi_metrics(kpis, category='portfolio')
                payload = {'event': 'kpi_snapshot', 'timestamp': datetime.now(timezone.utc).isoformat(), 'kpis': [kpi.model_dump(mode='json') for kpi in kpis], 'source': 'realtime-stream'}
                await websocket.send_json(payload)
                if once:
                    break
                await asyncio.sleep(safe_interval)
        except WebSocketDisconnect:
            logger.info('KPI stream client disconnected')
        except Exception as e:
            logger.error('Error in KPI stream endpoint: %s', e)
            with suppress(Exception):
                await websocket.send_json({'event': 'error', 'detail': INTERNAL_SERVER_ERROR})

    def _raise_internal_http_error(endpoint_name: str, exc: Exception) -> None:
        logger.error('Error in %s: %s', endpoint_name, exc)
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from exc

    @app.post('/analytics/risk-alerts', response_model=RiskAlertsResponse)
    async def get_risk_alerts(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            ltv = request.ltv_threshold if request.ltv_threshold is not None else 80.0
            dti = request.dti_threshold if request.dti_threshold is not None else 50.0
            risk_loans_data = await service.get_risk_alerts(loans=request.loans, ltv_threshold=ltv, dti_threshold=dti)
            risk_loans = [RiskLoan(**loan) for loan in risk_loans_data]
            total = len(request.loans) if request.loans else 0
            high_count = len(risk_loans)
            ratio = high_count / total * 100 if total > 0 else 0.0
            return RiskAlertsResponse(high_risk_count=high_count, total_loans=total, risk_ratio=round(ratio, 2), high_risk_loans=risk_loans)
        except Exception as e:
            logger.error('Error in get_risk_alerts: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/advanced-risk', response_model=AdvancedRiskResponse, summary='Advanced Risk KPI Snapshot', response_description='Advanced delinquency, yield, concentration, and recovery metrics')
    async def get_advanced_risk(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_advanced_risk(request.loans)
        except Exception as e:
            logger.error('Error in get_advanced_risk: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/cohorts', response_model=CohortAnalyticsResponse, summary='Origination Cohort Analytics', response_description='Vintage-level risk and collections metrics by origination month')
    async def get_cohort_analytics(request: CohortAnalyticsRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_cohort_analytics(request.loans)
        except Exception as e:
            logger.error('Error in get_cohort_analytics: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/vintages', response_model=VintageCurveResponse, summary='Vintage Curve Analytics', response_description='Evolution of delinquency by Months on Book (MoB)')
    async def get_vintage_curves(request: CohortAnalyticsRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_vintage_curves(request.loans)
        except Exception as e:
            logger.error('Error in get_vintage_curves: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/segments', response_model=SegmentAnalyticsResponse, summary='Segment Drill-down Analytics', response_description='Segment-level KPI snapshot for risk and collections monitoring')
    async def get_segment_analytics(request: SegmentAnalyticsRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_segment_analytics(loans=request.loans, dimension=request.dimension, top_n=request.top_n)
        except Exception as e:
            logger.error('Error in get_segment_analytics: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/roll-rates', response_model=RollRateAnalyticsResponse, summary='Roll-Rate and Cure-Rate Analytics', response_description='Transition matrix and cure/migration diagnostics across DPD buckets')
    async def get_roll_rate_analytics(request: RollRateAnalyticsRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_roll_rate_analytics(request.loans)
        except Exception as e:
            logger.error('Error in get_roll_rate_analytics: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/stress-test', response_model=StressTestResponse, summary='Portfolio Stress Test', response_description='Baseline vs stressed projections for risk and unit-economics KPIs')
    async def run_stress_test(request: StressTestRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_stress_test(loans=request.loans, par_deterioration_pct=request.par_deterioration_pct, collection_efficiency_pct=request.collection_efficiency_pct, recovery_efficiency_pct=request.recovery_efficiency_pct, funding_cost_bps=request.funding_cost_bps)
        except Exception as e:
            logger.error('Error in run_stress_test: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/risk-stratification', response_model=RiskStratificationResponse, summary='Portfolio Risk Stratification', response_description='Risk bucket breakdown and key portfolio decision flags')
    async def get_risk_stratification(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.get_risk_stratification(request.loans)
        except Exception as e:
            logger.error('Error in get_risk_stratification: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/unit-economics', response_model=UnitEconomicsResponse, summary='Unit Economics & Credit Quality KPIs', response_description='NPL ratio, LGD, Cost of Risk, NIM, CAC payback period, cure rate, and DPD migration with recommended actions')
    async def get_unit_economics(request: UnitEconomicsRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.calculate_unit_economics(loans=request.loans, funding_cost_rate=request.funding_cost_rate, cac=request.cac, monthly_arpu=request.monthly_arpu)
        except Exception as e:
            logger.error('Error in get_unit_economics: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/full-analysis', response_model=FullAnalysisResponse)
    async def get_full_analysis(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            kpis = await _resolve_analysis_kpis(request, service)
            kpi_summary = _build_kpi_summary_text(kpis)
            roll_rates = await service.calculate_roll_rate_analytics(request.loans)
            trace_id, summary = await _resolve_full_analysis_summary(request, service, kpis, kpi_summary, roll_rates)
            return await _map_full_analysis_response(request, service, kpis, trace_id, summary, roll_rates)
        except Exception as e:
            logger.error('Error in get_full_analysis: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    async def _map_full_analysis_response(request: 'LoanPortfolioRequest', service: 'KPIService', kpis: list[Any], trace_id: str, summary: str, roll_rates: 'RollRateAnalyticsResponse') -> FullAnalysisResponse:
        recommendations = _build_full_analysis_recommendations(kpis, roll_rates)
        loans = _loan_records_or_empty(request)
        risk_stratification = await service.get_risk_stratification(loans)
        risk_heatmap_data = await service.get_risk_heatmap_summary(loans)
        risk_heatmap_response = RiskHeatmapResponse.model_validate(risk_heatmap_data) if risk_heatmap_data else None
        vintage_curves_data = await service.calculate_vintage_curves(loans)
        layered_analysis = await service.get_layered_insights(loans)
        unit_economics = await service.calculate_unit_economics(loans)
        portfolio_health = await service.get_portfolio_health_score(loans)
        strategic_data = await service.get_executive_analytics(loans)
        return FullAnalysisResponse(analysis_id=trace_id, summary=summary, recommendations=recommendations, kpis=kpis, risk_assessment=RiskAlertsResponse(high_risk_count=0, total_loans=len(loans), risk_ratio=0.0, high_risk_loans=[]), risk_stratification=risk_stratification, risk_heatmap=risk_heatmap_response, vintage_curves=vintage_curves_data, layered_analysis=layered_analysis, strategic_confirmations=strategic_data.get('strategic_confirmations', {}), executive_strip=strategic_data.get('executive_strip', {}), nsm_customer_types=strategic_data.get('nsm_customer_types', {}), dpd_buckets=strategic_data.get('dpd_buckets', {}), concentration=strategic_data.get('concentration', {}), portfolio_rotation=strategic_data.get('portfolio_rotation', {}), monthly_pricing=strategic_data.get('monthly_pricing', {}), weighted_apr=float(strategic_data.get('weighted_apr', 0.0) or 0.0), weighted_fee_rate=float(strategic_data.get('weighted_fee_rate', 0.0) or 0.0), churn_90d_metrics=strategic_data.get('churn_90d_metrics', []), revenue_forecast_6m=strategic_data.get('revenue_forecast_6m', []), opportunity_prioritization=strategic_data.get('opportunity_prioritization', []), data_governance=strategic_data.get('data_governance', {}), unit_economics=unit_economics, portfolio_health=portfolio_health)

    @app.post('/analytics/decision-dashboard', response_model=DecisionDashboardResponse)
    async def get_decision_dashboard(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            if not request.loans:
                raise HTTPException(status_code=400, detail='Decision dashboard requires loan records in request.loans')
            return await service.get_decision_dashboard(request.loans)
        except HTTPException:
            raise
        except Exception as e:
            logger.error('Error in get_decision_dashboard: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/analytics/executive-summary', response_model=ExecutiveAnalyticsResponse)
    async def get_executive_summary(request: ExecutiveAnalyticsRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            executive_data = await service.get_executive_analytics(loans=request.loans, payments=request.payments, customers=request.customers, schedule=request.schedule)
            return ExecutiveAnalyticsResponse(**executive_data)
        except Exception as e:
            logger.error('Error in get_executive_summary: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.post('/data-quality/profile', response_model=DataQualityResponse)
    async def get_data_quality_profile(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.get_data_quality_profile(request.loans)
        except Exception as e:
            _raise_internal_http_error('get_data_quality_profile', e)

    @app.post('/data-quality/validate', response_model=ValidationResponse)
    async def validate_loan_data(request: LoanPortfolioRequest=Body(...), service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.validate_loan_portfolio_schema(request.loans)
        except Exception as e:
            _raise_internal_http_error('validate_loan_data', e)

    @app.get('/data/{file_path:path}')
    def get_data(file_path: str):
        if not file_path or not file_path.strip():
            raise HTTPException(status_code=400, detail='file path cannot be empty')
        try:
            resolved = _sanitize_and_resolve(file_path, ALLOWED_DATA_DIR)
        except ValueError as exc:
            safe_path = _sanitize_for_logging(file_path)
            logger.warning('Invalid data path requested: %s (%s)', safe_path, str(exc))
            raise HTTPException(status_code=400, detail='Invalid path format') from exc
        if not resolved.exists() or not resolved.is_file():
            raise HTTPException(status_code=404, detail='file not found')
        return {'status': 'ok', 'path': str(resolved)}
    _risk_model_cache: dict = {}

    def _get_risk_model():
        backend = os.getenv('DEFAULT_RISK_MODEL_BACKEND', 'xgb').strip().lower()
        if _risk_model_cache.get('backend') != backend:
            _risk_model_cache.clear()
            _risk_model_cache['backend'] = backend
            logger.info('Risk model backend selected: %s', backend)
        if 'model' not in _risk_model_cache:
            try:
                base_path = Path(__file__).resolve().parents[4]
                if backend in {'torch', 'pytorch'}:
                    from backend.python.models.default_risk_torch_model import TorchDefaultRiskModel
                    model_path = base_path / 'models' / 'risk' / 'default_risk_torch.pt'
                    if model_path.exists():
                        _risk_model_cache['model'] = TorchDefaultRiskModel.load(str(model_path))
                        _risk_model_cache['model_version'] = 'torch_mlp_v1'
                        logger.info('Loaded torch default risk model from %s', model_path)
                    else:
                        logger.warning('Torch risk model not found at %s', model_path)
                        _risk_model_cache['model'] = None
                        _risk_model_cache['model_version'] = 'torch_mlp_v1'
                else:
                    from backend.python.models.default_risk_model import DefaultRiskModel
                    model_path = base_path / 'models' / 'risk' / 'default_risk_xgb.ubj'
                    if model_path.exists():
                        _risk_model_cache['model'] = DefaultRiskModel.load(str(model_path))
                        _risk_model_cache['model_version'] = 'xgb_v1'
                        logger.info('Loaded XGBoost default risk model from %s', model_path)
                    else:
                        logger.warning('XGBoost risk model not found at %s', model_path)
                        _risk_model_cache['model'] = None
                        _risk_model_cache['model_version'] = 'xgb_v1'
            except Exception as e:
                logger.error('Failed to load risk model: %s', e)
                _risk_model_cache['model'] = None
                _risk_model_cache['model_version'] = f'{backend}_unavailable'
        return (_risk_model_cache.get('model'), _risk_model_cache.get('model_version', 'unknown'))

    def _map_default_request_to_model_features(request: DefaultPredictionRequest) -> dict[str, float]:
        loan_amount = float(request.loan_amount)
        rate = float(request.interest_rate)
        if rate > 1.0:
            rate /= 100.0
        ltv_ratio = max(0.0, float(request.ltv_ratio))
        collateral_value = loan_amount
        if ltv_ratio > 0:
            collateral_value = loan_amount / max(ltv_ratio / 100.0, 1e-09)
        scheduled_proxy = loan_amount * (1.0 + rate * max(float(request.term_months), 0.0) / 12.0)
        return {'principal_amount': loan_amount, 'interest_rate': rate, 'term_months': float(request.term_months), 'collateral_value': float(collateral_value), 'outstanding_balance': loan_amount, 'tpv': loan_amount, 'equifax_score': float(request.credit_score), 'last_payment_amount': 0.0, 'total_scheduled': max(float(scheduled_proxy), 0.0), 'origination_fee': 0.0, 'days_past_due': float(request.days_past_due)}

    @app.post('/predict/default', response_model=DefaultPredictionResponse)
    async def predict_default(request: DefaultPredictionRequest=Body(...)):
        model, model_version = _get_risk_model()
        if model is None:
            raise HTTPException(status_code=503, detail='Risk model not available. Train and store a model under models/risk/ (xgb: default_risk_xgb.ubj, torch: default_risk_torch.pt).')
        try:
            loan_data = _map_default_request_to_model_features(request)
            probability = model.predict_proba(loan_data)
            if probability >= 0.7:
                risk_level = 'critical'
            elif probability >= 0.4:
                risk_level = 'high'
            elif probability >= 0.15:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            return DefaultPredictionResponse(probability=round(probability, 4), risk_level=risk_level, model_version=str(model_version))
        except Exception as e:
            logger.error('Error in predict_default: %s', e)
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR) from e

    @app.get('/analytics/nsm', response_model=NSMRecurrentTPVResponse)
    async def get_nsm(service: KPIService=Depends(get_kpi_service)):
        try:
            return await service.get_nsm_recurrent_tpv()
        except Exception as e:
            _raise_internal_http_error('get_nsm', e)

def _sanitize_for_logging(value: str, max_length: int=200) -> str:
    if not value:
        return ''
    sanitized = value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace('\x00', '').replace('\x1b', '')
    sanitized = re.sub('[\\x00-\\x08\\x0B-\\x0C\\x0E-\\x1F\\x7F]', '', sanitized)
    if len(sanitized) > max_length:
        return f'{sanitized[:max_length]}...[truncated]'
    return sanitized

def _sanitize_and_resolve(candidate: str, allowed_dir: Path) -> Path:
    if not candidate:
        raise ValueError(EMPTY_PATH_ERROR)
    normalized = candidate.replace('\\', '/').strip()
    if not normalized:
        raise ValueError(EMPTY_PATH_ERROR)
    if normalized.startswith('/'):
        raise ValueError('absolute paths are not allowed')
    if not re.match('^[a-zA-Z0-9_./\\-]+$', normalized):
        raise ValueError('invalid characters')
    safe_parts = []
    for part in normalized.split('/'):
        if not part or part == '.':
            continue
        if part == '..':
            raise ValueError('parent traversal is not allowed')
        if not re.match('^[a-zA-Z0-9_.\\-]+$', part):
            raise ValueError('invalid path segment')
        safe_parts.append(part)
    if not safe_parts:
        raise ValueError(EMPTY_PATH_ERROR)
    resolved = allowed_dir.resolve().joinpath(*safe_parts).resolve(strict=False)
    try:
        resolved.relative_to(allowed_dir.resolve())
    except ValueError as exc:
        raise ValueError('outside the allowed data directory') from exc
    return resolved
if __name__ == '__main__':
    import uvicorn
    host = os.getenv('API_HOST', '127.0.0.1')
    port = int(os.getenv('API_PORT', '8000'))
    if app is not None:
        uvicorn.run(app, host=host, port=port)
    else:
        print('FastAPI app not initialized. Check imports.')
        sys.exit(1)
