import json
import os
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Set
import pandas as pd
from backend.python.logging_config import get_logger
try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]
try:
    from supabase import Client, create_client
except ImportError:
    Client = None  # type: ignore[assignment,misc]
    create_client = None  # type: ignore[assignment]
if TYPE_CHECKING:
    from backend.python.kpis.engine import KPIEngineV2
logger = get_logger(__name__)
KPI_DEFINITIONS_TABLE = 'monitoring.kpi_definitions'

class OutputPhase:

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info('Initialized output phase')

    def execute(self, kpi_results: Dict[str, Any], run_dir: Optional[Path]=None, kpi_engine: Optional['KPIEngineV2']=None, segment_kpis: Optional[Dict[str, Any]]=None, time_series: Optional[Dict[str, Any]]=None, anomalies: Optional[list]=None, nsm_recurrent_tpv: Optional[Dict[str, Any]]=None, clustering_metrics: Optional[Dict[str, Any]]=None, transformation_metrics: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        logger.info('Starting Phase 4: Output')
        try:
            exports = self._export_run_outputs(kpi_results=kpi_results, run_dir=run_dir, kpi_engine=kpi_engine, segment_kpis=segment_kpis, time_series=time_series, anomalies=anomalies, nsm_recurrent_tpv=nsm_recurrent_tpv, clustering_metrics=clustering_metrics, transformation_metrics=transformation_metrics)
            if kpi_engine is not None:
                if audit_path := self._export_kpi_audit_trail(kpi_engine):
                    exports['kpi_audit_trail'] = str(audit_path)
            db_result = self._write_to_database(kpi_results)
            dashboard_result = self._trigger_dashboard_refresh()
            audit_trail = self._generate_audit_metadata(kpi_results, exports, kpi_engine)
            results = {'status': 'success', 'exports': exports, 'database_write': db_result, 'dashboard_refresh': dashboard_result, 'audit_trail': audit_trail, 'timestamp': datetime.now().isoformat()}
            logger.info(f"Output completed: {len(exports)} exports, database: {db_result['status']}")
            return results
        except Exception as e:
            logger.error('Output failed: %s', str(e), exc_info=True)
            raise RuntimeError(f'CRITICAL: Output phase failed: {e}') from e

    def _export_run_outputs(self, *, kpi_results: Dict[str, Any], run_dir: Optional[Path], kpi_engine: Optional['KPIEngineV2'], segment_kpis: Optional[Dict[str, Any]], time_series: Optional[Dict[str, Any]], anomalies: Optional[list], nsm_recurrent_tpv: Optional[Dict[str, Any]], clustering_metrics: Optional[Dict[str, Any]], transformation_metrics: Optional[Dict[str, Any]]) -> Dict[str, str]:
        exports: Dict[str, str] = {}
        if run_dir is None:
            return exports
        exports['parquet'] = str(self._export_parquet(kpi_results, run_dir))
        exports['csv'] = str(self._export_csv(kpi_results, run_dir))
        exports['kpis'] = str(self._export_payload_json(kpi_results, run_dir, 'kpis.json'))
        self._export_optional_payload(exports, 'segment_kpis', segment_kpis, run_dir, 'segment_kpis.json')
        self._export_optional_payload(exports, 'time_series', time_series, run_dir, 'time_series.json')
        self._export_optional_payload(exports, 'anomalies', anomalies, run_dir, 'anomalies.json')
        self._export_optional_payload(exports, 'clustering_metrics', clustering_metrics if clustering_metrics is not None else {}, run_dir, 'clustering_metrics.json')
        segment_snapshot_path = self._export_segment_snapshot(run_dir)
        if segment_snapshot_path is not None:
            exports['segment_snapshot'] = str(segment_snapshot_path)
        self._export_optional_payload(exports, 'nsm_recurrent_tpv', nsm_recurrent_tpv, run_dir, 'nsm_recurrent_tpv_output.json')
        audit_metadata_payload = self._build_audit_metadata_payload(kpi_results=kpi_results, exports=exports, kpi_engine=kpi_engine, transformation_metrics=transformation_metrics)
        exports['audit_metadata'] = str(self._export_payload_json(audit_metadata_payload, run_dir, 'audit_metadata.json'))
        return exports

    def _export_optional_payload(self, exports: Dict[str, str], export_key: str, payload: Any, run_dir: Path, filename: str) -> None:
        if payload is None:
            return
        exports[export_key] = str(self._export_payload_json(payload, run_dir, filename))

    def _export_parquet(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        output_path = run_dir / 'kpis_output.parquet'
        df = pd.DataFrame([kpi_results])
        df.to_parquet(output_path, index=False)
        logger.info('Exported Parquet: %s', output_path)
        return output_path

    def _export_csv(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        output_path = run_dir / 'kpis_output.csv'
        df = pd.DataFrame([kpi_results])
        financial_columns = {'amount', 'principal_amount', 'original_amount', 'current_balance', 'payment_amount', 'interest_rate'}
        for col in financial_columns:
            if col in df.columns and df[col].iloc[0] is not None:
                try:
                    value = df[col].iloc[0]
                    if isinstance(value, (int, float)):
                        decimal_val = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        df.at[0, col] = str(decimal_val)
                except (ValueError, TypeError) as e:
                    logger.warning('Could not convert %s to Decimal: %s', col, e)
        df.to_csv(output_path, index=False)
        logger.info('Exported CSV with Decimal precision: %s', output_path)
        return output_path

    def _export_json(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        output_path = run_dir / 'kpis_output.json'
        with open(output_path, 'w') as f:
            json.dump(kpi_results, f, indent=2, default=str)
        logger.info('Exported JSON: %s', output_path)
        return output_path

    def _export_payload_json(self, payload: Any, run_dir: Path, filename: str) -> Path:
        output_path = run_dir / filename
        with open(output_path, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2, default=str)
        logger.info('Exported payload: %s', output_path)
        return output_path

    def _export_segment_snapshot(self, run_dir: Path) -> Optional[Path]:
        data_path = self._resolve_segment_snapshot_source(run_dir)
        if data_path is None:
            logger.debug('Segment snapshot skipped: no clean/transformed parquet in %s', run_dir)
            return None
        df = self._read_segment_snapshot_frame(data_path)
        if df.empty:
            logger.debug('Segment snapshot skipped: source dataframe is empty')
            return None
        balance_col = self._resolve_first_column(df, ['outstanding_balance', 'current_balance', 'balance'])
        status_col = self._resolve_first_column(df, ['status', 'loan_status'])
        dpd_col = self._resolve_first_column(df, ['dpd', 'days_past_due'])
        loan_id_col = self._resolve_first_column(df, ['loan_id', 'loan_uid'])
        interest_rate_col = self._resolve_first_column(df, ['interest_rate'])
        if balance_col is None:
            logger.debug('Segment snapshot skipped: no balance column present')
            return None
        working = self._prepare_segment_snapshot_frame(df, balance_col=balance_col, status_col=status_col, dpd_col=dpd_col, interest_rate_col=interest_rate_col)
        dimension_rows = self._build_segment_snapshot_dimensions(working, loan_id_col)
        if not dimension_rows:
            logger.debug('Segment snapshot skipped: no segment rows generated')
            return None
        as_of_date = self._derive_segment_as_of_date(working)
        if as_of_date is None:
            as_of_date = datetime.now().date().isoformat()
            logger.debug('as_of_date not derivable from data; defaulting to run date %s', as_of_date)
        payload = {'generated_at': datetime.now().isoformat(), 'run_id': run_dir.name, 'source_data_path': data_path.name, 'as_of_date': as_of_date, 'dimensions': dimension_rows}
        output_path = run_dir / 'segment_snapshot.json'
        with open(output_path, 'w', encoding='utf-8') as file_handle:
            json.dump(payload, file_handle, indent=2, default=str)
        logger.info('Exported segment snapshot: %s', output_path)
        return output_path

    @staticmethod
    def _resolve_segment_snapshot_source(run_dir: Path) -> Optional[Path]:
        for candidate in ('clean_data.parquet', 'transformed.parquet'):
            candidate_path = run_dir / candidate
            if candidate_path.exists():
                return candidate_path
        return None

    @staticmethod
    def _read_segment_snapshot_frame(data_path: Path) -> pd.DataFrame:
        try:
            return pd.read_parquet(data_path)
        except Exception as exc:
            logger.error('Failed reading segment snapshot source file: %s. Fail-fast triggered.', exc)
            raise RuntimeError(f'Cannot read segment data from {data_path}: {exc}') from exc

    def _prepare_segment_snapshot_frame(self, df: pd.DataFrame, *, balance_col: str, status_col: Optional[str], dpd_col: Optional[str], interest_rate_col: Optional[str]) -> pd.DataFrame:
        working = df.copy()
        working['__balance'] = pd.to_numeric(working[balance_col], errors='coerce').fillna(0.0)
        working['__status'] = working[status_col].astype(str).str.strip().str.lower() if status_col is not None else pd.Series(['unknown'] * len(working), index=working.index, dtype=object)
        working['__dpd'] = pd.to_numeric(working[dpd_col], errors='coerce').fillna(0.0) if dpd_col is not None else pd.Series([0.0] * len(working), index=working.index, dtype=float)
        working['__interest_rate'] = self._normalize_segment_interest_rate(working, interest_rate_col)
        return working

    @staticmethod
    def _normalize_segment_interest_rate(working: pd.DataFrame, interest_rate_col: Optional[str]) -> pd.Series:
        if interest_rate_col is None:
            return pd.Series([pd.NA] * len(working), index=working.index)
        interest_rate = pd.to_numeric(working[interest_rate_col], errors='coerce')
        if interest_rate.notna().any() and float(interest_rate.median()) > 1:
            interest_rate = interest_rate / 100.0
        return interest_rate

    def _build_segment_snapshot_dimensions(self, working: pd.DataFrame, loan_id_col: Optional[str]) -> Dict[str, list[Dict[str, Any]]]:
        dimension_rows: Dict[str, list[Dict[str, Any]]] = {}
        dimensions = ['company', 'credit_line', 'kam_hunter', 'kam_farmer', 'gov', 'industry', 'doc_type']
        missing_markers = {'', 'nan', 'none', 'null', 'n/a', 'missing', 'unknown'}
        for dimension in dimensions:
            if rows := self._build_segment_dimension_rows(working, dimension, loan_id_col, missing_markers):
                dimension_rows[dimension] = rows
        return dimension_rows

    def _build_segment_dimension_rows(self, working: pd.DataFrame, dimension: str, loan_id_col: Optional[str], missing_markers: Set[str]) -> list[Dict[str, Any]]:
        if dimension not in working.columns:
            return []
        raw_segment = working[dimension].astype(str).str.strip()
        valid_mask = ~raw_segment.str.lower().isin(missing_markers)
        if valid_mask.sum() == 0:
            return []
        segment_df = working.loc[valid_mask].copy()
        segment_df['__segment'] = raw_segment.loc[valid_mask]
        rows = [self._build_segment_snapshot_row(segment_name, group, loan_id_col) for segment_name, group in segment_df.groupby('__segment', dropna=False)]
        filtered_rows = [row for row in rows if row is not None]
        filtered_rows.sort(key=lambda item: item['total_outstanding_balance'], reverse=True)
        return filtered_rows[:25]

    def _build_segment_snapshot_row(self, segment_name: Any, group: pd.DataFrame, loan_id_col: Optional[str]) -> Optional[Dict[str, Any]]:
        balance_sum = Decimal(str(group['__balance'].sum()))
        if balance_sum <= 0:
            return None
        loan_count = int(group[loan_id_col].astype(str).nunique()) if loan_id_col is not None else len(group)
        row: Dict[str, Any] = {'segment': str(segment_name), 'loan_count': loan_count, 'total_outstanding_balance': float(balance_sum), 'par_30': float(self._segment_ratio(group, balance_sum, dpd_threshold=30)), 'par_60': float(self._segment_ratio(group, balance_sum, dpd_threshold=60)), 'par_90': float(self._segment_ratio(group, balance_sum, dpd_threshold=90)), 'default_rate': float(self._segment_default_rate(group, loan_count)), 'avg_dpd': float(Decimal(str(group['__dpd'].mean())))}
        if group['__interest_rate'].notna().any():
            portfolio_yield = Decimal(str(group['__interest_rate'].mean())) * Decimal('100')
            row['portfolio_yield'] = float(portfolio_yield)
        return row

    @staticmethod
    def _resolve_first_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
        available = {col.lower(): col for col in df.columns}
        for candidate in candidates:
            found = available.get(candidate.lower())
            if found is not None:
                return found
        return None

    @staticmethod
    def _segment_ratio(group: pd.DataFrame, balance_sum: Decimal, dpd_threshold: int) -> Decimal:
        if balance_sum <= 0:
            return Decimal('0')
        delinquent_outstanding = Decimal(str(group.loc[group['__dpd'] >= dpd_threshold, '__balance'].sum()))
        return delinquent_outstanding / balance_sum * Decimal('100')

    @staticmethod
    def _segment_default_rate(group: pd.DataFrame, loan_count: int) -> Decimal:
        if loan_count <= 0:
            return Decimal('0')
        defaulted_count = int((group['__status'] == 'defaulted').sum())
        return Decimal(defaulted_count) / Decimal(loan_count) * Decimal('100')

    @staticmethod
    def _derive_segment_as_of_date(df: pd.DataFrame) -> Optional[str]:
        for date_col in ('as_of_date', 'snapshot_date', 'fecha_actual', 'ingestion_timestamp', 'ingest_date'):
            if date_col in df.columns:
                parsed = pd.to_datetime(df[date_col], errors='coerce', format='mixed')
                max_dt = parsed.max()
                if pd.notna(max_dt):
                    return max_dt.date().isoformat()
        return None

    def _export_kpi_audit_trail(self, kpi_engine: Any) -> Optional[Path]:
        try:
            repo_root = Path(__file__).parent.parent.parent
            exports_dir = repo_root / 'exports'
            exports_dir.mkdir(exist_ok=True)
            output_path = exports_dir / 'kpi_audit_trail.csv'
            audit_df = kpi_engine.get_audit_trail()
            if audit_df.empty:
                logger.warning('No audit trail records to export')
                return None
            audit_df.to_csv(output_path, index=False)
            logger.info('Exported KPI audit trail: %s (%d records)', output_path, len(audit_df))
            return output_path
        except Exception as e:
            logger.error('Failed to export KPI audit trail: %s', str(e), exc_info=True)
            return None

    def _check_database_prerequisites(self) -> Optional[Dict[str, Any]]:
        if not self.config.get('database', {}).get('enabled', False):
            logger.debug('Database output is disabled in configuration')
            return {'status': 'skipped', 'reason': 'database_disabled'}
        return None

    def _validate_supabase_setup(self) -> Optional[Dict[str, Any]]:
        if Client is None or create_client is None:
            logger.warning('Supabase library not installed')
            return {'status': 'skipped', 'reason': 'supabase_not_installed'}
        supabase_url, supabase_key, _ = self._resolve_supabase_credentials()
        if not supabase_url or not supabase_key:
            logger.warning('Supabase credentials not configured in environment')
            return {'status': 'skipped', 'reason': 'missing_credentials'}
        return None

    def _resolve_supabase_credentials(self) -> tuple[Optional[str], Optional[str], str]:
        supabase_url = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        if service_role_key:
            return (supabase_url, service_role_key, 'service_role')
        return (supabase_url, anon_key, 'anon')

    def _validate_kpi_results(self, kpi_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not kpi_results or not isinstance(kpi_results, dict):
            logger.warning('No KPI results to write to database')
            return {'status': 'skipped', 'reason': 'empty_kpi_results'}
        return None

    def _prepare_kpi_rows(self, kpi_results: Dict[str, Any]) -> tuple[list, str, str]:
        rows_to_insert = []
        timestamp = datetime.now().isoformat()
        run_date = datetime.now().date().isoformat()
        table_name = self.config.get('database', {}).get('table', 'kpi_timeseries_daily')
        is_monitoring_table = self._is_monitoring_kpi_values_table(table_name)
        for kpi_name, kpi_value in kpi_results.items():
            if kpi_value is None:
                logger.debug('Skipping NULL KPI: %s', kpi_name)
                continue
            if is_monitoring_table:
                rows_to_insert.append({'kpi_name': kpi_name, 'value': self._to_numeric_value(kpi_value), 'timestamp': timestamp, 'status': 'green'})
            else:
                rows_to_insert.append({'kpi_name': kpi_name, 'kpi_value': self._to_numeric_value(kpi_value), 'timestamp': timestamp, 'run_date': run_date, 'source': 'pipeline_v2'})
        return (rows_to_insert, timestamp, run_date)

    def _is_monitoring_kpi_values_table(self, table_name: str) -> bool:
        normalized = (table_name or '').strip().lower()
        return normalized in {'monitoring.kpi_values', 'public.kpi_values', 'kpi_values'}

    @staticmethod
    def _to_numeric_value(value: Any) -> Optional[float]:
        return float(value) if isinstance(value, (Decimal, int, float)) else None

    def _get_kpi_definitions_map(self, supabase: Any) -> Optional[tuple[Dict[str, str], Dict[str, int]]]:
        try:
            definitions_table = self.config.get('database', {}).get('definitions_table', KPI_DEFINITIONS_TABLE)
            query = self._table_query(supabase, definitions_table)
            response = None
            try:
                response = query.select('id, name, kpi_key').execute()
            except Exception:
                response = query.select('name, kpi_key').execute()
            name_to_key: Dict[str, str] = {}
            name_to_id: Dict[str, int] = {}
            for kpi in response.data:
                name = kpi.get('name') or kpi.get('kpi_key')
                kpi_key = kpi.get('kpi_key') or name
                if not name or not kpi_key:
                    continue
                name_to_key[str(name)] = str(kpi_key)
                if kpi.get('id') is not None:
                    name_to_id[str(name)] = int(kpi['id'])
            logger.info('Loaded KPI definitions: %d names mapped', len(name_to_key))
            return (name_to_key, name_to_id)
        except Exception as e:
            logger.warning('Failed to load KPI definitions: %s', e)
            return None

    def _split_table_name(self, table_name: str) -> tuple[str, str]:
        if '.' in table_name:
            schema_name, bare_table = table_name.split('.', 1)
            return (schema_name, bare_table)
        return ('public', table_name)

    def _table_query(self, supabase: Any, table_name: str):
        schema_name, bare_table = self._split_table_name(table_name)
        if schema_name == 'monitoring':
            return supabase.table(bare_table)
        return supabase.schema(schema_name).table(bare_table)

    def _map_monitoring_kpi_name(self, kpi_name: str) -> str:
        configured_aliases = self.config.get('database', {}).get('kpi_name_aliases', {}) if isinstance(self.config.get('database', {}), dict) else {}
        return configured_aliases.get(kpi_name, kpi_name)

    def _insert_batch_rows(self, supabase: Any, table_name: str, rows: list) -> int:
        batch_size = 100
        is_monitoring_table = self._is_monitoring_kpi_values_table(table_name)
        if is_monitoring_table:
            rows = self._build_monitoring_rows(supabase, rows)
            if not rows:
                return 0
        return self._write_row_batches(supabase=supabase, table_name=table_name, rows=rows, batch_size=batch_size, is_monitoring_table=is_monitoring_table)

    def _build_monitoring_rows(self, supabase: Any, rows: list) -> list[Dict[str, Any]]:
        kpi_maps = self._get_kpi_definitions_map(supabase)
        if not kpi_maps:
            logger.error('Cannot write to monitoring.kpi_values without KPI definitions')
            return []
        name_to_key, name_to_id = kpi_maps
        mapped_names = {self._map_monitoring_kpi_name(str(row.get('kpi_name', ''))) for row in rows if row.get('kpi_name')}
        self._ensure_missing_kpi_definitions(supabase, mapped_names, set(name_to_key.keys()))
        if not mapped_names.issubset(set(name_to_key.keys())):
            if refreshed_maps := self._get_kpi_definitions_map(supabase):
                name_to_key, name_to_id = refreshed_maps
        metadata = self._get_monitoring_write_metadata()
        monitoring_rows: list[Dict[str, Any]] = []
        for row in rows:
            monitoring_row = self._build_monitoring_row(row, name_to_key, name_to_id, metadata)
            if monitoring_row is not None:
                monitoring_rows.append(monitoring_row)
        return monitoring_rows

    def _get_monitoring_write_metadata(self) -> Dict[str, str]:
        return {'snapshot_id': self.config.get('database', {}).get('snapshot_id') or os.getenv('PIPELINE_MONITORING_SNAPSHOT_ID') or 'pipeline_daily', 'run_id': self.config.get('database', {}).get('run_id') or f'pipeline_v2_{date.today().isoformat()}', 'inputs_hash': self.config.get('database', {}).get('inputs_hash') or 'pipeline_v2'}

    def _build_monitoring_row(self, row: Dict[str, Any], name_to_key: Dict[str, str], name_to_id: Dict[str, int], metadata: Dict[str, str]) -> Optional[Dict[str, Any]]:
        original_name = str(row.get('kpi_name', ''))
        mapped_name = self._map_monitoring_kpi_name(original_name)
        if mapped_name not in name_to_key:
            logger.warning('KPI not found in definitions: %s (mapped: %s)', original_name, mapped_name)
            return None
        row_timestamp = row.get('timestamp')
        as_of_date = str(row_timestamp).split('T')[0] if row_timestamp else date.today().isoformat()
        value = row.get('value')
        monitoring_row: Dict[str, Any] = {'kpi_key': name_to_key[mapped_name], 'value': value, 'value_num': value, 'timestamp': row_timestamp, 'computed_at': row_timestamp, 'as_of_date': as_of_date, 'status': row.get('status', 'green'), **metadata}
        if mapped_name in name_to_id:
            monitoring_row['kpi_id'] = name_to_id[mapped_name]
        return monitoring_row

    def _write_row_batches(self, *, supabase: Any, table_name: str, rows: list, batch_size: int, is_monitoring_table: bool) -> int:
        total_inserted = 0
        for index in range(0, len(rows), batch_size):
            batch = rows[index:index + batch_size]
            query = self._table_query(supabase, table_name)
            if is_monitoring_table:
                query.upsert(batch, on_conflict='as_of_date,kpi_key,snapshot_id').execute()
            else:
                query.insert(batch).execute()
            total_inserted += len(batch)
            logger.info('Inserted batch', extra={'batch_start': index, 'batch_end': index + len(batch), 'batch_size': len(batch)})
        return total_inserted

    def _ensure_missing_kpi_definitions(self, supabase: Any, mapped_names: Set[str], existing_names: Set[str]) -> None:
        missing = sorted((name for name in mapped_names if name and name not in existing_names))
        if not missing:
            return
        configured_table = self.config.get('database', {}).get('definitions_table', KPI_DEFINITIONS_TABLE)
        definitions_table = configured_table if '.' in configured_table else KPI_DEFINITIONS_TABLE
        query = self._table_query(supabase, definitions_table)
        for kpi_name in missing:
            payload_variants = [({'kpi_key': kpi_name, 'name': kpi_name, 'display_name': kpi_name.replace('_', ' ').title(), 'category': 'Pipeline', 'description': f'Auto-registered KPI definition for {kpi_name}', 'unit': 'unknown'}, 'kpi_key'), ({'kpi_key': kpi_name, 'display_name': kpi_name.replace('_', ' ').title(), 'category': 'Pipeline', 'description': f'Auto-registered KPI definition for {kpi_name}', 'unit': 'unknown'}, 'kpi_key'), ({'kpi_key': kpi_name, 'display_name': kpi_name.replace('_', ' ').title()}, 'kpi_key'), ({'name': kpi_name, 'category': 'Pipeline', 'description': f'Auto-registered KPI definition for {kpi_name}', 'unit': 'unknown'}, 'name')]
            created = False
            last_error: Optional[Exception] = None
            for payload, conflict_col in payload_variants:
                try:
                    query.upsert([payload], on_conflict=conflict_col).execute()
                    created = True
                    break
                except Exception as exc:
                    last_error = exc
            if created:
                logger.info('Auto-created missing KPI definition: %s', kpi_name)
            else:
                logger.warning("Could not auto-create KPI definition '%s'. Apply Supabase migrations for full KPI coverage. Last error: %s", kpi_name, last_error)

    def _write_to_database(self, kpi_results: Dict[str, Any]) -> Dict[str, Any]:
        if prereq_error := self._check_database_prerequisites():
            return prereq_error
        if input_error := self._validate_kpi_results(kpi_results):
            return input_error
        result: Dict[str, Any]
        try:
            if setup_error := self._validate_supabase_setup():
                return setup_error
            supabase_url, supabase_key, key_source = self._resolve_supabase_credentials()
            if supabase_url is None or supabase_key is None:
                raise RuntimeError('Supabase credentials missing during Phase 4 persistence')
            supabase: Any = create_client(supabase_url, supabase_key)
            logger.info('Using Supabase credentials source: %s', key_source)
            rows_to_insert, timestamp, _ = self._prepare_kpi_rows(kpi_results)
            if not rows_to_insert:
                logger.warning('No rows to insert after filtering')
                return {'status': 'skipped', 'reason': 'no_valid_kpis'}
            table_name = self.config.get('database', {}).get('table', 'kpi_timeseries_daily')
            logger.info('Writing %d KPI records to Supabase table: %s', len(rows_to_insert), table_name)
            total_inserted = self._insert_batch_rows(supabase, table_name, rows_to_insert)
            logger.info('Successfully wrote %d KPI records to database', total_inserted)
            result = {'status': 'success', 'records_written': total_inserted, 'timestamp': timestamp, 'table': table_name}
        except ImportError as e:
            logger.warning('Supabase library not available: %s', e)
            result = {'status': 'skipped', 'reason': 'supabase_not_installed'}
        except Exception as e:
            logger.error('Database write failed: %s', e, exc_info=True)
            result = {'status': 'error', 'error': str(e)}
        return result

    def _trigger_dashboard_refresh(self) -> Dict[str, str]:
        try:
            webhook_url = self.config.get('dashboard_webhook_url')
            if not webhook_url:
                logger.debug('Dashboard webhook URL not configured - refresh skipped')
                return {'status': 'skipped', 'reason': 'no_webhook_configured'}
            if httpx is None:
                logger.warning('httpx not installed - webhook POST skipped')
                return {'status': 'skipped', 'reason': 'httpx_not_installed'}
            payload = {'event': 'kpi_pipeline_complete', 'timestamp': datetime.now().isoformat(), 'source': 'pipeline_phase_4'}
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(webhook_url, json=payload)
                resp.raise_for_status()
            logger.info('Dashboard refresh triggered: webhook=%s status=%d', webhook_url, resp.status_code)
            return {'status': 'triggered', 'webhook': webhook_url, 'timestamp': payload['timestamp']}
        except Exception as e:
            logger.error('Dashboard refresh failed: %s', e, exc_info=True)
            return {'status': 'error', 'error': str(e)}

    def _get_failed_kpis_from_audit(self, audit_df: pd.DataFrame) -> list:
        try:
            if audit_df.empty:
                return []
            if 'status' not in audit_df.columns or 'kpi_name' not in audit_df.columns:
                raise ValueError('Audit DataFrame missing required columns: status, kpi_name')
            failed_mask = audit_df['status'] == 'failed'
            return audit_df[failed_mask]['kpi_name'].tolist()
        except Exception as e:
            logger.error('Error extracting failed KPIs from audit trail: %s', e)
            raise RuntimeError(f'Could not extract failed KPI audit data: {e}') from e

    def _build_audit_metadata_payload(self, kpi_results: Dict[str, Any], exports: Dict[str, str], kpi_engine: Optional['KPIEngineV2']=None, transformation_metrics: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {'timestamp': datetime.now().isoformat(), 'kpis_generated': len(kpi_results), 'exports_created': list(exports.keys()), 'quality_score': self._calculate_quality_score(kpi_results, kpi_engine), 'sla_met': self._check_sla(kpi_results, kpi_engine)}
        opaque_counts = self._collect_opaque_counts(transformation_metrics)
        payload['is_opaque_validation_counts'] = opaque_counts
        payload['total_opaque_observations'] = sum((v for v in opaque_counts.values() if v > 0))
        self._attach_kpi_engine_audit_summary(payload, kpi_engine)
        return payload

    def _collect_opaque_counts(self, transformation_metrics: Optional[Dict[str, Any]]) -> Dict[str, int]:
        opaque_counts: Dict[str, int] = {}
        if not transformation_metrics:
            return opaque_counts
        null_handling = transformation_metrics.get('null_handling', {})
        structured_opacity = null_handling.get('opacity_counts')
        if isinstance(structured_opacity, dict):
            for key, value in structured_opacity.items():
                try:
                    opaque_counts[str(key)] = int(value)
                except (TypeError, ValueError):
                    continue
        canonical_risk = transformation_metrics.get('canonical_risk_state', {})
        if canonical_risk.get('opaque_ratio_rows', 0):
            opaque_counts['ratio_pago_real_opaque'] = int(canonical_risk.get('opaque_ratio_rows', 0))
        return opaque_counts

    def _attach_kpi_engine_audit_summary(self, payload: Dict[str, Any], kpi_engine: Optional['KPIEngineV2']) -> None:
        if kpi_engine is None:
            return
        try:
            audit_df = kpi_engine.get_audit_trail()
            if audit_df.empty:
                return
            failed_kpis = self._get_failed_kpis_from_audit(audit_df)
            payload['kpi_engine_used'] = True
            payload['total_calculations'] = len(audit_df)
            payload['failed_calculations'] = len(failed_kpis)
            if failed_kpis:
                payload['failed_kpis'] = failed_kpis
        except Exception as e:
            logger.warning('Could not add KPI engine audit info: %s', e)

    def _generate_audit_metadata(self, kpi_results: Dict[str, Any], exports: Dict[str, str], kpi_engine: Optional['KPIEngineV2']=None) -> Dict[str, Any]:
        quality_score = self._calculate_quality_score(kpi_results, kpi_engine)
        sla_met = self._check_sla(kpi_results, kpi_engine)
        audit_info = {'timestamp': datetime.now().isoformat(), 'kpis_generated': len(kpi_results), 'exports_created': list(exports.keys()), 'quality_score': quality_score, 'sla_met': sla_met}
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    failed_kpis = self._get_failed_kpis_from_audit(audit_df)
                    audit_info['kpi_engine_used'] = True
                    audit_info['total_calculations'] = len(audit_df)
                    audit_info['failed_calculations'] = len(failed_kpis)
                    if failed_kpis:
                        audit_info['failed_kpis'] = failed_kpis
            except Exception as e:
                logger.warning('Could not add detailed audit info: %s', e)
        return audit_info

    def _calculate_quality_score(self, kpi_results: Dict[str, Any], kpi_engine: Optional['KPIEngineV2']=None) -> float:
        if not kpi_results:
            return 0.0
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    total = len(audit_df)
                    failed_kpis = self._get_failed_kpis_from_audit(audit_df)
                    successful = total - len(failed_kpis)
                    return round(successful / total, 2) if total > 0 else 0.0
            except Exception as e:
                logger.warning('Could not calculate quality score from audit trail: %s', e)
                return 0.0
        return 0.0

    def _check_sla(self, kpi_results: Dict[str, Any], kpi_engine: Optional['KPIEngineV2']=None) -> bool:
        if not kpi_results:
            return False
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    failed_kpis = self._get_failed_kpis_from_audit(audit_df)
                    return len(failed_kpis) == 0
            except Exception as e:
                logger.warning('Could not check SLA from audit trail: %s', e)
                return False
        return False
