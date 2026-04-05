import json
import logging
import os
from decimal import Decimal, ROUND_HALF_UP, getcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
# Set ROUND_HALF_UP before importing SSOT modules — the financial precision policy requires this
# (docs/FINANCIAL_PRECISION_GOVERNANCE.md) and ssot_asset_quality enforces it at import time.
getcontext().rounding = ROUND_HALF_UP
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
try:
    from backend.loans_analytics.kpis.ssot_asset_quality import (
        calculate_par as _ssot_calculate_par,
    )
except ModuleNotFoundError:

    def _ssot_calculate_par(  # type: ignore[misc]
        par_amount: Decimal, total_portfolio: Decimal, dpd_threshold: int = 0
    ) -> Decimal:
        """PAR rate fallback: par_amount / total_portfolio (fail-fast on zero denominator)."""
        if total_portfolio == 0:
            raise ValueError(
                f"CRITICAL: calculate_par(dpd_threshold={dpd_threshold}) received zero total "
                "portfolio. Provide a non-zero portfolio balance."
            )
        return (par_amount / total_portfolio).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
from backend.loans_analytics.multi_agent.guardrails import Guardrails
from backend.loans_analytics.multi_agent.orchestrator import MultiAgentOrchestrator
from backend.loans_analytics.multi_agent.protocol import LLMProvider
from frontend.streamlit_app.components.csv_upload import BORROWER_ID_COLS, classify_loan_id_duplicates as _classify_loan_id_duplicates, coerce_numeric as _coerce_amount
from frontend.streamlit_app.utils.security import sanitize_api_base
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
REPO_ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)
st.set_page_config(page_title='Loans Analytics', page_icon='📊', layout='wide', initial_sidebar_state='expanded')
st.markdown('\n<style>\n    .main-header {\n        font-size: 2.5rem;\n        font-weight: bold;\n        color: #1f77b4;\n        text-align: center;\n        padding: 1rem 0;\n    }\n    .metric-card {\n        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n        padding: 1.5rem;\n        border-radius: 0.5rem;\n        color: white;\n        text-align: center;\n        margin: 0.5rem 0;\n    }\n    .metric-value {\n        font-size: 2rem;\n        font-weight: bold;\n    }\n    .metric-label {\n        font-size: 0.9rem;\n        opacity: 0.9;\n    }\n    .status-current {\n        background-color: #28a745;\n        color: white;\n        padding: 0.25rem 0.5rem;\n        border-radius: 0.25rem;\n    }\n    .status-delinquent {\n        background-color: #ffc107;\n        color: black;\n        padding: 0.25rem 0.5rem;\n        border-radius: 0.25rem;\n    }\n    .status-default {\n        background-color: #dc3545;\n        color: white;\n        padding: 0.25rem 0.5rem;\n        border-radius: 0.25rem;\n    }\n    .status-paid-off {\n        background-color: #17a2b8;\n        color: white;\n        padding: 0.25rem 0.5rem;\n        border-radius: 0.25rem;\n    }\n</style>\n', unsafe_allow_html=True)
REQUIRED_COLUMNS = ['loan_id', 'borrower_name', 'borrower_email', 'borrower_id_number', 'principal_amount', 'interest_rate', 'term_months', 'origination_date', 'current_status', 'payment_history_json', 'risk_score', 'region']
CORE_REQUIRED_COLUMNS = ['loan_id', 'principal_amount', 'interest_rate', 'term_months', 'origination_date', 'current_status']
MONITORING_EVENTS_ENDPOINT = '/monitoring/events'
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000')
API_BASE_SAFE = sanitize_api_base(API_BASE_URL)
AGENT_OUTPUTS_DIR = REPO_ROOT / 'data' / 'agent_outputs'
AGENT_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
KPI_EXPECTED_LOSS = 'Expected Loss'
DPD_30_PLUS = 'DPD 30+'
DPD_60_PLUS = 'DPD 60+'
DPD_90_PLUS = 'DPD 90+'
SEG_OUTSTANDING = 'Outstanding ($)'
SEG_PAR_30 = 'PAR 30 (%)'
SEG_PAR_60 = 'PAR 60 (%)'
SEG_PAR_90 = 'PAR 90 (%)'
SEG_DEFAULT_RATE = 'Default Rate (%)'
_ACTIVE_ALIASES = {'active', 'current', 'vigente', 'open', 'in_force'}
_CLOSED_ALIASES = {'closed', 'complete', 'completed', 'paid', 'paid_off', 'paid-off', 'cancelled', 'canceled', 'liquidated'}
_DELINQUENT_ALIASES = {'delinquent', 'late', 'past_due', 'arrears', 'mora'}
_DEFAULTED_ALIASES = {'default', 'defaulted', 'charged_off', 'charge_off', 'written_off'}
STATUS_ALIAS_TO_CANONICAL = dict.fromkeys(_ACTIVE_ALIASES, 'active') | dict.fromkeys(_CLOSED_ALIASES, 'closed') | dict.fromkeys(_DELINQUENT_ALIASES, 'delinquent') | dict.fromkeys(_DEFAULTED_ALIASES, 'defaulted')

def _build_monitoring_events_url() -> str | None:
    if API_BASE_SAFE is None:
        return None
    base = API_BASE_SAFE.rstrip('/')
    url = f'{base}{MONITORING_EVENTS_ENDPOINT}'
    parsed_url = urlparse(url)
    parsed_base = urlparse(base)
    if parsed_url.netloc != parsed_base.netloc or parsed_url.scheme != parsed_base.scheme:
        return None
    return url

def _emit_agent_comments_to_monitoring(results: dict[str, Any]) -> int:
    comments = results.get('_agent_comments', [])
    if not isinstance(comments, list) or not comments:
        return 0
    events_url = _build_monitoring_events_url()
    if events_url is None:
        return 0
    metadata = results.get('_metadata', {}) if isinstance(results.get('_metadata'), dict) else {}
    emitted = 0
    for item in comments:
        comment = item.get('comment') if isinstance(item, dict) else None
        if not comment:
            continue
        payload = {'agent_role': item.get('agent_role'), 'output_key': item.get('output_key'), 'comment': comment, 'tokens_used': item.get('tokens_used'), 'cost_usd': item.get('cost_usd'), 'latency_ms': item.get('latency_ms'), 'scenario_name': metadata.get('scenario_name'), 'trace_id': metadata.get('trace_id')}
        body = {'event_type': 'agent_commentary', 'severity': 'info', 'source': 'agent', 'payload': payload}
        try:
            resp = requests.post(events_url, json=body, timeout=5)
            resp.raise_for_status()
            emitted += 1
        except requests.RequestException:
            continue
    return emitted

def _kpi_snapshot_from_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {'total_loans': int(metrics.get('total_loans', 0)), 'total_loans_all': int(metrics.get('total_loans_all', 0)), 'closed_loans': int(metrics.get('closed_loans', 0)), 'total_portfolio': float(metrics.get('total_portfolio', 0.0)), 'weighted_avg_rate': float(metrics.get('weighted_avg_rate', 0.0)), 'delinquency_rate_30': float(metrics.get('delinquency_rate_30', 0.0)), 'delinquency_rate_60': float(metrics.get('delinquency_rate_60', 0.0)), 'delinquency_rate_90': float(metrics.get('delinquency_rate_90', 0.0)), 'par_30_rate': float(metrics.get('par_30_rate', 0.0)), 'par_90_rate': float(metrics.get('par_90_rate', 0.0)), 'default_rate': float(metrics.get('default_rate', 0.0)), 'collections_rate': float(metrics.get('collections_rate', 0.0)), 'recovery_rate': float(metrics.get('recovery_rate', 0.0)), 'loss_rate': float(metrics.get('loss_rate', 0.0)), 'active_borrowers': int(metrics.get('active_borrowers', 0)), 'repeat_borrower_rate': float(metrics.get('repeat_borrower_rate', 0.0)), 'cash_on_hand': float(metrics.get('cash_on_hand', 0.0)), 'expected_loss': float(metrics.get('expected_loss', 0.0)), 'expected_loss_rate': float(metrics.get('expected_loss_rate', 0.0)), 'avg_loan_size': float(metrics.get('avg_loan_size', 0.0)), 'avg_risk_score': float(metrics.get('avg_risk_score', 0.0))}

def _kpi_methodology_from_metrics(metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    total_loans = int(metrics.get('total_loans', 0))
    total_portfolio = float(metrics.get('total_portfolio', 0.0))
    weighted_rate_numerator = float(metrics.get('weighted_rate_numerator', 0.0))
    dpd_30_count = int(metrics.get('dpd_30_count', 0))
    dpd_60_count = int(metrics.get('dpd_60_count', 0))
    dpd_90_count = int(metrics.get('dpd_90_count', 0))
    par_30_amount = float(metrics.get('par_30_amount', 0.0))
    par_90_amount = float(metrics.get('par_90_amount', 0.0))
    expected_loss = float(metrics.get('expected_loss', 0.0))
    default_count = int(metrics.get('default_count', 0))
    default_exposure = float(metrics.get('default_exposure', 0.0))
    collections_received = float(metrics.get('collections_received', 0.0))
    collections_scheduled = float(metrics.get('collections_scheduled', 0.0))
    default_collections = float(metrics.get('default_collections', 0.0))
    return {'weighted_avg_rate': {'formula': 'sum(exposure_amount * interest_rate) / sum(exposure_amount)', 'numerator': weighted_rate_numerator, 'denominator': total_portfolio, 'value': float(metrics.get('weighted_avg_rate', 0.0)), 'unit': 'ratio'}, 'delinquency_rate_30': {'formula': 'count(loans where days_past_due >= 30) / total_loans * 100', 'numerator': dpd_30_count, 'denominator': total_loans, 'value': float(metrics.get('delinquency_rate_30', 0.0)), 'unit': 'percent'}, 'delinquency_rate_60': {'formula': 'count(loans where days_past_due >= 60) / total_loans * 100', 'numerator': dpd_60_count, 'denominator': total_loans, 'value': float(metrics.get('delinquency_rate_60', 0.0)), 'unit': 'percent'}, 'delinquency_rate_90': {'formula': 'count(loans where days_past_due >= 90) / total_loans * 100', 'numerator': dpd_90_count, 'denominator': total_loans, 'value': float(metrics.get('delinquency_rate_90', 0.0)), 'unit': 'percent'}, 'par_30_rate': {'formula': 'sum(exposure where days_past_due >= 30) / total_portfolio * 100', 'numerator': par_30_amount, 'denominator': total_portfolio, 'value': float(metrics.get('par_30_rate', 0.0)), 'unit': 'percent'}, 'par_90_rate': {'formula': 'sum(exposure where days_past_due >= 90) / total_portfolio * 100', 'numerator': par_90_amount, 'denominator': total_portfolio, 'value': float(metrics.get('par_90_rate', 0.0)), 'unit': 'percent'}, 'default_rate': {'formula': 'count(loans where status = defaulted) / total_loans * 100', 'numerator': default_count, 'denominator': total_loans, 'value': float(metrics.get('default_rate', 0.0)), 'unit': 'percent'}, 'collections_rate': {'formula': 'sum(last_payment_amount) / sum(total_scheduled) * 100', 'numerator': collections_received, 'denominator': collections_scheduled, 'value': float(metrics.get('collections_rate', 0.0)), 'unit': 'percent'}, 'recovery_rate': {'formula': 'sum(last_payment_amount where status=defaulted) / sum(exposure where status=defaulted) * 100', 'numerator': default_collections, 'denominator': default_exposure, 'value': float(metrics.get('recovery_rate', 0.0)), 'unit': 'percent'}, 'expected_loss': {'formula': 'sum(risk_score * exposure_amount)', 'numerator': expected_loss, 'denominator': None, 'value': expected_loss, 'unit': 'currency_eur'}, 'expected_loss_rate': {'formula': 'expected_loss / total_portfolio * 100', 'numerator': expected_loss, 'denominator': total_portfolio, 'value': float(metrics.get('expected_loss_rate', 0.0)), 'unit': 'percent'}}

def _kpi_methodology_rows(metrics: dict[str, Any]) -> list[dict[str, str]]:

    def fmt_currency(value: float) -> str:
        return f'€{value:,.2f}'

    def fmt_percent(value: float) -> str:
        return f'{value:.2f}%'

    def fmt_ratio(value: float) -> str:
        return f'{value:.4f}'
    methodology = _kpi_methodology_from_metrics(metrics)
    total_loans = int(metrics.get('total_loans', 0))
    total_portfolio = float(metrics.get('total_portfolio', 0.0))
    return [
        {'KPI': 'Total Portfolio Value', 'Formula': 'sum(exposure_amount) for active loans', 'Numerator': fmt_currency(total_portfolio), 'Denominator': 'n/a', 'Value': fmt_currency(total_portfolio)},
        {'KPI': 'Weighted Avg Rate', 'Formula': methodology['weighted_avg_rate']['formula'], 'Numerator': f"{methodology['weighted_avg_rate']['numerator']:,.2f}", 'Denominator': fmt_currency(float(methodology['weighted_avg_rate']['denominator'] or 0.0)), 'Value': f"{float(methodology['weighted_avg_rate']['value']):.2%}"},
        {'KPI': f'{DPD_30_PLUS} Rate', 'Formula': methodology['delinquency_rate_30']['formula'], 'Numerator': f"{int(methodology['delinquency_rate_30']['numerator']):,} loans", 'Denominator': f'{total_loans:,} loans', 'Value': fmt_percent(float(methodology['delinquency_rate_30']['value']))},
        {'KPI': f'{DPD_60_PLUS} Rate', 'Formula': methodology['delinquency_rate_60']['formula'], 'Numerator': f"{int(methodology['delinquency_rate_60']['numerator']):,} loans", 'Denominator': f'{total_loans:,} loans', 'Value': fmt_percent(float(methodology['delinquency_rate_60']['value']))},
        {'KPI': f'{DPD_90_PLUS} Rate', 'Formula': methodology['delinquency_rate_90']['formula'], 'Numerator': f"{int(methodology['delinquency_rate_90']['numerator']):,} loans", 'Denominator': f'{total_loans:,} loans', 'Value': fmt_percent(float(methodology['delinquency_rate_90']['value']))},
        {'KPI': 'PAR 30', 'Formula': methodology['par_30_rate']['formula'], 'Numerator': fmt_currency(float(methodology['par_30_rate']['numerator'])), 'Denominator': fmt_currency(float(methodology['par_30_rate']['denominator'] or 0.0)), 'Value': fmt_percent(float(methodology['par_30_rate']['value']))},
        {'KPI': 'PAR 90', 'Formula': methodology['par_90_rate']['formula'], 'Numerator': fmt_currency(float(methodology['par_90_rate']['numerator'])), 'Denominator': fmt_currency(float(methodology['par_90_rate']['denominator'] or 0.0)), 'Value': fmt_percent(float(methodology['par_90_rate']['value']))},
        {'KPI': 'Default Rate', 'Formula': methodology['default_rate']['formula'], 'Numerator': f"{int(methodology['default_rate']['numerator']):,} loans", 'Denominator': f'{total_loans:,} loans', 'Value': fmt_percent(float(methodology['default_rate']['value']))},
        {'KPI': 'Collections Rate', 'Formula': methodology['collections_rate']['formula'], 'Numerator': fmt_currency(float(methodology['collections_rate']['numerator'])), 'Denominator': fmt_currency(float(methodology['collections_rate']['denominator'] or 0.0)), 'Value': fmt_percent(float(methodology['collections_rate']['value']))},
        {'KPI': 'Recovery Rate', 'Formula': methodology['recovery_rate']['formula'], 'Numerator': fmt_currency(float(methodology['recovery_rate']['numerator'])), 'Denominator': fmt_currency(float(methodology['recovery_rate']['denominator'] or 0.0)), 'Value': fmt_percent(float(methodology['recovery_rate']['value']))},
        {'KPI': KPI_EXPECTED_LOSS, 'Formula': methodology['expected_loss']['formula'], 'Numerator': fmt_currency(float(methodology['expected_loss']['numerator'])), 'Denominator': 'n/a', 'Value': fmt_currency(float(methodology['expected_loss']['value']))},
        {'KPI': f'{KPI_EXPECTED_LOSS} Rate', 'Formula': methodology['expected_loss_rate']['formula'], 'Numerator': fmt_currency(float(methodology['expected_loss_rate']['numerator'])), 'Denominator': fmt_currency(float(methodology['expected_loss_rate']['denominator'] or 0.0)), 'Value': fmt_percent(float(methodology['expected_loss_rate']['value']))},
        {'KPI': 'Average Loan Size', 'Formula': 'total_portfolio / total_loans', 'Numerator': fmt_currency(total_portfolio), 'Denominator': f'{total_loans:,} loans', 'Value': fmt_currency(float(metrics.get('avg_loan_size', 0.0)))},
        {'KPI': 'Average Risk Score', 'Formula': 'sum(risk_score) / total_loans', 'Numerator': f"{float(metrics.get('risk_score_sum', 0.0)):.4f}", 'Denominator': f'{total_loans:,} loans', 'Value': fmt_ratio(float(metrics.get('avg_risk_score', 0.0)))}
    ]

def _enrich_agent_results_with_kpis(results: dict[str, Any], metrics: dict[str, Any], mode: str) -> dict[str, Any]:
    enriched = dict(results)
    enriched['kpi_snapshot'] = _kpi_snapshot_from_metrics(metrics)
    enriched['kpi_methodology'] = _kpi_methodology_from_metrics(metrics)
    metadata = enriched.get('_metadata', {})
    if not isinstance(metadata, dict):
        metadata = {}
    metadata['analysis_mode'] = mode
    metadata['kpi_count'] = len(enriched['kpi_snapshot'])
    enriched['_metadata'] = metadata
    return enriched

def _emit_kpi_snapshot_to_monitoring(results: dict[str, Any]) -> int:
    kpi_snapshot = results.get('kpi_snapshot')
    if not isinstance(kpi_snapshot, dict) or not kpi_snapshot:
        return 0
    events_url = _build_monitoring_events_url()
    if events_url is None:
        return 0
    metadata = results.get('_metadata', {}) if isinstance(results.get('_metadata'), dict) else {}
    message = f"KPI snapshot | Portfolio: €{float(kpi_snapshot.get('total_portfolio', 0.0)):,.0f} | DPD30+: {float(kpi_snapshot.get('delinquency_rate_30', 0.0)):.2f}% | PAR30: {float(kpi_snapshot.get('par_30_rate', 0.0)):.2f}% | {KPI_EXPECTED_LOSS}: €{float(kpi_snapshot.get('expected_loss', 0.0)):,.0f}"
    body = {'event_type': 'agent_kpi_snapshot', 'severity': 'info', 'source': 'dashboard', 'payload': {'message': message, 'kpis': kpi_snapshot, 'kpi_methodology': results.get('kpi_methodology', {}), 'scenario_name': metadata.get('scenario_name'), 'trace_id': metadata.get('trace_id'), 'analysis_mode': metadata.get('analysis_mode')}}
    try:
        resp = requests.post(events_url, json=body, timeout=5)
        resp.raise_for_status()
        return 1
    except requests.RequestException:
        return 0

def _safe_slug(value: str) -> str:
    lowered = value.lower().replace('_', '-').strip()
    slug = ''.join((ch if ch.isalnum() or ch == '-' else '-' for ch in lowered))
    slug = '-'.join((part for part in slug.split('-') if part))
    return slug or 'unknown'

def _persist_agent_outputs(results: dict[str, Any]) -> int:
    comments = results.get('_agent_comments', [])
    if not isinstance(comments, list) or not comments:
        return 0
    metadata = results.get('_metadata', {}) if isinstance(results.get('_metadata'), dict) else {}
    scenario_name = str(metadata.get('scenario_name', 'unknown_scenario'))
    trace_id = metadata.get('trace_id')
    saved = 0
    for item in comments:
        if not isinstance(item, dict):
            continue
        comment = item.get('comment')
        error = item.get('error')
        output_key = str(item.get('output_key', 'agent_output'))
        role_slug = _safe_slug(str(item.get('agent_role', 'unknown_agent')))
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec='microseconds')
        file_path = AGENT_OUTPUTS_DIR / f'{timestamp}_{role_slug}_response.json'
        status = 'success' if comment else 'error'
        response_text = str(comment) if comment else str(error or '')
        payload = {'query': f'{scenario_name}:{output_key}', 'response': response_text, 'status': status, 'tokens_used': int(item.get('tokens_used') or 0), 'cost_usd': float(item.get('cost_usd') or 0.0), 'latency_ms': float(item.get('latency_ms') or 0.0), 'trace_id': trace_id, 'scenario_name': scenario_name, 'output_key': output_key, 'analysis_mode': metadata.get('analysis_mode'), 'kpi_snapshot': results.get('kpi_snapshot', {})}
        with open(file_path, 'w', encoding='utf-8') as output_file:
            json.dump(payload, output_file, ensure_ascii=False, indent=2)
        saved += 1
    return saved
COLUMN_ALIASES = {'loan_id': ['id_loan', 'idprestamo', 'prestamo_id', 'loanid', 'id', 'numero_desembolso', 'codigo_desembolso', 'correlativo_de_operaciones', 'nrc', 'application_id'], 'borrower_name': ['customer_name', 'client_name', 'nombre', 'nombre_cliente'], 'borrower_email': ['email', 'correo', 'correo_electronico', 'customer_email'], 'borrower_id_number': ['dni', 'documento', 'id_number', 'cedula', 'nif'], 'borrower_id': ['customer_id', 'customer_id_cust', 'codcliente', 'codcliente1', 'cliente_id'], 'principal_amount': ['principal', 'loan_amount', 'principal_balance', 'outstanding_balance', 'current_balance', 'amount', 'monto', 'monto_prestamo', 'monto_financiado', 'monto_financiar', 'valor_financiado', 'valor_factura', 'importe', 'capital_inicial', 'saldo_inicial', 'capital', 'tpv', 'total_receivable_usd', 'discounted_balance_usd', 'monto_del_desembolso', 'monto_financiado_real_por_desembolso', 'monto_total_aprobado_por_desembolso', 'monto_financiado_real', 'monto_total_aprobado'], 'interest_rate': ['interest_rate_apr', 'annual_interest_rate', 'apr', 'rate', 'rate_pct', 'rate_percent', 'tasa', 'tasa_interes', 'tasa_de_interes', 'tasa_anual', 'tasa_nominal', 'tasa_efectiva', 'interest_rate_percent', 'interest_pct', 'interest', 'interes'], 'term_months': ['term', 'tenor_months', 'plazo_meses', 'duration_months'], 'origination_date': ['disbursement_date', 'start_date', 'fecha_originacion', 'fecha_inicio', 'fecha_desembolso', 'fechadesembolso', 'fecha_de_desembolso'], 'current_status': ['status', 'loan_status', 'estado', 'estado_actual'], 'payment_history_json': ['payment_history', 'payments_json', 'historial_pagos'], 'risk_score': ['score', 'riesgo', 'risk', 'credit_score'], 'region': ['province', 'zona', 'location', 'state'], 'days_past_due': ['dias_mora', 'dias_de_mora', 'dpd', 'dias_vencido', 'mora_en_dias'], 'company': ['empresa', 'compania'], 'credit_line': ['lineacredito'], 'kam_hunter': ['cod_kam_hunter', 'cod_kam_hunter_', 'cod_kam_hunter1', 'cod_kam_hunter_1'], 'kam_farmer': ['cod_kam_farmer', 'cod_kam_farmer_', 'cod_kam_farmer1', 'cod_kam_farmer_1', 'farmer'], 'collections_eligible': ['procede_a_cobrar'], 'delinquency_definition': ['definicion_m'], 'delinquency_bucket_raw': ['rango_m'], 'credit_line_range': ['rango_de_la_linea'], 'ministry': ['ministerio'], 'government_sector': ['goes'], 'capital_collected': ['capitalcobrado'], 'total_payment_received': ['montototalabonado'], 'utilization_pct': ['porcentaje_utilizado'], 'approved_value': ['valoraprobado'], 'mdsc_posted': ['mdscposteado'], 'advisory_channel': ['asesoriadigital']}
OPTIONAL_DEFAULTS = {'borrower_name': 'Unknown Borrower', 'borrower_email': '', 'borrower_id_number': '', 'payment_history_json': '[]', 'risk_score': 0.2, 'region': 'unknown'}
STATUS_ACTIVE_EXPOSURE = {'active', 'delinquent', 'defaulted', 'unknown'}

def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = normalized.columns.astype(str).str.normalize('NFKD').str.encode('ascii', 'ignore').str.decode('ascii').str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    return normalized

def _apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.copy()
    rename_map: dict[str, str] = {}
    existing = set(renamed.columns)
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in existing:
            continue
        for alias in aliases:
            if alias in existing:
                rename_map[alias] = canonical
                break
    if rename_map:
        renamed = renamed.rename(columns=rename_map)
    return renamed


def _coalesce_duplicate_columns(merged: pd.DataFrame) -> pd.DataFrame:
    dup_cols = [col for col in merged.columns if col.endswith('_dup')]
    updates: dict[str, pd.Series] = {}
    drop_cols: list[str] = []
    rename_map: dict[str, str] = {}
    for dup_col in dup_cols:
        base_col = dup_col[:-4]
        if base_col in merged.columns:
            fill_mask = merged[base_col].isna() & merged[dup_col].notna()
            updates[base_col] = merged[base_col].where(~fill_mask, merged[dup_col])
            drop_cols.append(dup_col)
        else:
            rename_map[dup_col] = base_col
    if updates:
        merged = merged.assign(**updates)
    if drop_cols:
        merged = merged.drop(columns=drop_cols)
    if rename_map:
        merged = merged.rename(columns=rename_map)
    return merged.copy()

def _merge_uploaded_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    merged = frames[0].copy()
    for frame in frames[1:]:
        if 'loan_id' in merged.columns and 'loan_id' in frame.columns:
            merged = merged.merge(frame, on='loan_id', how='outer', suffixes=('', '_dup'))
            merged = _coalesce_duplicate_columns(merged)
            continue
        merged = pd.concat([merged, frame], ignore_index=True, sort=False)
    return merged

def _normalize_payment_history(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps(value)
    if isinstance(value, dict):
        return json.dumps([value])
    if pd.isna(value):
        return '[]'
    text_value = str(value).strip()
    if not text_value:
        return '[]'
    try:
        parsed = json.loads(text_value)
        if isinstance(parsed, list):
            return json.dumps(parsed)
        if isinstance(parsed, dict):
            return json.dumps([parsed])
    except (json.JSONDecodeError, TypeError):
        return '[]'
    return '[]'

def _get_exposure_series(df: pd.DataFrame) -> pd.Series:
    # CANONICAL: align column resolution with the KPI engine (risk.py / compute_par*).
    # outstanding_principal is the canonical column; others are fallbacks in order of fidelity.
    candidate_names = [col for col in ('outstanding_principal', 'outstanding_balance', 'current_balance', 'principal_amount') if col in df]
    if not candidate_names:
        return pd.Series(0.0, index=df.index, dtype=float)
    exposure = pd.to_numeric(df[candidate_names[0]], errors='coerce')
    for col in candidate_names[1:]:
        candidate = pd.to_numeric(df[col], errors='coerce')
        fill_mask = exposure.isna() & candidate.notna()
        if fill_mask.any():
            exposure = exposure.where(~fill_mask, candidate)
    return exposure.fillna(0.0)

def _get_numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(0.0, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors='coerce').fillna(0.0)

def _canonicalize_status(value: Any) -> str:
    raw = str(value).strip().lower()
    if not raw or raw == 'nan':
        return 'active'
    return STATUS_ALIAS_TO_CANONICAL.get(raw, 'unknown')

def validate_uploaded_data(df: pd.DataFrame) -> tuple[bool, list[str]]:
    missing_columns = [col for col in CORE_REQUIRED_COLUMNS if col not in df.columns]
    return (all(col in df.columns for col in CORE_REQUIRED_COLUMNS), missing_columns)

def _suggest_columns_for_missing(df: pd.DataFrame, missing: list[str]) -> dict[str, list[str]]:
    suggestions: dict[str, list[str]] = {}
    available = list(df.columns)
    for canonical in missing:
        aliases = set(COLUMN_ALIASES.get(canonical, []))
        aliases.add(canonical)
        matches: list[str] = []
        for col in available:
            col_l = col.lower()
            if any((alias in col_l or col_l in alias for alias in aliases)):
                matches.append(col)
        if matches:
            suggestions[canonical] = matches[:4]
    return suggestions

def prepare_uploaded_data(df: pd.DataFrame) -> pd.DataFrame:
    prepared = _apply_column_aliases(_normalize_column_names(df))
    valid, missing_cols = validate_uploaded_data(prepared)
    if not valid:
        suggestions = _suggest_columns_for_missing(prepared, missing_cols)
        if suggestions:
            hint = ' | Suggested mappings: ' + '; '.join((f"{canonical} <- {', '.join(cols)}" for canonical, cols in suggestions.items()))
        else:
            hint = ''
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}{hint}")
    prepared['loan_id'] = prepared['loan_id'].astype(str).str.strip()
    prepared = prepared[prepared['loan_id'] != ''].copy()
    prepared['principal_amount'] = _coerce_amount(prepared['principal_amount'])
    prepared['interest_rate'] = pd.to_numeric(prepared['interest_rate'], errors='coerce')
    prepared['term_months'] = pd.to_numeric(prepared['term_months'], errors='coerce')
    prepared['origination_date'] = pd.to_datetime(prepared['origination_date'], errors='coerce', format='mixed')
    if not prepared['interest_rate'].dropna().empty and prepared['interest_rate'].dropna().median() > 1:
        prepared['interest_rate'] = prepared['interest_rate'] / 100.0
    prepared['current_status'] = prepared['current_status'].map(_canonicalize_status)
    for numeric_col in ['days_past_due', 'outstanding_balance', 'current_balance', 'last_payment_amount', 'total_scheduled', 'tpv', 'amount']:
        if numeric_col in prepared.columns:
            prepared[numeric_col] = pd.to_numeric(prepared[numeric_col], errors='coerce')
    for col_name, default_value in OPTIONAL_DEFAULTS.items():
        if col_name not in prepared.columns:
            prepared[col_name] = default_value
    prepared['borrower_name'] = prepared['borrower_name'].fillna('').astype(str).str.strip().replace('', pd.NA).fillna('Unknown Borrower')
    prepared['borrower_email'] = prepared['borrower_email'].fillna('').astype(str).str.strip()
    prepared['borrower_id_number'] = prepared['borrower_id_number'].fillna('').astype(str).str.strip()
    prepared['region'] = prepared['region'].fillna('unknown').astype(str).str.strip().replace('', 'unknown').str.lower()
    status_risk_map = {'active': 0.05, 'closed': 0.0, 'delinquent': 0.45, 'defaulted': 0.9, 'unknown': 0.15}
    inferred_risk = prepared['current_status'].map(status_risk_map).fillna(0.2)
    prepared['risk_score'] = pd.to_numeric(prepared['risk_score'], errors='coerce')
    prepared['risk_score'] = prepared['risk_score'].fillna(inferred_risk)
    if not prepared['risk_score'].dropna().empty and prepared['risk_score'].dropna().median() > 1:
        prepared['risk_score'] = prepared['risk_score'] / 100.0
    prepared['risk_score'] = prepared['risk_score'].clip(lower=0, upper=1)
    prepared['payment_history_json'] = prepared['payment_history_json'].apply(_normalize_payment_history)
    prepared = prepared.dropna(subset=['principal_amount', 'interest_rate', 'term_months', 'origination_date'])
    prepared['term_months'] = prepared['term_months'].astype(int)
    return prepared

def parse_payment_history(payment_history_json: str) -> list[dict[str, Any]]:
    try:
        return json.loads(payment_history_json)
    except (json.JSONDecodeError, TypeError):
        return []

def calculate_days_past_due(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def get_dpd_from_history(row):
        payment_history = parse_payment_history(row.get('payment_history_json', '[]'))
        if not payment_history:
            return 0
        overdue_days = [p.get('days_late', 0) for p in payment_history if p.get('status') in ['missed', 'defaulted'] or (p.get('status') == 'late_paid' and p.get('days_late', 0) > 30)]
        return max(overdue_days) if overdue_days else 0
    existing_dpd = pd.to_numeric(df['days_past_due'], errors='coerce').fillna(0) if 'days_past_due' in df.columns else pd.Series(0, index=df.index, dtype=float)
    derived_dpd = pd.to_numeric(df.apply(get_dpd_from_history, axis=1), errors='coerce').fillna(0) if 'payment_history_json' in df.columns else pd.Series(0, index=df.index, dtype=float)
    df['days_past_due'] = pd.concat([existing_dpd, derived_dpd], axis=1).max(axis=1)
    return df


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise ValueError(
            f"ERROR: Cannot compute percentage with zero or negative denominator. "
            f"Numerator={numerator}, Denominator={denominator}. "
            f"This indicates a data quality issue or empty dataset."
        )
    return numerator / denominator * 100


def _compute_borrower_metrics(portfolio_df: pd.DataFrame) -> tuple[int, float]:
    borrower_col = next((col for col in ('borrower_id', 'borrower_id_number', 'borrower_email', 'borrower_name') if col in portfolio_df.columns), None)
    if borrower_col is None:
        return (0, 0.0)
    borrower_series = portfolio_df[borrower_col].fillna('').astype(str).str.strip().replace({'': pd.NA, 'nan': pd.NA, 'none': pd.NA, 'unknown borrower': pd.NA}).dropna()
    active_borrowers = int(borrower_series.nunique())
    if active_borrowers <= 0:
        return (0, 0.0)
    borrower_counts = borrower_series.value_counts()
    repeat_rate = float((borrower_counts > 1).sum() / active_borrowers * 100)
    return (active_borrowers, repeat_rate)


def _compute_dpd_and_par_metrics(portfolio_df: pd.DataFrame, total_loans: int, total_portfolio: float) -> dict[str, float | int]:
    dpd_30_plus = int((portfolio_df['days_past_due'] >= 30).sum())
    dpd_60_plus = int((portfolio_df['days_past_due'] >= 60).sum())
    dpd_90_plus = int((portfolio_df['days_past_due'] >= 90).sum())
    par_30_amount = float(portfolio_df[portfolio_df['days_past_due'] >= 30]['exposure_amount'].sum())
    par_90_amount = float(portfolio_df[portfolio_df['days_past_due'] >= 90]['exposure_amount'].sum())
    # Delegate PAR rate computation to the canonical SSOT function to avoid shadow arithmetic.
    # _ssot_calculate_par raises ValueError on zero total_portfolio (fail-fast; matches backend semantics).
    total_portfolio_dec = Decimal(str(total_portfolio))
    par_30_rate = float(_ssot_calculate_par(Decimal(str(par_30_amount)), total_portfolio_dec, dpd_threshold=30))
    par_90_rate = float(_ssot_calculate_par(Decimal(str(par_90_amount)), total_portfolio_dec, dpd_threshold=90))
    return {
        'dpd_30_count': dpd_30_plus,
        'dpd_60_count': dpd_60_plus,
        'dpd_90_count': dpd_90_plus,
        'delinquency_rate_30': _safe_pct(float(dpd_30_plus), float(total_loans)),
        'delinquency_rate_60': _safe_pct(float(dpd_60_plus), float(total_loans)),
        'delinquency_rate_90': _safe_pct(float(dpd_90_plus), float(total_loans)),
        'par_30_amount': par_30_amount,
        'par_90_amount': par_90_amount,
        'par_30_rate': par_30_rate,
        'par_90_rate': par_90_rate,
    }

def calculate_portfolio_metrics(df: pd.DataFrame) -> dict[str, Any]:
    df = calculate_days_past_due(df)
    status_series = df['current_status'] if 'current_status' in df.columns else pd.Series('unknown', index=df.index)
    df['exposure_amount'] = _get_exposure_series(df)
    exposure_mask = status_series.isin(STATUS_ACTIVE_EXPOSURE)
    portfolio_df = df[exposure_mask].copy()
    total_loans_all = len(df)
    closed_loans = int((~exposure_mask).sum())
    total_portfolio = float(portfolio_df['exposure_amount'].sum())
    weighted_rate_numerator = float((portfolio_df['exposure_amount'] * portfolio_df['interest_rate']).sum())
    weighted_rate = weighted_rate_numerator / total_portfolio if total_portfolio > 0 else 0.0
    total_loans = len(portfolio_df)
    dpd_par_metrics = _compute_dpd_and_par_metrics(portfolio_df, total_loans, total_portfolio)
    risk_score_sum = float(portfolio_df['risk_score'].sum())
    expected_loss = float((portfolio_df['risk_score'] * portfolio_df['exposure_amount']).sum())
    expected_loss_rate = _safe_pct(expected_loss, total_portfolio)
    avg_risk_score = float(portfolio_df['risk_score'].mean()) if total_loans > 0 else 0.0
    default_mask = portfolio_df['current_status'] == 'defaulted'
    default_count = int(default_mask.sum())
    default_exposure = float(portfolio_df.loc[default_mask, 'exposure_amount'].sum())
    default_rate = _safe_pct(float(default_count), float(total_loans))
    loss_rate = _safe_pct(default_exposure, total_portfolio)
    scheduled_sum = float(_get_numeric_series(portfolio_df, 'total_scheduled').sum())
    collected_sum = float(_get_numeric_series(portfolio_df, 'last_payment_amount').sum())
    collections_rate = _safe_pct(collected_sum, scheduled_sum)
    default_collected_sum = float(_get_numeric_series(portfolio_df.loc[default_mask], 'last_payment_amount').sum())
    recovery_rate = _safe_pct(default_collected_sum, default_exposure)
    cash_on_hand = float(_get_numeric_series(portfolio_df, 'current_balance').sum()) if 'current_balance' in portfolio_df.columns else total_portfolio
    active_borrowers, repeat_borrower_rate = _compute_borrower_metrics(portfolio_df)
    status_dist = portfolio_df['current_status'].value_counts().to_dict()
    return {
        'total_portfolio': total_portfolio,
        'weighted_avg_rate': weighted_rate,
        'weighted_rate_numerator': weighted_rate_numerator,
        'delinquency_rate_30': float(dpd_par_metrics['delinquency_rate_30']),
        'delinquency_rate_60': float(dpd_par_metrics['delinquency_rate_60']),
        'delinquency_rate_90': float(dpd_par_metrics['delinquency_rate_90']),
        'dpd_30_count': int(dpd_par_metrics['dpd_30_count']),
        'dpd_60_count': int(dpd_par_metrics['dpd_60_count']),
        'dpd_90_count': int(dpd_par_metrics['dpd_90_count']),
        'par_30_rate': float(dpd_par_metrics['par_30_rate']),
        'par_30_amount': float(dpd_par_metrics['par_30_amount']),
        'par_90_rate': float(dpd_par_metrics['par_90_rate']),
        'par_90_amount': float(dpd_par_metrics['par_90_amount']),
        'expected_loss': expected_loss,
        'expected_loss_rate': expected_loss_rate,
        'default_count': default_count,
        'default_rate': default_rate,
        'default_exposure': default_exposure,
        'loss_rate': loss_rate,
        'collections_received': collected_sum,
        'collections_scheduled': scheduled_sum,
        'collections_rate': collections_rate,
        'default_collections': default_collected_sum,
        'recovery_rate': recovery_rate,
        'cash_on_hand': cash_on_hand,
        'active_borrowers': active_borrowers,
        'repeat_borrower_rate': repeat_borrower_rate,
        'total_loans_all': total_loans_all,
        'closed_loans': closed_loans,
        'total_loans': total_loans,
        'status_distribution': status_dist,
        'avg_loan_size': float(portfolio_df['exposure_amount'].mean()) if total_loans > 0 else 0.0,
        'risk_score_sum': risk_score_sum,
        'avg_risk_score': avg_risk_score,
    }

def render_metrics_cards(metrics: dict[str, Any]):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label='💰 Total Portfolio Value', value=f"€{metrics['total_portfolio']:,.0f}", delta=f"{metrics['total_loans']} active loans")
    with col2:
        st.metric(label='📊 Weighted Avg Rate', value=f"{metrics['weighted_avg_rate']:.2%}", delta=f"Avg: €{metrics['avg_loan_size']:,.0f}")
    with col3:
        st.metric(label='⚠️ Delinquency Rate (30+ DPD)', value=f"{metrics['delinquency_rate_30']:.1f}%", delta=f"60+: {metrics['delinquency_rate_60']:.1f}%", delta_color='inverse')
    with col4:
        st.metric(label='🎯 PAR > 30', value=f"{metrics['par_30_rate']:.2f}%", delta=f"{KPI_EXPECTED_LOSS}: {metrics['expected_loss_rate']:.2f}%", delta_color='inverse')
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(label='📉 PAR > 90', value=f"{metrics.get('par_90_rate', 0.0):.2f}%", delta=f"Loss Rate: {metrics.get('loss_rate', 0.0):.2f}%", delta_color='inverse')
    with col6:
        st.metric(label='🧯 Default Rate', value=f"{metrics.get('default_rate', 0.0):.2f}%", delta=f"{int(metrics.get('default_count', 0))} loans", delta_color='inverse')
    with col7:
        st.metric(label='💸 Collections Rate', value=f"{metrics.get('collections_rate', 0.0):.2f}%", delta=f"Recovery: {metrics.get('recovery_rate', 0.0):.2f}%")
    with col8:
        st.metric(label='👥 Active Borrowers', value=f"{int(metrics.get('active_borrowers', 0)):,}", delta=f"Repeat: {metrics.get('repeat_borrower_rate', 0.0):.2f}%")

def render_kpi_methodology(metrics: dict[str, Any]):
    with st.expander('📘 KPI Calculation Methodology', expanded=False):
        st.caption('Each KPI includes formula, numerator, denominator, and current value used by agents.')
        methodology_rows = _kpi_methodology_rows(metrics)
        st.dataframe(pd.DataFrame(methodology_rows), width='stretch', hide_index=True)

def create_delinquency_trend(df: pd.DataFrame) -> go.Figure:
    CHART_MODE = 'lines+markers'
    df = df.copy()
    df['origination_date'] = pd.to_datetime(df['origination_date'], format='mixed')
    df = calculate_days_past_due(df)
    df['origination_month'] = df['origination_date'].dt.to_period('M').astype(str)
    cohort_data = []
    for month in sorted(df['origination_month'].unique()):
        cohort = df[df['origination_month'] == month]
        total = len(cohort)
        dpd_30 = len(cohort[cohort['days_past_due'] >= 30])
        dpd_60 = len(cohort[cohort['days_past_due'] >= 60])
        dpd_90 = len(cohort[cohort['days_past_due'] >= 90])
        cohort_data.append({'month': month, DPD_30_PLUS: dpd_30 / total * 100 if total > 0 else 0, DPD_60_PLUS: dpd_60 / total * 100 if total > 0 else 0, DPD_90_PLUS: dpd_90 / total * 100 if total > 0 else 0})
    cohort_df = pd.DataFrame(cohort_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cohort_df['month'], y=cohort_df[DPD_30_PLUS], name='30+ Days', mode=CHART_MODE, line={'color': '#ffc107', 'width': 2}))
    fig.add_trace(go.Scatter(x=cohort_df['month'], y=cohort_df[DPD_60_PLUS], name='60+ Days', mode=CHART_MODE, line={'color': '#ff9800', 'width': 2}))
    fig.add_trace(go.Scatter(x=cohort_df['month'], y=cohort_df[DPD_90_PLUS], name='90+ Days', mode=CHART_MODE, line={'color': '#dc3545', 'width': 2}))
    fig.update_layout(title='Delinquency Trend by Origination Cohort', xaxis_title='Origination Month', yaxis_title='Delinquency Rate (%)', hovermode='x unified', height=400)
    return fig

def create_risk_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(df, x='risk_score', nbins=20, title='Risk Score Distribution', labels={'risk_score': 'Risk Score', 'count': 'Number of Loans'}, color_discrete_sequence=['#667eea'])
    fig.update_layout(xaxis_title='Risk Score', yaxis_title='Number of Loans', height=400, showlegend=False)
    return fig

def build_agent_portfolio_context(df: pd.DataFrame) -> dict[str, Any]:
    metrics = calculate_portfolio_metrics(df)
    kpi_snapshot = _kpi_snapshot_from_metrics(metrics)
    kpi_methodology = _kpi_methodology_from_metrics(metrics)
    status_counts = df['current_status'].value_counts(dropna=False).to_dict() if 'current_status' in df.columns else {}
    region_counts = df['region'].value_counts(dropna=False).head(10).to_dict() if 'region' in df.columns else {}

    def to_native(value: Any) -> Any:
        if isinstance(value, (int, float, str)) or value is None:
            return value
        if hasattr(value, 'item'):
            return value.item()
        return float(value) if isinstance(value, (int, float)) else str(value)
    portfolio_data = {'total_loans': int(metrics.get('total_loans', 0)), 'total_loans_all': int(metrics.get('total_loans_all', 0)), 'closed_loans': int(metrics.get('closed_loans', 0)), 'total_portfolio': to_native(metrics.get('total_portfolio', 0)), 'avg_interest_rate': to_native(metrics.get('weighted_avg_rate', 0)), 'delinquency_rate_30': to_native(metrics.get('delinquency_rate_30', 0)), 'delinquency_rate_60': to_native(metrics.get('delinquency_rate_60', 0)), 'delinquency_rate_90': to_native(metrics.get('delinquency_rate_90', 0)), 'par_30_rate': to_native(metrics.get('par_30_rate', 0)), 'par_90_rate': to_native(metrics.get('par_90_rate', 0)), 'default_rate': to_native(metrics.get('default_rate', 0)), 'collections_rate': to_native(metrics.get('collections_rate', 0)), 'recovery_rate': to_native(metrics.get('recovery_rate', 0)), 'loss_rate': to_native(metrics.get('loss_rate', 0)), 'expected_loss': to_native(metrics.get('expected_loss', 0)), 'expected_loss_rate': to_native(metrics.get('expected_loss_rate', 0)), 'avg_loan_size': to_native(metrics.get('avg_loan_size', 0)), 'avg_risk_score': to_native(metrics.get('avg_risk_score', 0)), 'active_borrowers': int(metrics.get('active_borrowers', 0)), 'repeat_borrower_rate': to_native(metrics.get('repeat_borrower_rate', 0)), 'cash_on_hand': to_native(metrics.get('cash_on_hand', 0)), 'status_distribution': {k: int(v) for k, v in status_counts.items()}, 'top_regions': {k: int(v) for k, v in region_counts.items()}}
    context = {'portfolio_data': portfolio_data, 'kpi_snapshot': kpi_snapshot, 'kpi_methodology': kpi_methodology}
    return Guardrails.sanitize_context(context)

def _build_local_agent_fallback(df: pd.DataFrame, metrics: dict[str, Any]) -> dict[str, Any]:
    total_loans = int(metrics.get('total_loans', 0))
    total_loans_all = int(metrics.get('total_loans_all', total_loans))
    closed_loans = int(metrics.get('closed_loans', 0))
    total_portfolio = float(metrics.get('total_portfolio', 0.0))
    weighted_rate = float(metrics.get('weighted_avg_rate', 0.0))
    delinquency_30 = float(metrics.get('delinquency_rate_30', 0.0))
    delinquency_60 = float(metrics.get('delinquency_rate_60', 0.0))
    delinquency_90 = float(metrics.get('delinquency_rate_90', 0.0))
    par_30_rate = float(metrics.get('par_30_rate', 0.0))
    par_90_rate = float(metrics.get('par_90_rate', 0.0))
    default_rate = float(metrics.get('default_rate', 0.0))
    expected_loss = float(metrics.get('expected_loss', 0.0))
    expected_loss_rate = float(metrics.get('expected_loss_rate', 0.0))
    collections_rate = float(metrics.get('collections_rate', 0.0))
    recovery_rate = float(metrics.get('recovery_rate', 0.0))
    exposure = _get_exposure_series(df)
    top_regions_series = df.assign(exposure_amount=exposure).groupby('region')['exposure_amount'].sum().sort_values(ascending=False).head(3) if 'region' in df.columns and (not df.empty) else pd.Series(dtype=float)
    top_regions_text = 'No regional breakdown available' if top_regions_series.empty else ', '.join((f'{idx}: €{val:,.0f}' for idx, val in top_regions_series.items()))
    status_distribution = metrics.get('status_distribution', {})
    if isinstance(status_distribution, dict):
        status_distribution_text = ', '.join((f'{status}: {count}' for status, count in status_distribution.items()))
    else:
        status_distribution_text = 'n/a'
    if delinquency_30 >= 12 or par_30_rate >= 8 or par_90_rate >= 4 or (expected_loss_rate >= 7):
        portfolio_risk = 'high'
    elif delinquency_30 >= 6 or par_30_rate >= 4 or default_rate >= 2 or (expected_loss_rate >= 4):
        portfolio_risk = 'moderate'
    else:
        portfolio_risk = 'low'
    risk_analysis = f'Deterministic analysis generated locally (no external LLM).\n\n1. Portfolio risk level: {portfolio_risk.upper()}.\n2. Exposure: €{total_portfolio:,.0f} across {total_loans:,} active loans ({total_loans_all:,} total, {closed_loans:,} closed).\n3. Pricing baseline: weighted average rate {weighted_rate:.2%}.\n4. Delinquency profile: 30+ DPD {delinquency_30:.2f}%, 60+ DPD {delinquency_60:.2f}%, 90+ DPD {delinquency_90:.2f}%.\n5. Capital at risk: PAR30 {par_30_rate:.2f}% and PAR90 {par_90_rate:.2f}%.\n6. Default profile: default rate {default_rate:.2f}%.\n7. Collections profile: collections {collections_rate:.2f}%, recoveries {recovery_rate:.2f}%.\n8. Expected loss: €{expected_loss:,.0f} ({expected_loss_rate:.2f}% of portfolio).\n9. Status distribution: {status_distribution_text}.\n10. Top regional concentration: {top_regions_text}.\n11. KPI formulas and numerators/denominators are attached in `kpi_methodology`.'
    compliance_findings: list[str] = []
    if delinquency_30 >= 10:
        compliance_findings.append(f'Elevated arrears signal (DPD 30+ = {delinquency_30:.2f}%) requires enhanced monitoring.')
    if delinquency_90 >= 4:
        compliance_findings.append(f'Severe delinquency (DPD 90+ = {delinquency_90:.2f}%) requires immediate collections controls.')
    if expected_loss_rate >= 6:
        compliance_findings.append(f'Expected loss rate {expected_loss_rate:.2f}% is above conservative underwriting tolerance.')
    if collections_rate < 85:
        compliance_findings.append(f'Collections rate {collections_rate:.2f}% is below operational floor (85%).')
    if not compliance_findings:
        compliance_findings.append('No hard-threshold breaches detected in deterministic checks.')
    compliance_review = 'Compliance checkpoint:\n' + '\n'.join((f'{idx}. {item}' for idx, item in enumerate(compliance_findings, start=1)))
    ops_recommendations = 'Operational actions:\n1. Prioritize collections queues for 60+ DPD loans and track cure rate weekly.\n2. Apply tighter underwriting cutoffs for high-risk cohorts (risk_score and late history).\n3. Launch regional mitigation plan for top concentration regions and cap incremental exposure.\n4. Review pricing floor against expected loss to preserve risk-adjusted margin.\n5. Recompute KPI pack daily and publish to monitoring with the same formulas.'
    trace_id = f"local-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    return {'risk_analysis': risk_analysis, 'compliance_review': compliance_review, 'ops_recommendations': ops_recommendations, '_metadata': {'scenario_name': 'loan_risk_review', 'trace_id': trace_id, 'total_cost_usd': 0.0, 'total_tokens': 0, 'steps_completed': 3}, '_agent_comments': [{'agent_role': 'risk_analyst', 'output_key': 'risk_analysis', 'comment': risk_analysis, 'tokens_used': 0, 'cost_usd': 0.0, 'latency_ms': 0.0}, {'agent_role': 'compliance', 'output_key': 'compliance_review', 'comment': compliance_review, 'tokens_used': 0, 'cost_usd': 0.0, 'latency_ms': 0.0}, {'agent_role': 'ops_optimizer', 'output_key': 'ops_recommendations', 'comment': ops_recommendations, 'tokens_used': 0, 'cost_usd': 0.0, 'latency_ms': 0.0}]}

def create_regional_heatmap(df: pd.DataFrame) -> go.Figure:
    regional_data = df.groupby('region').agg({'principal_amount': ['sum', 'count'], 'risk_score': 'mean'}).reset_index()
    regional_data.columns = ['region', 'total_amount', 'loan_count', 'avg_risk']
    regional_data['concentration'] = regional_data['total_amount'] / regional_data['total_amount'].sum() * 100
    regional_data = regional_data.sort_values('concentration', ascending=False)
    fig = px.bar(regional_data.head(10), x='region', y='concentration', color='avg_risk', title='Top 10 Regions by Portfolio Concentration', labels={'concentration': 'Portfolio %', 'avg_risk': 'Avg Risk', 'region': 'Region'}, color_continuous_scale='RdYlGn_r', text='concentration')
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(height=400, xaxis_tickangle=-45)
    return fig

def create_vintage_analysis(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df['origination_date'] = pd.to_datetime(df['origination_date'])
    df['origination_quarter'] = df['origination_date'].dt.to_period('Q').astype(str)
    vintage_data = df.groupby(['origination_quarter', 'current_status']).size().unstack(fill_value=0)
    vintage_pct = vintage_data.div(vintage_data.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    status_colors = {'current': '#28a745', 'paid-off': '#17a2b8', 'delinquent': '#ffc107', 'default': '#dc3545'}
    for status in vintage_pct.columns:
        fig.add_trace(go.Bar(name=status.title(), x=vintage_pct.index, y=vintage_pct[status], marker_color=status_colors.get(status, '#6c757d')))
    fig.update_layout(title='Vintage Analysis - Loan Status by Origination Quarter', xaxis_title='Origination Quarter', yaxis_title='Percentage (%)', barmode='stack', height=400, hovermode='x unified')
    return fig


def _run_agent_analysis(df: pd.DataFrame, metrics: dict[str, Any]) -> dict[str, Any]:
    context = build_agent_portfolio_context(df)
    has_openai_key = bool(os.getenv('OPENAI_API_KEY'))
    if has_openai_key:
        orchestrator = MultiAgentOrchestrator(provider=LLMProvider.OPENAI, enable_tracing=False)
        base_results = orchestrator.run_scenario('loan_risk_review', context)
        return _enrich_agent_results_with_kpis(base_results, metrics, 'llm_openai')
    base_results = _build_local_agent_fallback(df, metrics)
    return _enrich_agent_results_with_kpis(base_results, metrics, 'local_fallback')


def _persist_and_notify_agent_results(results: dict[str, Any]) -> None:
    st.session_state['agent_results'] = results
    emitted_events = _emit_agent_comments_to_monitoring(results)
    emitted_kpi_events = _emit_kpi_snapshot_to_monitoring(results)
    saved_outputs = _persist_agent_outputs(results)
    analysis_mode = str(results.get('_metadata', {}).get('analysis_mode', 'local_fallback'))
    if analysis_mode == 'llm_openai':
        st.success('✅ Agent analysis completed')
    else:
        st.warning('OPENAI_API_KEY is not set. Generated deterministic local analysis with full KPIs.')
    if emitted_events > 0:
        st.info(f'📝 Published {emitted_events} agent comments to monitoring feed (Grafana).')
    if emitted_kpi_events > 0:
        st.info('📊 Published KPI snapshot event to monitoring feed (Grafana).')
    elif API_BASE_SAFE is None:
        st.caption('Agent comments were generated locally. Set API_BASE_URL to publish them to Monitoring/Grafana.')
    if saved_outputs > 0:
        st.caption(f'Saved {saved_outputs} agent output files to data/agent_outputs for Agent Insights.')


def _handle_agent_button_click() -> None:
    if not st.session_state.get('data_loaded'):
        st.warning('Please upload data before running agent analysis.')
        return
    with st.spinner('Running multi-agent analysis...'):
        df = st.session_state.get('loan_data')
        if not isinstance(df, pd.DataFrame) or df.empty:
            st.warning('No valid loan data available for analysis.')
            return
        metrics = calculate_portfolio_metrics(df)
        try:
            results = _run_agent_analysis(df, metrics)
        except Exception as exc:
            fallback_results = _enrich_agent_results_with_kpis(_build_local_agent_fallback(df, metrics), metrics, 'local_fallback_after_error')
            _persist_and_notify_agent_results(fallback_results)
            st.warning('LLM agent execution failed. Deterministic local analysis was generated instead.')
            st.error(f'Original LLM error: {exc}')
            return
        _persist_and_notify_agent_results(results)


def _load_and_normalize_uploaded_frames(uploaded_files: Any) -> list[pd.DataFrame]:
    normalized_frames: list[pd.DataFrame] = []
    for uploaded_file in uploaded_files:
        raw_df = pd.read_csv(uploaded_file, low_memory=False)
        normalized_frames.append(_apply_column_aliases(_normalize_column_names(raw_df)))
    return normalized_frames

def render_sidebar() -> Any:
    st.header('📤 Upload Loan Data')
    uploaded_files = st.file_uploader('Upload one or more CSV files', type=['csv'], accept_multiple_files=True, help=f"You can upload one consolidated file or multiple partial files. Minimum required columns: {', '.join(CORE_REQUIRED_COLUMNS)}")
    st.markdown('---')
    st.header('🤖 AI Analysis')
    if st.button('🔍 Run Agent Analysis'):
        _handle_agent_button_click()
    st.markdown('---')
    st.caption('💡 Upload your own CSV to analyze the loan portfolio')
    return uploaded_files

def handle_file_upload(uploaded_files: Any) -> bool:
    if not uploaded_files:
        return False
    try:
        _process_uploaded_files(uploaded_files)
        return True
    except ValueError as exc:
        st.error(f'❌ {exc}')
        st.info('Required columns (minimum): ' + ', '.join(CORE_REQUIRED_COLUMNS) + ' | Optional columns are auto-completed.')
        return False
    except Exception as e:
        st.error(f'❌ Error loading file: {str(e)}')
        return False


def _prepare_uploaded_dataframe(uploaded_files: Any) -> pd.DataFrame:
    normalized_frames = _load_and_normalize_uploaded_frames(uploaded_files)
    merged_df = _merge_uploaded_frames(normalized_frames)
    return prepare_uploaded_data(merged_df)


def _process_uploaded_files(uploaded_files: Any) -> None:
    prepared_df = _prepare_uploaded_dataframe(uploaded_files)
    _store_uploaded_dataframe(prepared_df, uploaded_files)


def _store_uploaded_dataframe(prepared_df: pd.DataFrame, uploaded_files: Any) -> None:
    st.session_state['data_loaded'] = True
    st.session_state['loan_data'] = prepared_df
    st.success(f'✅ Data uploaded and validated successfully! Files: {len(uploaded_files)} | Rows: {len(prepared_df):,}')
    _cls_candidates = ['loan_id'] + list(BORROWER_ID_COLS) + ['principal_amount']
    _cls_cols = [c for c in _cls_candidates if c in prepared_df.columns]
    classify_df = prepared_df[_cls_cols].rename(columns={'principal_amount': 'amount'}, errors='ignore')
    for level, message in _classify_loan_id_duplicates(classify_df):
        if level == 'info':
            st.info(f'ℹ️ {message}')
        else:
            st.warning(f'⚠️ {message}')

def _render_markdown_items(title: str, items: list[str]) -> None:
    st.markdown(title)
    for item in items:
        st.markdown(f'- `{item}`')


def _render_required_columns_list(columns: list[str]) -> None:
    for column in columns:
        st.markdown(f'- `{column}`')


def render_data_format_guide():
    st.info('👆 Please upload a CSV file or load sample data from the sidebar to begin analysis')
    st.markdown('### 📋 Required Data Format')
    st.markdown('Your CSV must include these minimum columns:')
    _render_required_columns_list(['loan_id', 'principal_amount', 'interest_rate', 'term_months', 'origination_date', 'current_status'])
    st.markdown('Optional columns (auto-filled if missing):')
    col1, col2 = st.columns(2)
    with col1:
        _render_markdown_items('**Borrower Information (optional):**', ['borrower_name', 'borrower_email', 'borrower_id_number', 'region'])
    with col2:
        _render_markdown_items('**Loan Details (optional):**', ['risk_score', 'payment_history_json'])


def _render_agent_text_sections(results: dict[str, Any], metadata: dict[str, Any]) -> None:
    with st.expander('View multi-agent outputs', expanded=True):
        if results.get('risk_analysis'):
            st.markdown('**Risk Analysis**')
            st.write(results['risk_analysis'])
        if results.get('compliance_review'):
            st.markdown('**Compliance Review**')
            st.write(results['compliance_review'])
        if results.get('ops_recommendations'):
            st.markdown('**Ops Recommendations**')
            st.write(results['ops_recommendations'])
        if metadata:
            st.caption(f"Trace ID: {metadata.get('trace_id', 'n/a')} | Mode: {metadata.get('analysis_mode', 'n/a')}")


def _render_agent_kpi_basis(results: dict[str, Any], metrics: dict[str, Any]) -> None:
    with st.expander('KPI basis used in agent analysis', expanded=False):
        methodology = results.get('kpi_methodology')
        rows = [
            {'KPI': kpi_id, 'Formula': details.get('formula', 'n/a'), 'Numerator': details.get('numerator', 'n/a'), 'Denominator': details.get('denominator', 'n/a'), 'Value': details.get('value', 'n/a'), 'Unit': details.get('unit', 'n/a')}
            for kpi_id, details in methodology.items()
            if isinstance(details, dict)
        ] if isinstance(methodology, dict) and methodology else _kpi_methodology_rows(metrics)
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)


def _resolve_segment_status_column(df: pd.DataFrame) -> str | None:
    status_col = 'current_status' if 'current_status' in df.columns else None
    if status_col is None and 'status' in df.columns:
        status_col = 'status'
    return status_col


def _build_segment_row(grp: pd.DataFrame, exposure_col: str, dpd_col: str | None, status_col: str | None, seg_val: Any) -> dict[str, Any] | None:
    total = grp[exposure_col].sum()
    if total <= 0:
        return None
    row: dict[str, Any] = {'Segment': seg_val, 'Loans': len(grp), SEG_OUTSTANDING: round(total, 0)}
    if dpd_col:
        row[SEG_PAR_30] = round(float(grp.loc[grp[dpd_col] >= 30, exposure_col].sum()) / total * 100, 2)
        row[SEG_PAR_60] = round(float(grp.loc[grp[dpd_col] >= 60, exposure_col].sum()) / total * 100, 2)
        row[SEG_PAR_90] = round(float(grp.loc[grp[dpd_col] >= 90, exposure_col].sum()) / total * 100, 2)
    if status_col:
        defaulted = grp[status_col].astype(str).str.contains('default|charged', case=False, na=False).sum()
        row[SEG_DEFAULT_RATE] = round(float(defaulted) / len(grp) * 100, 2)
    return row


def _render_segment_par_chart(seg_df: pd.DataFrame, dim_label: str) -> None:
    if SEG_PAR_30 not in seg_df.columns:
        return
    fig = px.bar(seg_df, x='Segment', y=[SEG_PAR_30, SEG_PAR_60, SEG_PAR_90], barmode='group', title=f'PAR 30 / 60 / 90 by {dim_label}', color_discrete_map={SEG_PAR_30: '#ffc107', SEG_PAR_60: '#ff9800', SEG_PAR_90: '#dc3545'}, height=380)
    fig.update_layout(xaxis_tickangle=-30, legend_title_text='')
    st.plotly_chart(fig, width='stretch')


def _render_segment_secondary_charts(seg_df: pd.DataFrame, dim_label: str) -> None:
    col1, col2 = st.columns(2)
    with col1:
        outstanding_fig = px.bar(seg_df, x='Segment', y=SEG_OUTSTANDING, title=f'Outstanding Balance by {dim_label}', color=SEG_OUTSTANDING, color_continuous_scale='Blues', height=340)
        outstanding_fig.update_layout(xaxis_tickangle=-30, showlegend=False)
        st.plotly_chart(outstanding_fig, width='stretch')
    with col2:
        if SEG_DEFAULT_RATE in seg_df.columns:
            default_fig = px.bar(seg_df, x='Segment', y=SEG_DEFAULT_RATE, title=f'Default Rate by {dim_label}', color=SEG_DEFAULT_RATE, color_continuous_scale='Reds', height=340)
            default_fig.update_layout(xaxis_tickangle=-30, showlegend=False)
            st.plotly_chart(default_fig, width='stretch')

def render_agent_results(metrics: dict[str, Any]):
    if 'agent_results' not in st.session_state:
        st.info('Run `Agent Analysis` to generate risk, compliance, and operations outputs.')
        return
    st.markdown('### 🤖 AI Analysis Results')
    results = st.session_state.get('agent_results', {})
    metadata = results.get('_metadata', {}) if isinstance(results.get('_metadata'), dict) else {}
    kpi_snapshot = results.get('kpi_snapshot')
    if not isinstance(kpi_snapshot, dict) or not kpi_snapshot:
        kpi_snapshot = _kpi_snapshot_from_metrics(metrics)
    cols = st.columns(4)
    cols[0].metric('Portfolio', f"€{float(kpi_snapshot.get('total_portfolio', 0.0)):,.0f}")
    cols[1].metric(DPD_30_PLUS, f"{float(kpi_snapshot.get('delinquency_rate_30', 0.0)):.2f}%")
    cols[2].metric('PAR 30', f"{float(kpi_snapshot.get('par_30_rate', 0.0)):.2f}%")
    cols[3].metric(KPI_EXPECTED_LOSS, f"€{float(kpi_snapshot.get('expected_loss', 0.0)):,.0f}")
    _render_agent_text_sections(results, metadata)
    _render_agent_kpi_basis(results, metrics)

def render_segment_breakdown(df: pd.DataFrame) -> None:
    st.subheader('🏷️ Segment Risk Breakdown')
    segment_dims = {'company': 'Company', 'credit_line': 'Credit Line', 'kam_hunter': 'KAM Hunter', 'kam_farmer': 'KAM Farmer', 'dpd_bucket': 'DPD Bucket'}
    if 'current_status' in df.columns:
        segment_dims['current_status'] = 'Loan Status'
    elif 'status' in df.columns:
        segment_dims['status'] = 'Loan Status'
    available_dims = {k: v for k, v in segment_dims.items() if k in df.columns}
    if not available_dims:
        st.info('No segment dimension columns found in the current dataset.')
        return
    dim_label = st.selectbox('Segment dimension', options=list(available_dims.values()), index=0, key='seg_dim_select')
    dim_col = next((k for k, v in available_dims.items() if v == dim_label))
    exposure_col = next((c for c in ('outstanding_balance', 'current_balance', 'principal_amount') if c in df.columns), None)
    dpd_col = next((c for c in ('days_past_due', 'dpd') if c in df.columns), None)
    status_col = _resolve_segment_status_column(df)
    if exposure_col is None:
        st.warning('No balance column found for segment analysis.')
        return
    work = df.copy()
    work[exposure_col] = pd.to_numeric(work[exposure_col], errors='coerce').fillna(0.0)
    if dpd_col:
        work[dpd_col] = pd.to_numeric(work[dpd_col], errors='coerce').fillna(0.0)
    rows = []
    for seg_val, grp in work.groupby(dim_col, sort=False):
        if (row := _build_segment_row(grp, exposure_col, dpd_col, status_col, seg_val)) is not None:
            rows.append(row)
    if not rows:
        st.info('No data for selected dimension.')
        return
    seg_df = pd.DataFrame(rows).sort_values(SEG_OUTSTANDING, ascending=False)
    _render_segment_par_chart(seg_df, dim_label)
    _render_segment_secondary_charts(seg_df, dim_label)
    st.markdown('#### Segment Detail Table')
    st.dataframe(seg_df, width='stretch', hide_index=True)

def _first_existing_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((col for col in candidates if col in df.columns), None)

def _coerce_datetime_series(df: pd.DataFrame, candidates: tuple[str, ...]) -> tuple[pd.Series, str | None]:
    col = _first_existing_column(df, candidates)
    if col is None:
        return (pd.Series(pd.NaT, index=df.index, dtype='datetime64[ns]'), None)
    return (pd.to_datetime(df[col], errors='coerce', format='mixed'), col)

def _coerce_money_series(df: pd.DataFrame, candidates: tuple[str, ...]) -> tuple[pd.Series, str | None]:
    col = _first_existing_column(df, candidates)
    if col is None:
        return (pd.Series(0.0, index=df.index, dtype=float), None)
    return (_coerce_amount(df[col]).fillna(0.0), col)


def _empty_temporal_metadata(disb_col: str | None, pay_col: str | None, principal_col: str | None, outstanding_col: str | None) -> dict[str, Any]:
    return {
        'raw_rows': 0,
        'dedup_rows': 0,
        'principal_sum': 0.0,
        'outstanding_sum': 0.0,
        'disbursement_col': disb_col,
        'payment_col': pay_col,
        'principal_col': principal_col,
        'outstanding_col': outstanding_col,
        'key_label': 'N/A',
    }


def _build_operational_temporal_key_parts(df: pd.DataFrame, work: pd.DataFrame, principal_work: pd.Series) -> tuple[list[pd.Series], str]:
    client_col = _first_existing_column(df, ('codcliente', 'client_code', 'borrower_id', 'borrower_id_number'))
    disb_num_col = _first_existing_column(df, ('numerodesembolso', 'numero_desembolso', 'codigo_desembolso', 'correlativo_de_operaciones', 'loan_id'))
    due_date_series, due_col = _coerce_datetime_series(df, ('fechacobro', 'fechapagoprogramado'))
    due_work = due_date_series.loc[work.index].dt.strftime('%Y-%m-%d').fillna('NA')
    key_parts = [_string_part(work, client_col), _string_part(work, disb_num_col), principal_work.round(2).map(lambda x: f'{x:.2f}'), due_work]
    key_label = f"Operational key: {client_col or 'NA'} + {disb_num_col or 'NA'} + principal + {due_col or 'NA'}"
    return (key_parts, key_label)


def _build_legacy_temporal_key_parts(df: pd.DataFrame, work: pd.DataFrame, principal_work: pd.Series) -> tuple[list[pd.Series], str]:
    loan_col = _first_existing_column(df, ('loan_id',))
    due_date_series, due_col = _coerce_datetime_series(df, ('fechacobro',))
    due_work = due_date_series.loc[work.index].dt.strftime('%Y-%m-%d').fillna('NA')
    key_parts = [_string_part(work, loan_col), principal_work.round(2).map(lambda x: f'{x:.2f}'), due_work]
    key_label = f"Legacy key: {loan_col or 'NA'} + principal + {due_col or 'NA'}"
    return (key_parts, key_label)


def _build_temporal_key_data(df: pd.DataFrame, work: pd.DataFrame, principal_work: pd.Series, key_strategy: str) -> tuple[list[pd.Series], str]:
    if key_strategy == 'operational_stable':
        return _build_operational_temporal_key_parts(df, work, principal_work)
    return _build_legacy_temporal_key_parts(df, work, principal_work)


def _string_part(work: pd.DataFrame, col: str | None) -> pd.Series:
    return work[col].astype(str).str.strip() if col else pd.Series('NA', index=work.index)

def _calculate_temporal_active_set(df: pd.DataFrame, cutoff: pd.Timestamp, key_strategy: str) -> tuple[pd.DataFrame, dict[str, Any], str | None]:
    disb_series, disb_col = _coerce_datetime_series(df, ('origination_date', 'fechadesembolso', 'fecha_de_desembolso'))
    if disb_col is None:
        return (pd.DataFrame(), {}, 'No disbursement date column found (expected origination_date/fechadesembolso).')
    pay_series, pay_col = _coerce_datetime_series(df, ('fecha_de_pago', 'payment_date'))
    principal_series, principal_col = _coerce_money_series(df, ('montodesembolsado', 'monto_del_desembolso', 'principal_amount', 'amount', 'monto_financiado_real_por_desembolso', 'monto_total_aprobado_por_desembolso'))
    outstanding_series, outstanding_col = _coerce_money_series(df, ('outstanding_balance', 'current_balance', 'totalsaldovigente', 'principal_amount', 'amount'))
    temporal_mask = disb_series.notna() & (disb_series <= cutoff)
    if pay_col is not None:
        temporal_mask = temporal_mask & (pay_series.isna() | (pay_series > cutoff))
    work = df.loc[temporal_mask].copy()
    if work.empty:
        return work, _empty_temporal_metadata(disb_col, pay_col, principal_col, outstanding_col), None
    principal_work = principal_series.loc[work.index].fillna(0.0)
    outstanding_work = outstanding_series.loc[work.index].fillna(0.0)
    disb_work = disb_series.loc[work.index]
    key_parts, key_label = _build_temporal_key_data(df, work, principal_work, key_strategy)
    work = work.assign(_temporal_principal=principal_work, _temporal_outstanding=outstanding_work, _temporal_disbursement_date=disb_work.dt.strftime('%Y-%m-%d').fillna('NA'))
    work['_temporal_key'] = key_parts[0].fillna('NA')
    for part in key_parts[1:]:
        work['_temporal_key'] = work['_temporal_key'] + '|' + part.fillna('NA')
    dedup = work.drop_duplicates(subset=['_temporal_key']).copy()
    metadata = {'raw_rows': len(work), 'dedup_rows': len(dedup), 'principal_sum': dedup['_temporal_principal'].sum(), 'outstanding_sum': dedup['_temporal_outstanding'].sum(), 'disbursement_col': disb_col, 'payment_col': pay_col, 'principal_col': principal_col, 'outstanding_col': outstanding_col, 'key_label': key_label}
    return dedup, metadata, None


def _render_regional_distribution(df: pd.DataFrame) -> None:
    st.markdown('#### Regional Distribution')
    regional_summary = df.groupby('region').agg({'principal_amount': 'sum', 'loan_id': 'count', 'risk_score': 'mean'}).round(2)
    regional_summary.columns = ['Total Amount (€)', 'Loan Count', 'Avg Risk']
    regional_summary = regional_summary.sort_values('Total Amount (€)', ascending=False)
    st.dataframe(regional_summary, width='stretch')


def _render_delinquency_tab(df: pd.DataFrame, metrics: dict[str, Any]) -> None:
    st.plotly_chart(create_delinquency_trend(df), width='stretch')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(DPD_30_PLUS, f"{metrics['delinquency_rate_30']:.1f}%")
    with col2:
        st.metric('DPD 60+', f"{metrics['delinquency_rate_60']:.1f}%")
    with col3:
        st.metric('DPD 90+', f"{metrics['delinquency_rate_90']:.1f}%")


def _render_risk_tab(df: pd.DataFrame, metrics: dict[str, Any]) -> None:
    st.plotly_chart(create_risk_distribution(df), width='stretch')
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Average Risk Score', f"{metrics['avg_risk_score']:.4f}")
    with col2:
        st.metric(KPI_EXPECTED_LOSS, f"€{metrics['expected_loss']:,.0f}")


def _render_vintage_tab(df: pd.DataFrame) -> None:
    st.plotly_chart(create_vintage_analysis(df), width='stretch')
    st.markdown('#### Status Distribution')
    status_counts = df['current_status'].value_counts()
    status_pct = (status_counts / len(df) * 100).round(1)
    col1, col2, col3, col4 = st.columns(4)
    for i, (status, count) in enumerate(status_counts.items()):
        col = [col1, col2, col3, col4][i % 4]
        with col:
            st.metric(status.title(), f'{count} ({status_pct[status]:.1f}%)')

def render_temporal_active_set(df: pd.DataFrame) -> None:
    st.subheader('⏱️ Temporal Active Set')
    st.caption('Definition: disbursement_date <= cutoff and (payment_date is null or payment_date > cutoff). Use this to reconcile principal disbursed pending payment.')
    disb_dates, disb_col = _coerce_datetime_series(df, ('origination_date', 'fechadesembolso', 'fecha_de_desembolso'))
    valid_disb = disb_dates.dropna()
    if disb_col is None or valid_disb.empty:
        st.warning('Temporal filter unavailable: missing disbursement dates (origination_date/fechadesembolso/fecha_de_desembolso).')
        return
    min_cutoff = valid_disb.min().date()
    max_cutoff = min(valid_disb.max().date(), datetime.now().date())
    col1, col2 = st.columns(2)
    with col1:
        cutoff_date = st.date_input('Cutoff date', value=max_cutoff, min_value=min_cutoff, max_value=max_cutoff, key='temporal_active_cutoff')
    with col2:
        key_choice = st.selectbox('Dedup key', options=['operational_stable', 'loan_legacy'], format_func=lambda x: 'Operational stable (codcliente + numerodesembolso + monto + fechacobro)' if x == 'operational_stable' else 'Legacy (loan_id + monto + fechacobro)', key='temporal_active_key_choice')
    dedup_df, metadata, error = _calculate_temporal_active_set(df, cutoff=pd.Timestamp(cutoff_date), key_strategy=key_choice)
    if error:
        st.warning(error)
        return
    metric_cols = st.columns(4)
    metric_cols[0].metric('Rows (raw)', f"{metadata['raw_rows']:,}")
    metric_cols[1].metric('Rows (dedup)', f"{metadata['dedup_rows']:,}")
    metric_cols[2].metric('Principal Pending ($)', f"{metadata['principal_sum']:,.2f}")
    metric_cols[3].metric('Outstanding Snapshot ($)', f"{metadata['outstanding_sum']:,.2f}")
    st.caption(f"Columns used: disbursement={metadata.get('disbursement_col') or 'NA'} | payment={metadata.get('payment_col') or 'NA'} | principal={metadata.get('principal_col') or 'NA'} | outstanding={metadata.get('outstanding_col') or 'NA'}")
    st.caption(metadata.get('key_label', ''))
    st.markdown('#### Temporal Active Set (Deduplicated)')
    display_cols = [col for col in ('loan_id', 'codcliente', 'numerodesembolso', 'codigo_desembolso', 'fechadesembolso', 'origination_date', 'fecha_de_pago', 'fechacobro', 'montodesembolsado', 'outstanding_balance', '_temporal_principal', '_temporal_outstanding', '_temporal_key') if col in dedup_df.columns]
    st.dataframe(dedup_df[display_cols], width='stretch', hide_index=True)
    export_csv = dedup_df.to_csv(index=False).encode('utf-8')
    st.download_button(label='📥 Export temporal active set (CSV)', data=export_csv, file_name=f'temporal_active_set_{cutoff_date}_{key_choice}.csv', mime='text/csv')

def render_visualization_tabs(df: pd.DataFrame, metrics: dict[str, Any]):
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(['📈 Delinquency Trends', '📊 Risk Distribution', '🗺️ Regional Analysis', '📅 Vintage Analysis', '📋 Loan Table', '🏷️ Segment Breakdown', '⏱️ Temporal Active Set'])
    with tab1:
        _render_delinquency_tab(df, metrics)
    with tab2:
        _render_risk_tab(df, metrics)
    with tab3:
        st.plotly_chart(create_regional_heatmap(df), width='stretch')
        _render_regional_distribution(df)
    with tab4:
        _render_vintage_tab(df)
    with tab5:
        render_loan_table(df)
    with tab6:
        render_segment_breakdown(df)
    with tab7:
        render_temporal_active_set(df)

def render_loan_table(df: pd.DataFrame):
    st.subheader('📋 Loan Portfolio - Detailed View')
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_filter = st.multiselect('Status', options=df['current_status'].unique().tolist(), default=df['current_status'].unique().tolist())
    with col2:
        regions = sorted(df['region'].unique().tolist())
        region_filter = st.multiselect('Region', options=regions, default=[])
    with col3:
        min_amount = float(df['principal_amount'].min())
        max_amount = float(df['principal_amount'].max())
        amount_range = st.slider('Principal Amount (€)', min_value=min_amount, max_value=max_amount, value=(min_amount, max_amount), format='€%.0f')
    with col4:
        search_term = st.text_input('🔍 Search (Loan ID or Borrower)', '')
    filtered_df = df[df['current_status'].isin(status_filter)]
    if region_filter:
        filtered_df = filtered_df[filtered_df['region'].isin(region_filter)]
    filtered_df = filtered_df[(filtered_df['principal_amount'] >= amount_range[0]) & (filtered_df['principal_amount'] <= amount_range[1])]
    if search_term:
        filtered_df = filtered_df[filtered_df['loan_id'].str.contains(search_term, case=False) | filtered_df['borrower_name'].str.contains(search_term, case=False)]
    st.info(f'Showing {len(filtered_df)} of {len(df)} loans')
    display_df = filtered_df[['loan_id', 'borrower_name', 'region', 'principal_amount', 'interest_rate', 'term_months', 'origination_date', 'current_status', 'risk_score']].copy()
    display_df['principal_amount'] = display_df['principal_amount'].apply(lambda x: f'€{x:,.2f}')
    display_df['interest_rate'] = display_df['interest_rate'].apply(lambda x: f'{x:.2%}')
    display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f'{x:.4f}')
    st.dataframe(display_df, width='stretch', height=400, hide_index=True, column_config={'loan_id': st.column_config.TextColumn('Loan ID', width='small'), 'borrower_name': st.column_config.TextColumn('Borrower', width='medium'), 'region': st.column_config.TextColumn('Region', width='medium'), 'principal_amount': st.column_config.TextColumn('Principal', width='small'), 'interest_rate': st.column_config.TextColumn('Rate', width='small'), 'term_months': st.column_config.NumberColumn('Term (mo)', width='small'), 'origination_date': st.column_config.DateColumn('Orig. Date', width='small'), 'current_status': st.column_config.TextColumn('Status', width='small'), 'risk_score': st.column_config.TextColumn('Risk', width='small')})
    col1, col2 = st.columns([1, 5])
    with col1:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(label='📥 Export CSV', data=csv, file_name=f"loan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime='text/csv')

def _safe_cache_data_decorator(*decorator_args: Any, **decorator_kwargs: Any):
    cache_data = getattr(st, 'cache_data', None)
    if callable(cache_data):
        try:
            decorated = cache_data(*decorator_args, **decorator_kwargs)
            if callable(decorated):
                return decorated
        except Exception as exc:
            logger.debug('cache_data fallback activated: %s', exc)

    def _identity(fn):
        return fn
    return _identity

@_safe_cache_data_decorator(ttl=60, show_spinner=False)
def _fetch_nsm_data(api_url: str) -> dict | None:
    parsed = urlparse(api_url)
    base_url = f'{parsed.scheme}://{parsed.netloc}' if parsed.netloc else ''
    if parsed.hostname:
        host_port = parsed.hostname
        if parsed.port:
            host_port = f'{host_port}:{parsed.port}'
        log_base_url = f'{parsed.scheme}://{host_port}'
    else:
        log_base_url = '<unknown>'
    if sanitize_api_base(base_url) is None:
        logger.warning('Blocked NSM fetch: invalid or unsafe URL base: %s', log_base_url)
        return None
    try:
        resp = requests.get(api_url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning('NSM API call failed for base %s: %s', log_base_url, exc)
        return None

def render_nsm_section() -> None:
    st.markdown('### 🌟 North Star Metric — Recurrent TPV')
    if API_BASE_SAFE is None:
        st.warning('API base URL is not configured. Set API_BASE_URL to enable this section.')
        return
    nsm_url = f"{API_BASE_SAFE.rstrip('/')}/analytics/nsm"
    data = _fetch_nsm_data(nsm_url)
    if data is None:
        st.info('NSM data not available.')
        return
    latest_period = data.get('latest_period')
    latest = data.get('latest') or {}
    by_period = data.get('by_period') or {}
    if not latest_period:
        st.info('No NSM data found. Run the pipeline to generate recurrent TPV metrics.')
        return
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Period', latest_period)
    col2.metric('Recurrent TPV', f"${latest.get('tpv_recurrent', 0):,.2f}")
    col3.metric('New TPV', f"${latest.get('tpv_new', 0):,.2f}")
    col4.metric('Recovered TPV', f"${latest.get('tpv_recovered', 0):,.2f}")
    col5, col6, col7, col8 = st.columns(4)
    col5.metric('Active Clients', latest.get('active_clients', 0))
    col6.metric('Recurrent Clients', latest.get('recurrent_clients', 0))
    col7.metric('New Clients', latest.get('new_clients', 0))
    col8.metric('Recovered Clients', latest.get('recovered_clients', 0))
    if by_period:
        chart_data = {p: {'Total TPV': m.get('tpv_total', 0), 'Recurrent TPV': m.get('tpv_recurrent', 0), 'New TPV': m.get('tpv_new', 0), 'Recovered TPV': m.get('tpv_recovered', 0)} for p, m in sorted(by_period.items())}
        chart_df = pd.DataFrame.from_dict(chart_data, orient='index')
        chart_df.index.name = 'Period'
        st.line_chart(chart_df)

def main():
    st.markdown('<p class="main-header">📊 Loans Analytics Dashboard</p>', unsafe_allow_html=True)
    with st.sidebar:
        uploaded_files = render_sidebar()
    if uploaded_files and not handle_file_upload(uploaded_files):
        return
    if 'data_loaded' not in st.session_state or not st.session_state['data_loaded']:
        render_data_format_guide()
        return
    df = st.session_state['loan_data']
    metrics = calculate_portfolio_metrics(df)
    st.markdown('### 📊 Key Portfolio Metrics')
    render_metrics_cards(metrics)
    render_kpi_methodology(metrics)
    render_agent_results(metrics)
    st.markdown('---')
    render_nsm_section()
    st.markdown('---')
    render_visualization_tabs(df, metrics)
if __name__ == '__main__':
    main()
