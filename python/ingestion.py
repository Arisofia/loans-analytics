"""Data ingestion module for Cascade Debt platform."""
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class CascadeIngestion:
    """Ingestion engine for Cascade Debt CSV/JSON exports."""

    # Expanded required fields for full pipeline and dashboard coverage
    REQUIRED_FIELDS = [
        'period', 'measurement_date', 'total_receivable_usd',
        'total_eligible_usd', 'discounted_balance_usd',
        'dpd_0_7_usd', 'dpd_7_30_usd', 'dpd_30_60_usd',
        'dpd_60_90_usd', 'dpd_90_plus_usd', 'collateralization_pct',
        'surplus_usd', 'par7_pct', 'par30_pct', 'par60_pct', 'par90_pct',
        'default_ratio_30dpd_pct', 'collection_rate_pct', 'cdr_pct',
        'smm_pct', 'cpp_pct', 'avg_apr_pct', 'active_clients',
        'loans_count', 'principal_outstanding_usd', 'next_payment_usd',
        'next_payment_date', 'cash_available_usd', 'debt_equity_ratio',
        'de_limit'
    ]
    NUMERIC_FIELDS = [
        'total_receivable_usd', 'total_eligible_usd', 'discounted_balance_usd',
        'dpd_0_7_usd', 'dpd_7_30_usd', 'dpd_30_60_usd', 'dpd_60_90_usd',
        'dpd_90_plus_usd', 'collateralization_pct', 'surplus_usd',
        'par7_pct', 'par30_pct', 'par60_pct', 'par90_pct',
        'default_ratio_30dpd_pct', 'collection_rate_pct', 'cdr_pct',
        'smm_pct', 'cpp_pct', 'avg_apr_pct', 'active_clients',
        'loans_count', 'principal_outstanding_usd', 'next_payment_usd',
        'cash_available_usd', 'debt_equity_ratio', 'de_limit'
    ]

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.timestamp = datetime.now().isoformat()
        self.errors: List[Dict[str, Any]] = []

    def _record_error(self, stage: str, error: str, **context: Any) -> None:
        payload = {
            'stage': stage,
            'error': error,
            'timestamp': datetime.now(UTC).isoformat(),
            'run_id': self.run_id,
        }
        if context:
            if 'filename' in context and 'file' not in context:
                context['file'] = context['filename']
            payload.update(context)
        self.errors.append(payload)

    def ingest_csv(self, filename: str) -> pd.DataFrame:
        """Ingest CSV file from Cascade Debt export."""
        filepath = self.data_dir / filename
        self.timestamp = datetime.now().isoformat()
        try:
            df = pd.read_csv(filepath)
            df['_ingest_run_id'] = self.run_id
            df['_ingest_timestamp'] = self.timestamp
            logger.info('Ingested %s records from %s', len(df), filename)
            return df
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._record_error('ingest', str(e), filename=filename)
            logger.error('Failed to ingest %s: %s', filename, e)
            return pd.DataFrame()

    def ingest_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Attach ingest metadata to an existing DataFrame."""
        df = df.copy()
        df['_ingest_run_id'] = self.run_id
        df['_ingest_timestamp'] = self.timestamp
        return df

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate portfolio data for all required fields and types."""
        validation_errors: List[str] = []

        # Check for missing required fields
        for field in self.REQUIRED_FIELDS:
            if field not in df.columns:
                validation_errors.append(f'Missing required field: {field}')

        # Check for missing or invalid numeric fields
        for numeric_field in self.NUMERIC_FIELDS:
            if numeric_field in df.columns:
                try:
                    df[numeric_field] = pd.to_numeric(df[numeric_field], errors='raise')
                except (ValueError, TypeError) as e:
                    validation_errors.append(
                        f'{numeric_field} column has non-numeric values: {str(e)}'
                    )
            else:
                validation_errors.append(f'Missing required numeric field: {numeric_field}')

        # Check for empty DataFrame
        if df.empty:
            validation_errors.append('Input DataFrame is empty after ingestion.')

        if validation_errors:
            for err in validation_errors:
                self._record_error('validation', err)
            logger.warning('Validation warnings: %s', validation_errors)

        df['_validation_passed'] = len(validation_errors) == 0
        return df

    def get_ingest_summary(self) -> Dict[str, Any]:
        """Get ingestion summary with audit trail."""
        return {
            'run_id': self.run_id,
            'timestamp': self.timestamp,
            'total_errors': len(self.errors),
            'errors': self.errors,
        }
