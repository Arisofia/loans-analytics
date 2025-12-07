"""Data ingestion module for Cascade Debt platform."""
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class CascadeIngestion:
    """Ingestion engine for Cascade Debt CSV/JSON exports."""

    REQUIRED_FIELDS = ['period', 'measurement_date', 'total_receivable_usd']
    NUMERIC_FIELDS = ['total_receivable_usd']

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
            # Normalize filename key for compatibility with existing summaries/tests
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
            logger.info(f'Ingested {len(df)} records from {filename}')
            return df
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._record_error('ingest', str(e), filename=filename)
            logger.error(f'Failed to ingest {filename}: {e}')
            return pd.DataFrame()

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate portfolio data."""
        validation_errors: List[str] = []

        for field in self.REQUIRED_FIELDS:
            if field not in df.columns:
                validation_errors.append(f'Missing required field: {field}')

        for numeric_field in self.NUMERIC_FIELDS:
            if numeric_field in df.columns:
                try:
                    pd.to_numeric(df[numeric_field])
                except (ValueError, TypeError) as e:  # pragma: no cover - defensive
                    validation_errors.append(f'{numeric_field} column has non-numeric values: {str(e)}')

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
