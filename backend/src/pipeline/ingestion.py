import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from backend.loans_analytics.logging_config import get_logger
from backend.src.infrastructure.google_sheets_adapter import ControlMoraSheetsAdapter
from backend.src.pipeline.constants import GSHEETS_URI_PREFIX
logger = get_logger(__name__)

class IngestionPhase:
    _GSHEETS_URI_PREFIX = GSHEETS_URI_PREFIX

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        logger.info('Initialized ingestion phase (run_id: %s)', self.run_id)

    def execute(self, input_path: Optional[Path]=None, run_dir: Optional[Path]=None) -> Dict[str, Any]:
        logger.info('Starting Phase 1: Ingestion')
        ingestion_timestamp = datetime.now(timezone.utc).isoformat()
        if self._should_use_google_sheets(input_path):
            ingestion_source = 'google_sheets'
            df = self._load_from_google_sheets(input_path)
        elif input_path and input_path.exists():
            ingestion_source = 'file'
            df = self._load_from_file(input_path)
        elif input_path and (not input_path.exists()):
            raise FileNotFoundError(f'Input file not found: {input_path}')
        else:
            logger.info('No input file provided; API ingestion is disabled')
            ingestion_source = 'api'
            df = self._load_from_api()
        validation_results = self._validate_schema(df)
        duplicate_check = self._check_duplicates(df)
        data_as_of_date, data_as_of_column = self._detect_data_as_of_date(df)
        if data_as_of_date:
            logger.info('Detected data as-of date: %s (from column: %s)', data_as_of_date, data_as_of_column)
        if run_dir:
            output_path = run_dir / 'raw_data.parquet'
            try:
                df.to_parquet(output_path, index=False)
            except Exception as parquet_error:
                logger.warning('Parquet write failed on raw frame; applying Arrow-safe coercion. Error: %s', parquet_error)
                df = self._make_arrow_safe(df)
                df.to_parquet(output_path, index=False)
            logger.info('Saved raw data to %s', output_path)
        else:
            output_path = None
        data_hash = self._calculate_hash(df)
        results = {
            'status': 'success',
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_hash': data_hash,
            'validation': validation_results,
            'duplicates': duplicate_check,
            'output_path': str(output_path) if output_path else None,
            'timestamp': ingestion_timestamp,
            'ingestion_source': ingestion_source,
            'data_as_of_date': data_as_of_date,
            'data_as_of_column': data_as_of_column,
        }
        logger.info('Ingestion completed: %d rows, %d columns', results['row_count'], results['column_count'])
        return results

    def _load_from_file(self, file_path: Path) -> pd.DataFrame:
        logger.info('Loading data from file: %s', file_path)
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, low_memory=False)
        elif file_path.suffix.lower() in ['.parquet', '.pq']:
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f'Unsupported file format: {file_path.suffix}')
        df = self._normalize_real_file_schema(df, file_path)
        logger.info('Loaded %d rows from %s', len(df), file_path.name)
        return df

    def _normalize_real_file_schema(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        required_columns = self.config.get('required_columns', ['loan_id', 'amount', 'status', 'borrower_id'])
        if all((column in df.columns for column in required_columns)):
            return df
        normalized_df = self._normalize_control_mora_like_file(df)
        if normalized_df is not df:
            logger.info('Normalized control-mora-like input schema for %s', file_path.name)
        return normalized_df

    def _normalize_control_mora_like_file(self, df: pd.DataFrame) -> pd.DataFrame:
        slug_to_column = {self._slugify(column): column for column in df.columns}
        evidence_columns = {'numerodesembolso', 'numerointerno', 'fechadesembolso', 'valororiginal', 'clinumero', 'diadepago', 'mesdepago'}
        if not evidence_columns.intersection(slug_to_column):
            return df
        normalized = df.copy()
        loan_id_col = self._first_existing_column(slug_to_column, ['loan_id', 'numerointerno', 'numerodesembolso', 'mfanumdoc'])
        borrower_id_col = self._first_existing_column(slug_to_column, ['borrower_id', 'clinumero', 'codcliente', 'client_id'])
        amount_col = self._first_existing_column(slug_to_column, ['amount', 'valororiginal', 'valoraprobado', 'montodesembolsado', 'totallinea', 'sumoftotallinea', 'totalconiva', 'sumoftotalconiva'])
        as_of_col = self._first_existing_column(slug_to_column, ['as_of_date', 'fechaactual', 'fechacorte', 'mfafecha'])
        origination_col = self._first_existing_column(slug_to_column, ['origination_date', 'fechadesembolso', 'disbursement_date'])
        existing_due_col = self._first_existing_column(slug_to_column, ['due_date', 'fechapagoprogramado', 'fechadevencimiento', 'fechavencimiento'])
        dpd_col = self._first_existing_column(slug_to_column, ['dpd', 'dayspastdue', 'diasmora', 'diasvencidos', 'diasvencido'])
        status_col = self._first_existing_column(slug_to_column, ['status', 'currentstatus', 'loanstatus', 'mdscposteado', 'infoclientefinal'])

        if loan_id_col and 'loan_id' not in normalized.columns:
            normalized['loan_id'] = normalized[loan_id_col].astype('string').str.strip()
        if borrower_id_col and 'borrower_id' not in normalized.columns:
            normalized['borrower_id'] = normalized[borrower_id_col].astype('string').str.strip()
        if amount_col and 'amount' not in normalized.columns:
            normalized['amount'] = self._coerce_numeric_loose(normalized[amount_col])
        if origination_col and 'origination_date' not in normalized.columns:
            normalized['origination_date'] = self._coerce_datetime_loose(normalized[origination_col])
        if as_of_col and 'as_of_date' not in normalized.columns:
            normalized['as_of_date'] = self._coerce_datetime_loose(normalized[as_of_col])
        due_date = self._build_due_date(normalized, slug_to_column, existing_due_col)
        if due_date is not None and 'due_date' not in normalized.columns:
            normalized['due_date'] = due_date

        existing_dpd = self._coerce_numeric_loose(normalized[dpd_col]) if dpd_col else pd.Series(pd.NA, index=normalized.index, dtype='Float64')
        derived_dpd = self._derive_dpd_from_dates(normalized)
        if existing_dpd.notna().any() or derived_dpd.notna().any():
            normalized['dpd'] = existing_dpd.where(existing_dpd.notna(), derived_dpd)

        if status_col and 'status' not in normalized.columns:
            normalized['status'] = self._normalize_status_values(normalized[status_col])
        if 'status' not in normalized.columns or normalized['status'].isna().all() or (normalized['status'].astype('string').str.strip() == '').all():
            if 'dpd' in normalized.columns:
                normalized['status'] = self._derive_status_from_dpd(normalized['dpd'])

        return normalized

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = value.replace('ñ', 'n').replace('Ñ', 'N')
        return re.sub(r'[^a-z0-9]+', '', normalized.lower())

    @staticmethod
    def _first_existing_column(slug_to_column: Dict[str, str], candidates: list[str]) -> Optional[str]:
        for candidate in candidates:
            if candidate in slug_to_column:
                return slug_to_column[candidate]
        return None

    @staticmethod
    def _coerce_numeric_loose(series: pd.Series) -> pd.Series:
        text = series.astype('string').str.strip()
        text = text.mask(text.isin({'', 'nan', 'none', 'null', 'missing'}), pd.NA)
        cleaned = text.str.replace(r'[^0-9,.-]', '', regex=True)
        comma_only_mask = cleaned.str.contains(',', na=False) & ~cleaned.str.contains(r'\.', na=False)
        thousands_mask = comma_only_mask & cleaned.str.contains(r',\d{3}$', regex=True, na=False)
        decimal_comma_mask = comma_only_mask & ~thousands_mask
        if thousands_mask.any():
            cleaned.loc[thousands_mask] = cleaned.loc[thousands_mask].str.replace(',', '', regex=False)
        if decimal_comma_mask.any():
            cleaned.loc[decimal_comma_mask] = cleaned.loc[decimal_comma_mask].str.replace(',', '.', regex=False)
        other_mask = ~comma_only_mask
        if other_mask.any():
            cleaned.loc[other_mask] = cleaned.loc[other_mask].str.replace(',', '', regex=False)
        return pd.to_numeric(cleaned, errors='coerce').astype(float)

    @staticmethod
    def _coerce_datetime_loose(series: pd.Series) -> pd.Series:
        try:
            return pd.to_datetime(series, errors='coerce', format='mixed', dayfirst=True)
        except TypeError:
            return pd.to_datetime(series, errors='coerce', dayfirst=True)

    def _build_due_date(self, df: pd.DataFrame, slug_to_column: Dict[str, str], existing_due_col: Optional[str]) -> Optional[pd.Series]:
        if existing_due_col:
            due_date = self._coerce_datetime_loose(df[existing_due_col])
            if due_date.notna().any():
                return due_date
        day_col = self._first_existing_column(slug_to_column, ['diadepago'])
        month_col = self._first_existing_column(slug_to_column, ['mesdepago'])
        year_col = self._first_existing_column(slug_to_column, ['anodelpago', 'aodelpago'])
        if not day_col or not month_col or not year_col:
            return None
        day = pd.to_numeric(df[day_col], errors='coerce')
        month = pd.to_numeric(df[month_col], errors='coerce')
        year = pd.to_numeric(df[year_col], errors='coerce')
        valid_mask = day.notna() & month.notna() & year.notna()
        if not valid_mask.any():
            return None
        due_date = pd.Series(pd.NaT, index=df.index, dtype='datetime64[ns]')
        due_date.loc[valid_mask] = pd.to_datetime({'year': year.loc[valid_mask].astype(int), 'month': month.loc[valid_mask].astype(int), 'day': day.loc[valid_mask].astype(int)}, errors='coerce')
        return due_date

    def _derive_dpd_from_dates(self, df: pd.DataFrame) -> pd.Series:
        if 'as_of_date' not in df.columns or 'due_date' not in df.columns:
            return pd.Series(pd.NA, index=df.index, dtype='Float64')
        as_of_date = self._coerce_datetime_loose(df['as_of_date'])
        due_date = self._coerce_datetime_loose(df['due_date'])
        dpd = (as_of_date - due_date).dt.days.clip(lower=0)
        return dpd.astype('Float64')

    @staticmethod
    def _normalize_status_values(series: pd.Series) -> pd.Series:
        normalized = series.astype('string').str.strip().str.lower()
        return normalized.replace({'vigente': 'active', 'al_dia': 'active', 'al dia': 'active', 'posted': 'active', 'mora': 'delinquent', 'moroso': 'delinquent', 'vencido': 'defaulted', 'castigado': 'defaulted', 'default': 'defaulted'})

    @staticmethod
    def _derive_status_from_dpd(dpd_series: pd.Series) -> pd.Series:
        dpd_values = pd.to_numeric(dpd_series, errors='coerce')
        status_series = pd.Series('unknown', index=dpd_series.index, dtype='object')
        status_series.loc[dpd_values.notna() & (dpd_values <= 0)] = 'active'
        status_series.loc[dpd_values > 0] = 'delinquent'
        status_series.loc[dpd_values > 90] = 'defaulted'
        return status_series

    def _make_arrow_safe(self, df: pd.DataFrame) -> pd.DataFrame:
        safe = df.copy()
        safe.columns = [str(col) for col in safe.columns]
        for col in safe.columns:
            series = safe[col]
            if series.dtype == 'object':
                safe[col] = series.map(self._to_nullable_string).astype('string')
        return safe

    @staticmethod
    def _to_nullable_string(value: Any) -> Any:
        if pd.isna(value):
            return pd.NA
        if isinstance(value, bytes):
            for encoding in ('utf-8', 'latin-1'):
                try:
                    return value.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError(f'CRITICAL: decode failure for bytes value {repr(value)}. Aborting batch.')
        return str(value)

    def _load_from_api(self) -> pd.DataFrame:
        raise RuntimeError('No input file provided. API ingestion was deprecated and dummy/sample fallback is disabled. Pass --input with a real dataset.')

    def _should_use_google_sheets(self, input_path: Optional[Path]) -> bool:
        if input_path is not None and self._extract_google_sheet_tab(input_path):
            return True
        sheets_cfg = self.config.get('google_sheets', {})
        return bool(sheets_cfg.get('enabled', False) and input_path is None)

    def _extract_google_sheet_tab(self, input_path: Path) -> Optional[str]:
        normalized = str(input_path).replace('\\', '/')
        if normalized.startswith(self._GSHEETS_URI_PREFIX):
            return normalized[len(self._GSHEETS_URI_PREFIX):].strip('/') or None
        if normalized.startswith('gsheets:/'):
            return normalized[len('gsheets:/'):].strip('/') or None
        return None

    def _load_from_google_sheets(self, input_path: Optional[Path]=None) -> pd.DataFrame:
        sheets_cfg = self.config.get('google_sheets', {})
        credentials_path = sheets_cfg.get('credentials_path') or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        spreadsheet_id = sheets_cfg.get('spreadsheet_id') or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        if not credentials_path or not spreadsheet_id:
            raise ValueError('CRITICAL: Google Sheets ingestion enabled but credentials_path/spreadsheet_id are missing. Set google_sheets config or environment variables.')
        adapter = ControlMoraSheetsAdapter(credentials_path=str(credentials_path), spreadsheet_id=str(spreadsheet_id))
        requested_tab = self._extract_google_sheet_tab(input_path) if input_path else None
        target_tab = requested_tab or str(sheets_cfg.get('worksheet', '')).strip() or 'DESEMBOLSOS'
        if target_tab.upper() == 'DESEMBOLSOS':
            records = adapter.fetch_desembolsos_raw()
        else:
            records = adapter.fetch_sheet_raw(target_tab)
        if not records:
            raise ValueError(f"CRITICAL: Google Sheets tab '{target_tab}' returned zero records")
        df = pd.DataFrame(records)
        df = self._coerce_google_sheets_schema(df)
        logger.info("Loaded %d rows from Google Sheets adapter tab '%s'", len(df), target_tab)

        # Merge outstanding balance from INTERMEDIA tab when loading DESEMBOLSOS
        if target_tab.upper() == 'DESEMBOLSOS':
            df = self._enrich_with_intermedia(df, adapter)

        return df

    def _enrich_with_intermedia(self, df: pd.DataFrame, adapter: ControlMoraSheetsAdapter) -> pd.DataFrame:
        """Merge TotalSaldoVigente (outstanding balance) from INTERMEDIA tab."""
        try:
            intermedia_records = adapter.fetch_intermedia_raw()
        except Exception as exc:
            logger.warning("Could not load INTERMEDIA tab for balance enrichment: %s", exc)
            return df
        if not intermedia_records:
            logger.warning("INTERMEDIA tab returned zero records; skipping balance enrichment")
            return df
        intermedia_df = pd.DataFrame(intermedia_records)
        # Find the loan ID column in INTERMEDIA
        id_col = None
        for candidate in ('NumeroInterno', 'numerointerno', 'loan_id'):
            if candidate in intermedia_df.columns:
                id_col = candidate
                break
        if id_col is None:
            logger.warning("INTERMEDIA tab has no loan ID column; skipping balance enrichment")
            return df
        # Find balance column
        bal_col = None
        for candidate in ('TotalSaldoVigente', 'totalsaldovigente'):
            if candidate in intermedia_df.columns:
                bal_col = candidate
                break
        if bal_col is None:
            logger.warning("INTERMEDIA tab has no TotalSaldoVigente column; skipping balance enrichment")
            return df
        # Prepare merge key
        intermedia_df['_merge_id'] = intermedia_df[id_col].astype(str).str.strip()
        intermedia_df['outstanding_balance'] = pd.to_numeric(intermedia_df[bal_col], errors='coerce')
        # Keep latest non-null balance per loan
        bal_lookup = (
            intermedia_df[['_merge_id', 'outstanding_balance']]
            .dropna(subset=['outstanding_balance'])
            .drop_duplicates(subset=['_merge_id'], keep='last')
        )
        # Merge into main dataframe
        df['_merge_id'] = df['loan_id'].astype(str).str.strip()
        df = df.merge(bal_lookup, on='_merge_id', how='left', suffixes=('', '_intermedia'))
        df.drop(columns=['_merge_id'], inplace=True, errors='ignore')
        matched = df['outstanding_balance'].notna().sum() if 'outstanding_balance' in df.columns else 0
        logger.info(
            "INTERMEDIA enrichment: merged outstanding_balance for %d/%d loans",
            matched, len(df),
        )
        return df

    def _coerce_google_sheets_schema(self, df: pd.DataFrame) -> pd.DataFrame:

        def first_existing(columns: list[str]) -> Optional[str]:
            return next((col for col in columns if col in df.columns), None)
        loan_id_col = first_existing(['loan_id', 'NumeroInterno', 'NumeroQuedan', 'numerointerno'])
        amount_col = first_existing(['amount', 'ValorAprobado', 'MontoDesembolsado', 'valoraprobado', 'montodesembolsado'])
        borrower_id_col = first_existing(['borrower_id', 'CodCliente', 'codcliente'])
        status_col = first_existing(['status', 'mdscPosteado', 'mdscposteado', 'infoclientefinal'])
        if loan_id_col and 'loan_id' not in df.columns:
            df['loan_id'] = df[loan_id_col]
        if amount_col and 'amount' not in df.columns:
            df['amount'] = pd.to_numeric(df[amount_col], errors='coerce')
        if borrower_id_col and 'borrower_id' not in df.columns:
            df['borrower_id'] = df[borrower_id_col]
        if 'status' not in df.columns:
            if status_col:
                normalized = df[status_col].astype(str).str.strip().str.lower()
                df['status'] = normalized.replace({'vigente': 'active', 'al_dia': 'active', 'posted': 'active', 'mora': 'delinquent', 'vencido': 'delinquent', 'castigado': 'defaulted', 'default': 'defaulted'})
            else:
                raise ValueError('CRITICAL: Google Sheets data cannot be normalized to canonical schema; missing status source column (expected one of: status, mdscPosteado, mdscposteado, infoclientefinal).')
        missing = [col for col in ('loan_id', 'amount', 'status', 'borrower_id') if col not in df.columns]
        if missing:
            raise ValueError(f'CRITICAL: Google Sheets data cannot be normalized to canonical schema; missing columns after mapping: {missing}. Available columns: {sorted(df.columns)}')
        return df

    def _validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        try:
            required_columns = self.config.get('required_columns', ['loan_id', 'amount', 'status', 'borrower_id'])
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f'CRITICAL: SCHEMA VALIDATION FAILED: Missing required columns: {missing_columns}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            type_validation: Dict[str, Any] = {'loan_id': str, 'amount': (int, float), 'status': str}
            type_errors = []
            for col, expected_type in type_validation.items():
                if col in df.columns and (not all((isinstance(val, expected_type) for val in df[col].dropna()))):
                    type_errors.append(col)
            if type_errors:
                error_msg = f'CRITICAL: SCHEMA VALIDATION FAILED: Type validation failed for columns: {type_errors}'
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info('Schema validation passed', extra={'column_count': len(df.columns), 'row_count': len(df)})
            return {'schema_valid': True, 'required_columns_present': True, 'data_types_valid': True, 'column_count': len(df.columns), 'row_count': len(df)}
        except Exception as e:
            if isinstance(e, ValueError) and 'CRITICAL: SCHEMA VALIDATION FAILED' in str(e):
                raise
            logger.error('Schema validation error: %s', e, exc_info=True)
            raise ValueError(f'CRITICAL: Schema validation pipeline failure: {e}') from e

    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        duplicates = df.duplicated().sum()
        return {'duplicate_count': int(duplicates), 'has_duplicates': duplicates > 0}

    def _detect_data_as_of_date(self, df: pd.DataFrame) -> tuple[Optional[str], Optional[str]]:
        """Return (max_date_str, source_column) representing the data as-of date.

        Inspects candidate date columns in order of preference and returns the
        maximum (most recent) date found, together with the column it came from.
        Returns (None, None) when no suitable date column is present.
        """
        primary_candidates = [
            'as_of_date', 'snapshot_date', 'measurement_date', 'reporting_date',
            'fecha_corte', 'fecha_de_corte', 'cutoff_date', 'data_ingest_ts',
            'FechaDesembolso', 'fechadesembolso',
        ]
        fallback_candidates = [
            'last_payment_date', 'origination_date', 'application_date',
            'FechaPago', 'fechapago',
        ]
        # Use dayfirst=True only for columns known to carry LatAm/Spanish-locale
        # dates (DD/MM/YYYY format).  English-named columns default to False to
        # avoid misinterpreting MM/DD/YYYY US-style dates.
        _latam_date_prefixes = ('fecha', 'Fecha')

        for col in [*primary_candidates, *fallback_candidates]:
            if col not in df.columns:
                continue
            dayfirst = col.startswith(_latam_date_prefixes)
            try:
                parsed = pd.to_datetime(df[col], errors='coerce', format='mixed', dayfirst=dayfirst)
            except TypeError:
                parsed = pd.to_datetime(df[col], errors='coerce', dayfirst=dayfirst)
            max_dt = parsed.max()
            if pd.notna(max_dt):
                return (str(max_dt.date()), col)
        return (None, None)

    def _calculate_hash(self, df: pd.DataFrame) -> str:
        canonical_df = df.reindex(sorted(df.columns), axis=1)
        data_str = canonical_df.to_json(orient='records', date_format='iso')
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
