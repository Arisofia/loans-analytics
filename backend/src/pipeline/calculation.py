import logging
import importlib
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler

getcontext().rounding = ROUND_HALF_UP

from backend.src.kpi_engine.engine import flatten_metric_result_groups, run_metric_engine
from backend.src.kpi_engine.risk import compute_default_rate_by_count


def _load_optional_callable(module_path: str, attr_name: str) -> Any | None:
    try:
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name, None)
        return value if callable(value) else None
    except Exception:
        return None


_ltv_fn = _load_optional_callable("backend.loans_analytics.kpis.ltv", "calculate_ltv_sintetico")
if _ltv_fn is not None:
    calculate_ltv_sintetico = _ltv_fn
else:

    def calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
        if 'ltv_sintetico' in df.columns:
            return pd.to_numeric(df['ltv_sintetico'], errors='coerce').fillna(0.0)
        return pd.Series(0.0, index=df.index, dtype=float)

_asset_quality_fn = _load_optional_callable(
    "backend.loans_analytics.kpis.ssot_asset_quality",
    "calculate_asset_quality_metrics",
)
if _asset_quality_fn is not None:
    calculate_asset_quality_metrics = _asset_quality_fn
else:

    def calculate_asset_quality_metrics(
        *,
        balance: pd.Series,
        dpd: pd.Series,
        status: Optional[pd.Series] = None,
        actor: str = 'pipeline.segment_analytics',
        metric_aliases: Optional[list[str]] = None,
    ) -> dict[str, float]:
        balance_num = pd.to_numeric(balance, errors='coerce').fillna(0.0)
        dpd_num = pd.to_numeric(dpd, errors='coerce').fillna(0.0)
        total = float(balance_num.sum())
        if total <= 0:
            return {'par30': 0.0, 'par60': 0.0, 'par90': 0.0}
        return {
            'par30': float(balance_num[dpd_num >= 30].sum() / total * 100.0),
            'par60': float(balance_num[dpd_num >= 60].sum() / total * 100.0),
            'par90': float(balance_num[dpd_num >= 90].sum() / total * 100.0),
        }
try:
    import umap
    _UMAP_AVAILABLE = True
except ImportError:
    _UMAP_AVAILABLE = False
try:
    import hdbscan as hdbscan_module
    _HDBSCAN_AVAILABLE = True
except ImportError:
    _HDBSCAN_AVAILABLE = False

def _quartile_fallback_labels(x_fallback: np.ndarray, metrics: Dict[str, Any]) -> np.ndarray:
    logger.info('HDBSCAN not available — using quartile-based fallback labels.')
    n = x_fallback.shape[0]
    labels = np.zeros(n, dtype=int)
    quartiles = np.percentile(x_fallback[:, 0], [25, 50, 75])
    for i, q in enumerate(quartiles, start=1):
        labels[x_fallback[:, 0] > q] = i
    metrics['hdbscan_fallback'] = 'pc1_quartile_split'
    return labels

def _compute_cluster_profile(cluster_rows: pd.DataFrame) -> tuple[Dict[str, Any], float]:
    centroid: Dict[str, Any] = {}
    risk_dims: List[float] = []
    for feat in _COHORT_FEATURE_COLS:
        if feat not in cluster_rows.columns:
            continue
        vals = pd.to_numeric(cluster_rows[feat], errors='coerce').dropna()
        if vals.empty:
            continue
        mean_val = float(vals.mean())
        centroid[feat] = round(mean_val, 6)
        risk_dims.append(-mean_val if feat == 'ratio_pago_real' else mean_val)
    risk_score = float(np.mean(risk_dims)) if risk_dims else 0.0
    return (centroid, risk_score)

def _assign_cluster_cohorts(risk_scores: Dict[int, float], centroids: Dict[int, Dict[str, Any]]) -> Dict[int, str]:
    sorted_clusters = sorted(risk_scores.keys(), key=lambda cluster_id: risk_scores[cluster_id])
    cohort_map: Dict[int, str] = {}
    n_labels = len(_COHORT_LABELS)
    for rank, cluster_id in enumerate(sorted_clusters):
        label_idx = min(rank * n_labels // max(len(sorted_clusters), 1), n_labels - 1)
        cohort_name = _COHORT_LABELS[label_idx]
        cohort_map[cluster_id] = cohort_name
        centroids[cluster_id]['cohort'] = cohort_name
        centroids[cluster_id]['composite_risk_score'] = round(risk_scores[cluster_id], 6)
    return cohort_map
__all__ = ['CalculationPhase']
logger = logging.getLogger(__name__)
_COHORT_LABELS = ['Alfa', 'Beta', 'Gamma', 'Delta']
_COHORT_FEATURE_COLS = ['ltv_sintetico', 'dpd_adjusted', 'vd_bps_month', 'ratio_pago_real']


class _CanonicalKPIAuditAdapter:

    def __init__(self, metrics_flat: Dict[str, float]) -> None:
        self._records = [
            {
                'kpi_name': metric_key,
                'status': 'success',
                'value': metric_value,
                'timestamp': datetime.now().isoformat(),
            }
            for metric_key, metric_value in metrics_flat.items()
        ]

    def get_audit_trail(self) -> pd.DataFrame:
        return pd.DataFrame(self._records)

    def get_audit_records(self) -> List[dict[str, Any]]:
        return list(self._records)

class CalculationPhase:

    def __init__(self, config: Dict[str, Any], kpi_definitions: Dict[str, Any]):
        self.config = config
        self.kpi_definitions = kpi_definitions
        self.engine: Any | None = None

    @staticmethod
    def _log_and_raise_critical_error(error_msg: str) -> None:
        logger.error(error_msg)
        raise ValueError(error_msg)

    def execute(self, clean_data_path: Optional[Path]=None, df: Optional[pd.DataFrame]=None) -> Dict[str, Any]:
        if df is None:
            if clean_data_path and Path(clean_data_path).exists():
                df = pd.read_parquet(clean_data_path)
            else:
                raise ValueError('CRITICAL: CalculationPhase.execute requires either a DataFrame or a valid clean_data_path.')
        results = self.process(df)
        results['status'] = 'success'
        results['kpi_engine'] = self.engine
        return results

    def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            error_msg = 'CRITICAL: EMPTY DATAFRAME PROVIDED TO CALCULATIONPHASE'
            self._log_and_raise_critical_error(error_msg)
        try:
            kpi_results = self._run_unified_kpi_calculation(df)
            segments = self._calculate_segment_kpis(df)
            time_series = self._calculate_time_series(df)
            client_tpv_timeseries = self._build_client_tpv_timeseries(df)
            nsm_recurrent_tpv = self._calculate_recurrent_tpv(client_tpv_timeseries)
            clustering_metrics = self._run_advanced_clustering(df)
            anomalies = self._detect_anomalies(kpi_results)
            expected_loss = self._calculate_expected_loss(df)
            roll_rates = self._calculate_roll_rates(df)
            vintage_analysis = self._calculate_vintage_analysis(df)
            concentration_hhi = self._calculate_concentration_hhi(df)
            manifest = self._generate_manifest(kpi_results, df)
            return {'kpis': kpi_results, 'segments': segments, 'segment_kpis': segments, 'time_series': time_series, 'nsm_recurrent_tpv': nsm_recurrent_tpv, 'anomalies': anomalies, 'clustering_metrics': clustering_metrics, 'expected_loss': expected_loss, 'roll_rates': roll_rates, 'vintage_analysis': vintage_analysis, 'concentration_hhi': concentration_hhi, 'manifest': manifest}
        except Exception as e:
            logger.error('CalculationPhase failure: %s', e, exc_info=True)
            raise ValueError(f'CRITICAL: KPI calculation pipeline failed: {e}') from e

    def _calculate_time_series(self, df: pd.DataFrame) -> Dict[str, List]:
        logger.info('Calculating time-series rollups')
        result = self._empty_time_series_result()
        date_columns = self._find_date_columns(df)
        if not date_columns:
            logger.debug('No date columns found for time-series analysis')
            return result
        date_col = date_columns[0]
        df_ts = self._prepare_time_series_dataframe(df, date_col)
        if df_ts.empty:
            return result
        numeric_cols = self._get_time_series_numeric_columns(df_ts)
        if not numeric_cols:
            return result
        result['daily'] = self._rollup_sum(df_ts, date_col, numeric_cols, 'daily', 30)
        result['weekly'] = self._rollup_sum(df_ts, date_col, numeric_cols, 'weekly', 12)
        result['monthly'] = self._rollup_sum(df_ts, date_col, numeric_cols, 'monthly', 12)
        logger.info('Time-series calculated: %d daily, %d weekly, %d monthly', len(result['daily']), len(result['weekly']), len(result['monthly']))
        return result

    @staticmethod
    def _empty_time_series_result() -> Dict[str, List[Dict[str, Any]]]:
        return {'daily': [], 'weekly': [], 'monthly': []}

    def _find_date_columns(self, df: pd.DataFrame) -> List[str]:
        _KNOWN_DATE_COLS = frozenset({'disbursement_date', 'origination_date', 'due_date', 'payment_date', 'measurement_date', 'approved_at', 'funded_at', 'created_at', 'updated_at'})
        date_name_pattern = re.compile('(^date|_date$|_at$|_ts$|^fecha|_fecha$)', re.IGNORECASE)
        date_columns: List[str] = []
        for col in df.columns:
            dtype = df[col].dtype
            dtype_str = str(dtype)
            is_datetime = dtype_str.startswith('datetime64')
            is_string = dtype_str in {'object', 'str'} or dtype_str.startswith('string')
            if not is_datetime and (not is_string):
                continue
            if is_datetime:
                date_columns.append(col)
                continue
            if col not in _KNOWN_DATE_COLS and (not date_name_pattern.search(col)):
                continue
            try:
                parsed = pd.to_datetime(df[col], errors='coerce', format='mixed')
                if parsed.notna().any():
                    date_columns.append(col)
            except Exception as exc:
                logger.debug('Skipping non-date column %s: %s', col, exc)
        return date_columns

    @staticmethod
    def _prepare_time_series_dataframe(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors='coerce', format='mixed')
        return df_ts.dropna(subset=[date_col])

    @staticmethod
    def _get_time_series_numeric_columns(df_ts: pd.DataFrame) -> List[str]:
        if (numeric_cols := df_ts.select_dtypes(include=[np.number]).columns.tolist()):
            return numeric_cols
        return ['amount'] if 'amount' in df_ts.columns else []

    @staticmethod
    def _build_client_tpv_timeseries(df: pd.DataFrame) -> pd.DataFrame:
        empty = pd.DataFrame(columns=['period', 'client_id', 'tpv'])
        if df.empty:
            return empty
        client_col = next((col for col in ('client_id', 'borrower_id') if col in df.columns), None)
        date_col = next((col for col in ('origination_date', 'FechaDesembolso') if col in df.columns), None)
        amount_col = next((col for col in ('amount', 'MontoDesembolsado') if col in df.columns), None)
        if not client_col or not date_col or (not amount_col):
            return empty
        work = df[[client_col, date_col, amount_col]].copy()
        work['_date'] = pd.to_datetime(work[date_col], errors='coerce', format='mixed')
        work = work.dropna(subset=['_date'])
        if work.empty:
            return empty
        work['period'] = work['_date'].dt.to_period('M').astype(str)
        work['tpv'] = pd.to_numeric(work[amount_col], errors='coerce').fillna(0.0)
        work = work.rename(columns={client_col: 'client_id'})
        result = work.groupby(['period', 'client_id'], as_index=False)['tpv'].sum()
        return result[['period', 'client_id', 'tpv']]

    @staticmethod
    def _calculate_recurrent_tpv(timeseries: pd.DataFrame) -> Dict[str, Any]:
        if timeseries.empty or 'period' not in timeseries.columns:
            return {}
        periods = sorted(timeseries['period'].dropna().unique().tolist())
        if not periods:
            return {}
        by_period: Dict[str, Dict[str, Any]] = {}
        ever_seen: set[str] = set()
        prev_active: set[str] = set()
        for period in periods:
            period_df = timeseries[timeseries['period'] == period].copy()
            if period_df.empty:
                continue
            period_df['tpv'] = pd.to_numeric(period_df['tpv'], errors='coerce').fillna(0.0)
            current_clients = set(period_df['client_id'].dropna().astype(str).unique().tolist())
            new_clients = current_clients - ever_seen
            recurrent_clients = current_clients & prev_active
            recovered_clients = current_clients - prev_active - new_clients
            tpv_by_client = period_df.groupby('client_id', dropna=False)['tpv'].sum().to_dict()
            tpv_new = round(sum((float(tpv_by_client.get(client, 0.0)) for client in new_clients)), 2)
            tpv_recurrent = round(sum((float(tpv_by_client.get(client, 0.0)) for client in recurrent_clients)), 2)
            tpv_recovered = round(sum((float(tpv_by_client.get(client, 0.0)) for client in recovered_clients)), 2)
            tpv_total = round(float(period_df['tpv'].sum()), 2)
            by_period[period] = {'tpv_total': tpv_total, 'tpv_new': tpv_new, 'tpv_recurrent': tpv_recurrent, 'tpv_recovered': tpv_recovered, 'active_clients': len(current_clients), 'new_clients': len(new_clients), 'recurrent_clients': len(recurrent_clients), 'recovered_clients': len(recovered_clients)}
            ever_seen |= current_clients
            prev_active = current_clients
        if not by_period:
            return {}
        latest_period = sorted(by_period.keys())[-1]
        return {'by_period': by_period, 'latest_period': latest_period, 'latest': by_period[latest_period]}

    def _rollup_sum(self, df_ts: pd.DataFrame, date_col: str, numeric_cols: List[str], period: str, limit: int) -> List[Dict[str, Any]]:
        try:
            if period == 'daily':
                grouped = df_ts.groupby(df_ts[date_col].dt.date)[numeric_cols].sum()
            elif period == 'weekly':
                grouped = df_ts.groupby(df_ts[date_col].dt.to_period('W'))[numeric_cols].sum()
            else:
                grouped = df_ts.groupby(df_ts[date_col].dt.to_period('M'))[numeric_cols].sum()
            return grouped.reset_index().to_dict('records')[:limit]
        except Exception as exc:
            raise ValueError(f"CRITICAL: {period.capitalize()} rollup failed for column '{date_col}': {exc}") from exc

    def _detect_anomalies(self, kpi_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies: List[Dict[str, Any]] = []
        try:
            normal_ranges = self._default_anomaly_ranges()
            for kpi_name, kpi_value in kpi_results.items():
                anomaly = self._build_anomaly_record(kpi_name, kpi_value, normal_ranges)
                if anomaly is None:
                    continue
                anomalies.append(anomaly)
                min_val, max_val = anomaly['expected_range']
                logger.warning('Anomaly detected in %s: %s (expected: %s-%s)', kpi_name, anomaly['value'], min_val, max_val)
            if anomalies:
                logger.info('Detected %d KPI anomalies', len(anomalies))
        except Exception as e:
            logger.error('Anomaly detection failed: %s', e, exc_info=True)
            raise ValueError(f'CRITICAL: Anomaly pipeline failure: {e}') from e
        return anomalies

    @staticmethod
    def _default_anomaly_ranges() -> Dict[str, tuple[float, float]]:
        return {'par_30': (0, 30), 'par_90': (0, 15), 'default_rate': (0, 4), 'portfolio_yield': (5, 15)}

    @staticmethod
    def _build_anomaly_record(kpi_name: str, kpi_value: Any, normal_ranges: Dict[str, tuple[float, float]]) -> Optional[Dict[str, Any]]:
        if kpi_value is None or not isinstance(kpi_value, (int, float)):
            return None
        if kpi_name not in normal_ranges:
            logger.debug("KPI '%s' has no anomaly range registered — anomaly monitoring skipped for this metric", kpi_name)
            return None
        min_val, max_val = normal_ranges[kpi_name]
        if min_val <= kpi_value <= max_val:
            return None
        return {'kpi_name': kpi_name, 'value': kpi_value, 'expected_range': (min_val, max_val), 'severity': 'critical' if abs(kpi_value - max_val) > max_val * 0.5 else 'warning'}

    def _calculate_segment_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        segment_dims = self._available_segment_dimensions(df)
        if not segment_dims:
            return {}
        balance_col = self._resolve_col(df, 'outstanding_balance', 'current_balance', 'amount')
        dpd_col = self._resolve_col(df, 'dpd', 'days_past_due')
        status_col = 'status' if 'status' in df.columns else None
        if balance_col is None:
            error_msg = 'CRITICAL: MISSING BALANCE COLUMN FOR SEGMENT CALCULATION'
            self._log_and_raise_critical_error(error_msg)
        work = self._prepare_segment_workframe(df, balance_col, dpd_col, status_col)  # type: ignore[arg-type]
        if work.empty:
            return {}
        return {dim: self._calculate_dimension_segment_kpis(work, dim, balance_col, dpd_col, status_col) for dim in segment_dims}  # type: ignore[arg-type]

    @staticmethod
    def _available_segment_dimensions(df: pd.DataFrame) -> List[str]:
        dimensions = []
        if 'company' in df.columns or 'empresa' in df.columns:
            dimensions.append('company')
        if any((c in df.columns for c in ('credit_line', 'lineacredito', 'linea_credito'))):
            dimensions.append('credit_line')
        if 'kam_hunter' in df.columns or 'cod_kam_hunter' in df.columns:
            dimensions.append('kam_hunter')
        if any((c in df.columns for c in ('kam_farmer', 'cod_kam_farmer', 'farmer'))):
            dimensions.append('kam_farmer')
        if any((c in df.columns for c in ('gov', 'ministry', 'ministerio'))):
            dimensions.append('gov')
        if any((c in df.columns for c in ('industry', 'industria', 'giro'))):
            dimensions.append('industry')
        if 'doc_type' in df.columns:
            dimensions.append('doc_type')
        return dimensions

    @staticmethod
    def _prepare_segment_workframe(df: pd.DataFrame, balance_col: str, dpd_col: Optional[str], status_col: Optional[str]) -> pd.DataFrame:
        active_mask = df[status_col].isin(['active', 'delinquent', 'defaulted']) if status_col else pd.Series(True, index=df.index, dtype=bool)
        work = df.loc[active_mask].copy()
        if work.empty:
            return work
        work[balance_col] = pd.to_numeric(work[balance_col], errors='coerce').fillna(0.0)
        if dpd_col:
            work[dpd_col] = pd.to_numeric(work[dpd_col], errors='coerce').fillna(0.0)
        return work

    def _calculate_dimension_segment_kpis(self, work: pd.DataFrame, dim: str, balance_col: str, dpd_col: Optional[str], status_col: Optional[str]) -> Dict[str, Any]:
        dim_result: Dict[str, Any] = {}
        dim_map = {'company': ['company', 'empresa', 'compania'], 'credit_line': ['credit_line', 'lineacredito', 'linea_credito'], 'kam_hunter': ['kam_hunter', 'cod_kam_hunter'], 'kam_farmer': ['kam_farmer', 'cod_kam_farmer', 'farmer'], 'gov': ['gov', 'ministry', 'ministerio'], 'industry': ['industry', 'industria', 'giro'], 'doc_type': ['doc_type']}
        resolved_dim = self._resolve_col(work, *dim_map.get(dim, [dim]))
        if not resolved_dim:
            return {}
        for seg_val, grp in work.groupby(resolved_dim, sort=True):
            if (seg_kpis := self._calculate_segment_group_kpis(grp, balance_col, dpd_col, status_col)):
                dim_result[str(seg_val)] = seg_kpis
        return dim_result

    def _calculate_segment_group_kpis(self, grp: pd.DataFrame, balance_col: str, dpd_col: Optional[str], status_col: Optional[str]) -> Optional[Dict[str, Any]]:
        from decimal import Decimal, ROUND_HALF_UP
        total_bal_raw = grp[balance_col].sum()
        if total_bal_raw <= 0:
            return None
        total_bal = Decimal(str(total_bal_raw)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        seg_kpis: Dict[str, Any] = {'outstanding_balance': float(total_bal), 'loan_count': len(grp)}
        if dpd_col:
            seg_kpis.update(self._calculate_segment_par_metrics(grp, balance_col, dpd_col, float(total_bal), status_col))
        if status_col:
            seg_kpis['default_rate'] = self._calculate_segment_default_rate(grp, status_col)
        return seg_kpis

    @staticmethod
    def _calculate_segment_par_metrics(grp: pd.DataFrame, balance_col: str, dpd_col: str, total_bal: float, status_col: Optional[str]=None) -> Dict[str, float]:
        if grp.empty or total_bal <= 0:
            return {'par_30': 0.0, 'par_60': 0.0, 'par_90': 0.0}
        raw_dpd = pd.to_numeric(grp[dpd_col], errors='coerce').fillna(0.0)
        if 'dpd_adjusted' in grp.columns:
            adjusted_dpd = pd.to_numeric(grp['dpd_adjusted'], errors='coerce').fillna(raw_dpd)
        else:
            adjusted_dpd = raw_dpd
        status_series = grp[status_col] if status_col else None
        ssot_metrics = calculate_asset_quality_metrics(balance=grp[balance_col], dpd=adjusted_dpd, status=status_series, actor='pipeline.segment_analytics', metric_aliases=['par30', 'par60', 'par90'])
        return {'par_30': round(float(ssot_metrics['par30']), 4), 'par_60': round(float(ssot_metrics['par60']), 4), 'par_90': round(float(ssot_metrics['par90']), 4)}

    @staticmethod
    def _calculate_segment_default_rate(grp: pd.DataFrame, status_col: str) -> float:
        if grp.empty:
            return 0.0
        canonical_ratio = compute_default_rate_by_count(
            pd.DataFrame({
                'status': grp[status_col],
                'outstanding_principal': pd.Series(1, index=grp.index, dtype='int64'),
            })
        )
        return round(float(canonical_ratio) * 100, 4)

    @staticmethod
    def _calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
        return calculate_ltv_sintetico(df)

    @staticmethod
    def _resolve_col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
        return next((c for c in candidates if c in df.columns), None)

    def _run_unified_kpi_calculation(self, df: pd.DataFrame) -> Dict[str, Any]:
        marts = self._build_canonical_marts(df)
        metric_groups = run_metric_engine(marts)
        flattened = flatten_metric_result_groups(metric_groups)
        self.engine = _CanonicalKPIAuditAdapter(flattened)
        return {k: float(v) for k, v in flattened.items()}

    @staticmethod
    def _build_canonical_marts(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        work = df.copy()

        def _series_or_default(column: str, default: Any = 0) -> pd.Series:
            if column in work.columns:
                return work[column]
            return pd.Series(default, index=work.index)

        def _first_existing_series(*columns: str, default: Any = 0) -> pd.Series:
            for column in columns:
                if column in work.columns:
                    return work[column]
            return pd.Series(default, index=work.index)

        if 'outstanding_principal' not in work.columns:
            work['outstanding_principal'] = pd.to_numeric(
                _first_existing_series('outstanding_balance', 'current_balance', 'amount', default=0),
                errors='coerce',
            ).fillna(0)
        if 'days_past_due' not in work.columns:
            work['days_past_due'] = pd.to_numeric(_series_or_default('dpd', 0), errors='coerce').fillna(0)
        if 'status' not in work.columns:
            work['status'] = 'active'
        work['default_flag'] = work['status'].astype(str).str.lower().eq('defaulted')
        if 'disbursement_amount' not in work.columns:
            work['disbursement_amount'] = pd.to_numeric(_series_or_default('amount', 0), errors='coerce').fillna(0)
        if 'disbursement_date' not in work.columns:
            work['disbursement_date'] = pd.to_datetime(
                work.get('origination_date', work.get('funded_at')),
                errors='coerce',
                format='mixed',
            )
        finance_mart = pd.DataFrame(
            {
                'interest_income': pd.to_numeric(_series_or_default('interest_income', 0), errors='coerce').fillna(0),
                'fee_income': pd.to_numeric(_series_or_default('fee_income', 0), errors='coerce').fillna(0),
                'funding_cost': pd.to_numeric(_series_or_default('funding_cost', 0), errors='coerce').fillna(0),
                'operating_expense': pd.to_numeric(_series_or_default('operating_expense', 0), errors='coerce').fillna(0),
                'provision_expense': pd.to_numeric(_series_or_default('provision_expense', 0), errors='coerce').fillna(0),
                'balance_avg': pd.to_numeric(_series_or_default('outstanding_principal', 0), errors='coerce').fillna(0),
                'debt_balance': pd.to_numeric(_series_or_default('outstanding_principal', 0), errors='coerce').fillna(0),
            }
        )
        finance_mart['gross_margin'] = (
            finance_mart['interest_income']
            + finance_mart['fee_income']
            - finance_mart['funding_cost']
            - finance_mart['operating_expense']
            - finance_mart['provision_expense']
        )
        sales_mart = pd.DataFrame(
            {
                'ticket_size': pd.to_numeric(_series_or_default('amount', 0), errors='coerce').fillna(0),
                'approved_ticket': pd.to_numeric(_first_existing_series('disbursement_amount', 'amount', default=0), errors='coerce').fillna(0),
                'funded_flag': ~work['status'].astype(str).str.lower().isin(['rejected', 'denied', 'cancelled']),
                'status': work.get('status', 'active'),
            }
        )
        return {
            'portfolio_mart': work,
            'finance_mart': finance_mart,
            'sales_mart': sales_mart,
            'disbursements_mart': work,
            'payments_mart': pd.DataFrame(),
        }

    def _calculate_expected_loss(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Expected Loss (EL = PD × LGD × EAD) per loan and portfolio total."""
        logger.info('Calculating Expected Loss (EL = PD × LGD × EAD)')
        balance_col = self._resolve_col(df, 'outstanding_balance', 'current_balance', 'amount')
        dpd_col = self._resolve_col(df, 'dpd', 'days_past_due')
        if not balance_col or not dpd_col:
            logger.warning('EL skipped: missing balance or DPD column')
            return {}
        lgd = Decimal('0.10')
        work = df.copy()
        work['_ead'] = pd.to_numeric(work[balance_col], errors='coerce').fillna(0.0)
        work['_dpd'] = pd.to_numeric(work[dpd_col], errors='coerce').fillna(0.0)
        dpd_to_pd = {0: Decimal('0.005'), 30: Decimal('0.05'), 60: Decimal('0.15'), 90: Decimal('0.35'), 180: Decimal('0.70')}

        def _assign_pd(dpd_val: float) -> Decimal:
            if dpd_val >= 180:
                return dpd_to_pd[180]
            if dpd_val >= 90:
                return dpd_to_pd[90]
            if dpd_val >= 60:
                return dpd_to_pd[60]
            if dpd_val >= 30:
                return dpd_to_pd[30]
            return dpd_to_pd[0]

        if 'status' in work.columns:
            defaulted_mask = work['status'] == 'defaulted'
        else:
            defaulted_mask = pd.Series(False, index=work.index)
        total_el = Decimal('0')
        total_ead = Decimal('0')
        pd_weighted_sum = Decimal('0')
        for _, row in work.iterrows():
            ead = Decimal(str(row['_ead']))
            if ead <= 0:
                continue
            if defaulted_mask.loc[row.name]:
                pd_i = Decimal('1.0')
            else:
                pd_i = _assign_pd(row['_dpd'])
            el_i = pd_i * lgd * ead
            total_el += el_i
            total_ead += ead
            pd_weighted_sum += pd_i * ead
        el_rate = (total_el / total_ead * 100) if total_ead > 0 else Decimal('0')
        weighted_avg_pd = (pd_weighted_sum / total_ead * 100) if total_ead > 0 else Decimal('0')
        result = {
            'total_expected_loss_usd': float(total_el.quantize(Decimal('0.01'))),
            'expected_loss_rate_pct': float(el_rate.quantize(Decimal('0.0001'))),
            'weighted_avg_pd_pct': float(weighted_avg_pd.quantize(Decimal('0.0001'))),
            'lgd_assumed_pct': float(lgd * 100),
            'total_ead_usd': float(total_ead.quantize(Decimal('0.01'))),
            'loan_count': int((work['_ead'] > 0).sum()),
        }
        logger.info('EL calculated: $%.2f (%.4f%% of EAD)', result['total_expected_loss_usd'], result['expected_loss_rate_pct'])
        return result

    def _calculate_roll_rates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate DPD bucket roll rates (balance-weighted migration matrix)."""
        logger.info('Calculating roll rates (DPD bucket transitions)')
        balance_col = self._resolve_col(df, 'outstanding_balance', 'current_balance', 'amount')
        dpd_col = self._resolve_col(df, 'dpd', 'days_past_due')
        if not balance_col or not dpd_col:
            logger.warning('Roll rates skipped: missing balance or DPD column')
            return {}
        work = df.copy()
        work['_bal'] = pd.to_numeric(work[balance_col], errors='coerce').fillna(0.0)
        work['_dpd'] = pd.to_numeric(work[dpd_col], errors='coerce').fillna(0.0)
        buckets = [('current', 0, 0), ('1-30', 1, 30), ('31-60', 31, 60), ('61-90', 61, 90), ('91-180', 91, 180), ('180+', 180, 999999)]

        def _assign_bucket(dpd_val: float) -> str:
            for name, lo, hi in buckets:
                if lo <= dpd_val <= hi:
                    return name
            return '180+'

        work['_bucket'] = work['_dpd'].apply(_assign_bucket)
        bucket_summary = {}
        for name, _, _ in buckets:
            mask = work['_bucket'] == name
            bucket_summary[name] = {
                'balance_usd': round(float(work.loc[mask, '_bal'].sum()), 2),
                'loan_count': int(mask.sum()),
                'pct_of_portfolio': 0.0,
            }
        total_bal = sum(b['balance_usd'] for b in bucket_summary.values())
        if total_bal > 0:
            for b in bucket_summary.values():
                b['pct_of_portfolio'] = round(b['balance_usd'] / total_bal * 100, 4)
        transitions = [('current', '1-30'), ('1-30', '31-60'), ('31-60', '61-90'), ('61-90', '91-180'), ('91-180', '180+')]
        roll_rate_matrix = {}
        for from_bucket, to_bucket in transitions:
            from_bal = bucket_summary[from_bucket]['balance_usd']
            to_bal = bucket_summary[to_bucket]['balance_usd']
            rate = round(to_bal / from_bal * 100, 4) if from_bal > 0 else 0.0
            roll_rate_matrix[f'{from_bucket}_to_{to_bucket}'] = {
                'from_balance': from_bal,
                'to_balance': to_bal,
                'roll_rate_pct': rate,
            }
        result = {
            'bucket_distribution': bucket_summary,
            'roll_rate_matrix': roll_rate_matrix,
            'total_portfolio_balance': round(total_bal, 2),
        }
        logger.info('Roll rates calculated across %d buckets', len(buckets))
        return result

    def _calculate_vintage_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate vintage/cohort analysis by origination month."""
        logger.info('Calculating vintage analysis by origination cohort')
        date_col = self._resolve_col(df, 'origination_date', 'FechaDesembolso', 'disbursement_date')
        balance_col = self._resolve_col(df, 'outstanding_balance', 'current_balance', 'amount')
        dpd_col = self._resolve_col(df, 'dpd', 'days_past_due')
        if not date_col:
            logger.warning('Vintage analysis skipped: no origination date column')
            return {}
        work = df.copy()
        work['_orig_date'] = pd.to_datetime(work[date_col], errors='coerce', format='mixed')
        work = work.dropna(subset=['_orig_date'])
        if work.empty:
            return {}
        work['_vintage'] = work['_orig_date'].dt.to_period('M').astype(str)
        if balance_col:
            work['_bal'] = pd.to_numeric(work[balance_col], errors='coerce').fillna(0.0)
        else:
            work['_bal'] = 1.0
        if dpd_col:
            work['_dpd'] = pd.to_numeric(work[dpd_col], errors='coerce').fillna(0.0)
        else:
            work['_dpd'] = 0.0
        status_col = 'status' if 'status' in work.columns else None
        vintage_data = {}
        for vintage, grp in work.groupby('_vintage', sort=True):
            total_bal = float(grp['_bal'].sum())
            loan_count = len(grp)
            avg_dpd = float(grp['_dpd'].mean())
            par30_bal = float(grp.loc[grp['_dpd'] >= 30, '_bal'].sum())
            par30_rate = round(par30_bal / total_bal * 100, 4) if total_bal > 0 else 0.0
            par90_bal = float(grp.loc[grp['_dpd'] >= 90, '_bal'].sum())
            par90_rate = round(par90_bal / total_bal * 100, 4) if total_bal > 0 else 0.0
            default_count = int((grp[status_col] == 'defaulted').sum()) if status_col else 0
            if status_col:
                default_rate = round(
                    float(
                        compute_default_rate_by_count(
                            pd.DataFrame(
                                {
                                    'status': grp[status_col],
                                    'outstanding_principal': pd.Series(1, index=grp.index, dtype='int64'),
                                }
                            )
                        )
                    )
                    * 100,
                    4,
                )
            else:
                default_rate = 0.0
            vintage_data[str(vintage)] = {
                'loan_count': loan_count,
                'total_balance_usd': round(total_bal, 2),
                'avg_dpd': round(avg_dpd, 2),
                'par_30_rate': par30_rate,
                'par_90_rate': par90_rate,
                'default_rate': default_rate,
                'default_count': default_count,
            }
        result = {
            'vintages': vintage_data,
            'total_vintages': len(vintage_data),
            'worst_vintage': max(vintage_data.items(), key=lambda x: x[1]['default_rate'])[0] if vintage_data else None,
            'best_vintage': min(vintage_data.items(), key=lambda x: x[1]['default_rate'])[0] if vintage_data else None,
        }
        logger.info('Vintage analysis: %d cohorts analyzed', len(vintage_data))
        return result

    def _calculate_concentration_hhi(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Herfindahl-Hirschman Index and concentration metrics."""
        logger.info('Calculating concentration HHI')
        balance_col = self._resolve_col(df, 'outstanding_balance', 'current_balance', 'amount')
        borrower_col = self._resolve_col(df, 'borrower_id', 'client_id', 'CodCliente', 'debtor_id')
        if not balance_col:
            logger.warning('Concentration HHI skipped: missing balance column')
            return {}
        work = df.copy()
        work['_bal'] = pd.to_numeric(work[balance_col], errors='coerce').fillna(0.0)
        total_bal = work['_bal'].sum()
        if total_bal <= 0:
            return {}
        if borrower_col:
            obligor_bal = work.groupby(borrower_col)['_bal'].sum().sort_values(ascending=False)
        else:
            obligor_bal = work['_bal'].sort_values(ascending=False)
        shares = obligor_bal / total_bal
        hhi = float((shares ** 2).sum() * 10000)
        top_1_pct = float(shares.iloc[0] * 100) if len(shares) > 0 else 0.0
        top_5_pct = float(shares.iloc[:5].sum() * 100) if len(shares) >= 5 else float(shares.sum() * 100)
        top_10_pct = float(shares.iloc[:10].sum() * 100) if len(shares) >= 10 else float(shares.sum() * 100)
        top_20_pct = float(shares.iloc[:20].sum() * 100) if len(shares) >= 20 else float(shares.sum() * 100)
        if hhi < 1000:
            concentration_level = 'low'
        elif hhi < 1800:
            concentration_level = 'moderate'
        elif hhi < 2500:
            concentration_level = 'high'
        else:
            concentration_level = 'very_high'
        result = {
            'hhi_index': round(hhi, 2),
            'concentration_level': concentration_level,
            'top_1_obligor_pct': round(top_1_pct, 4),
            'top_5_obligor_pct': round(top_5_pct, 4),
            'top_10_obligor_pct': round(top_10_pct, 4),
            'top_20_obligor_pct': round(top_20_pct, 4),
            'total_obligors': len(shares),
            'total_portfolio_usd': round(float(total_bal), 2),
        }
        logger.info('HHI: %.2f (%s), Top-10: %.2f%%', hhi, concentration_level, top_10_pct)
        return result

    def _generate_manifest(self, kpi_results: Dict[str, Any], source_df: pd.DataFrame) -> Dict[str, Any]:
        return {'run_timestamp': datetime.now().isoformat(), 'source_rows': len(source_df), 'kpis_calculated': list(kpi_results.keys()), 'formula_version': self.kpi_definitions.get('version', 'unknown'), 'traceability': {'source_columns': list(source_df.columns), 'calculation_engine': 'kpi_engine_v2'}}

    @staticmethod
    def _ltv_sintetico_invalid_mask(df: pd.DataFrame) -> pd.Series:
        required = {'valor_nominal_factura', 'tasa_dilucion'}
        if not required.issubset(df.columns):
            return pd.Series(dtype=bool)
        if df.empty:
            return pd.Series(False, index=df.index, dtype=bool)
        nominal = pd.to_numeric(df['valor_nominal_factura'], errors='coerce').fillna(0.0)
        dilution = pd.to_numeric(df['tasa_dilucion'], errors='coerce').fillna(0.0)
        adjusted = nominal * (1.0 - dilution)
        return adjusted.abs() < 1e-09

    @staticmethod
    def _calculate_velocity_of_default(df_ts: pd.DataFrame, default_rate_col: str='default_rate', period_col: Optional[str]=None) -> pd.Series:
        if default_rate_col not in df_ts.columns:
            return pd.Series(dtype=float)
        working = df_ts
        if period_col is not None and period_col in df_ts.columns:
            working = df_ts.sort_values(period_col)
        rate = pd.to_numeric(working[default_rate_col], errors='coerce')
        return rate.diff()

    def _compute_portfolio_velocity_of_default(self, df: pd.DataFrame) -> Optional[Decimal]:
        date_col = self._resolve_col(df, 'as_of_date', 'measurement_date', 'period')
        if date_col is None:
            return None
        work = df.copy()
        work['_period_date'] = pd.to_datetime(work[date_col], errors='coerce', format='mixed')
        work = work.dropna(subset=['_period_date'])
        if work.empty:
            return None
        if 'status' in work.columns:
            status = work['status'].astype(str).str.lower().fillna('active')
            work = work.loc[status != 'closed'].copy()
            work['_is_defaulted'] = status.loc[work.index] == 'defaulted'
        else:
            work['_is_defaulted'] = False
        if work.empty:
            return None
        work['_period'] = work['_period_date'].dt.to_period('M')
        grouped = work.groupby('_period', sort=True)['_is_defaulted'].mean() * 100.0
        if len(grouped) < 2:
            return None
        deltas = grouped.diff().dropna()
        if deltas.empty:
            return None
        return Decimal(str(round(float(deltas.iloc[-1]), 6)))

    def _run_advanced_clustering(self, df: pd.DataFrame) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {'umap_available': _UMAP_AVAILABLE, 'hdbscan_available': _HDBSCAN_AVAILABLE}
        try:
            try:
                X, feature_cols, opaque_mask = self._build_feature_matrix(df)
            except ValueError as exc:
                logger.warning('Clustering skipped: %s', exc)
                metrics['skipped'] = True
                metrics['skip_reason'] = str(exc)
                return metrics
            metrics['feature_columns'] = feature_cols
            metrics['n_opaque_excluded'] = int(opaque_mask.sum())
            if X.shape[0] < 10:
                logger.warning('Clustering skipped: insufficient non-opaque observations (%d < 10)', X.shape[0])
                metrics['skipped'] = True
                metrics['skip_reason'] = f'insufficient_observations ({X.shape[0]})'
                return metrics
            x_scaled, pca_explained = self._scale_and_reduce_pca(X)
            metrics['pca_explained_variance'] = pca_explained
            x_embed = self._apply_umap(x_scaled, metrics)
            labels = self._apply_hdbscan(x_embed, x_scaled, metrics)
            cohort_series, centroids = self._map_cohorts(df, labels, opaque_mask)
            metrics['cohort_distribution'] = cohort_series.value_counts().to_dict() if cohort_series is not None else {}
            metrics['cluster_centroids'] = centroids
        except Exception as exc:
            # Clustering is an optional enrichment step. When feature columns are
            # absent (e.g. raw data that has not been through the full transformation
            # pipeline) or any other runtime issue occurs, we degrade gracefully so
            # that the core KPIs computed earlier in process() are still returned.
            # Unexpected errors are logged at WARNING level and exposed in the
            # returned metrics dict so they remain observable.
            logger.warning(
                'Advanced clustering skipped: %s. Core KPIs are unaffected.',
                exc,
                exc_info=True,
            )
            metrics['skipped'] = True
            metrics['skip_reason'] = str(exc)
            return metrics
        return metrics

    def _build_feature_matrix(self, df: pd.DataFrame) -> tuple[np.ndarray, List[str], pd.Series]:
        feature_cols: List[str] = []
        flag_cols = sorted([c for c in df.columns if c.endswith('_is_missing') and pd.api.types.is_numeric_dtype(df[c])])
        feature_cols.extend(flag_cols)
        for col in _COHORT_FEATURE_COLS:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]) and (col not in feature_cols):
                feature_cols.append(col)
        if not feature_cols:
            raise ValueError(f'No numeric feature columns available for clustering (looked for: {_COHORT_FEATURE_COLS} + *_is_missing flags)')
        feat_df = df[feature_cols].copy()
        opaque_mask = feat_df.isna().any(axis=1)
        feat_df_clean = feat_df.loc[~opaque_mask]
        X = feat_df_clean.to_numpy(dtype=float)
        return (X, feature_cols, opaque_mask)

    @staticmethod
    def _scale_and_reduce_pca(x_input: np.ndarray) -> tuple[np.ndarray, List[float]]:
        scaler = RobustScaler()
        x_scaled = scaler.fit_transform(x_input)
        max_components = min(x_scaled.shape[1], x_scaled.shape[0] - 1, 10)
        if max_components >= 2:
            pca = PCA(n_components=0.95, svd_solver='full', random_state=42)
            x_pca = pca.fit_transform(x_scaled)
            explained = [round(float(v), 4) for v in pca.explained_variance_ratio_]
            if x_pca.shape[1] > max_components:
                x_pca = x_pca[:, :max_components]
                explained = explained[:max_components]
        else:
            pca = PCA(n_components=max_components, random_state=42)
            x_pca = pca.fit_transform(x_scaled)
            explained = [round(float(v), 4) for v in pca.explained_variance_ratio_]
        return (x_pca, explained)

    @staticmethod
    def _apply_umap(x_pca: np.ndarray, metrics: Dict[str, Any]) -> np.ndarray:
        if not _UMAP_AVAILABLE:
            logger.info('UMAP not available — using PCA output for clustering.')
            return x_pca
        try:
            reducer = umap.UMAP(n_components=2, n_neighbors=min(15, max(2, x_pca.shape[0] // 5)), min_dist=0.1, random_state=42)
            x_embed = reducer.fit_transform(x_pca)
            metrics['umap_n_components'] = 2
            return x_embed
        except Exception as exc:
            raise ValueError(f'CRITICAL: UMAP dimensionality reduction failed: {exc}') from exc

    @staticmethod
    def _apply_hdbscan(x_embed: np.ndarray, x_fallback: np.ndarray, metrics: Dict[str, Any]) -> np.ndarray:
        if not _HDBSCAN_AVAILABLE:
            return _quartile_fallback_labels(x_fallback, metrics)
        try:
            clusterer = hdbscan_module.HDBSCAN(min_cluster_size=max(5, x_embed.shape[0] // 20), min_samples=2, cluster_selection_method='eom')
            labels = clusterer.fit_predict(x_embed)
            metrics['n_clusters'] = int(len(set(labels)) - (1 if -1 in labels else 0))
            metrics['n_noise'] = int((labels == -1).sum())
            return labels
        except Exception as exc:
            raise ValueError(f'CRITICAL: HDBSCAN clustering failed: {exc}') from exc

    def _map_cohorts(self, df: pd.DataFrame, labels: np.ndarray, opaque_mask: pd.Series) -> tuple[Optional[pd.Series], Dict[int, Dict[str, Any]]]:
        non_opaque_idx = df.index[~opaque_mask]
        if len(non_opaque_idx) != len(labels):
            logger.warning('Label count (%d) != non-opaque rows (%d); skipping cohort map.', len(labels), len(non_opaque_idx))
            return (None, {})
        label_series = pd.Series(labels, index=non_opaque_idx, name='cluster_id')
        cluster_ids = sorted(set(labels))
        centroids: Dict[int, Dict[str, Any]] = {}
        risk_scores: Dict[int, float] = {}
        for cluster_id in cluster_ids:
            if cluster_id == -1:
                continue
            cluster_mask = label_series == cluster_id
            cluster_rows = df.loc[non_opaque_idx[cluster_mask.values]]
            centroid, risk_score = _compute_cluster_profile(cluster_rows)
            centroids[cluster_id] = centroid
            risk_scores[cluster_id] = risk_score
        cohort_map = _assign_cluster_cohorts(risk_scores, centroids)
        cohort_series = label_series.map(cohort_map)
        return (cohort_series, centroids)
