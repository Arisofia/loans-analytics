"""Data ingestion module for Cascade Debt platform."""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)

class CascadeIngestion:
    """Ingestion engine for Cascade Debt CSV/JSON exports."""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = datetime.utcnow().isoformat()
        self.errors: List[Dict[str, Any]] = []
    
    def ingest_csv(self, filename: str) -> pd.DataFrame:
        """Ingest CSV file from Cascade Debt export."""
        filepath = self.data_dir / filename
        try:
            df = pd.read_csv(filepath)
            df['_ingest_run_id'] = self.run_id
            df['_ingest_timestamp'] = datetime.utcnow().isoformat()
            logger.info(f'Ingested {len(df)} records from {filename}')
            return df
        except Exception as e:
            error = {'file': filename, 'error': str(e), 'timestamp': datetime.utcnow().isoformat(), 'run_id': self.run_idd}
            self.errors.append(error)
            logger.error(f'Failed to ingest {filename}: {e}')
            return pd.DataFrame()
    
    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate portfolio data."""
        validation_errors = []
        
        # Check required fields
        required_fields = ['period', 'measurement_date', 'total_receivable_usd']
        for field in required_fields:
            if field not in df.columns:
                validation_errors.append(f'Missing required field: {field}')
        
        # Check data types
        if 'total_receivable_usd' in df.columns:
            try:
                pd.to_numeric(df['total_receivable_usd'])
except (ValueError, TypeError) as e:                validation_errors.appendf('total_receivable_usd column has non-numeric values': {str(e)}'        
        if validation_errors:
            logger.warning(f'Validation warnings: {validation_errors}')
        
        df['_validation_passed'] = len(validation_errors) == 0
        return df
    
    def get_ingest_summary(self) -> Dict[str, Any]:
        """Get ingestion summary with audit trail."""
        return {
            'run_id': self.run_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_errors': len(self.errors),
            'errors': self.errors,
        }
