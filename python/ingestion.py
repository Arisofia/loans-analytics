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

    def __init__(self, data_dir: str = 'data/cascade'):
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
            error = {'file': filename, 'error': str(e), 'timestamp': self.run_id}
            self.errors.append(error)
            logger.error(f'Failed to ingest {filename}: {e}')
            return pd.DataFrame()

    def ingest_json(self, filename: str) -> List[Dict]:
        """Ingest JSON file from Cascade Debt export."""
        filepath = self.data_dir / filename
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for record in data:
                        record['_ingest_run_id'] = self.run_id
                        record['_ingest_timestamp'] = datetime.utcnow().isoformat()
                    logger.info(f'Ingested {len(data)} records from {filename}')
                    return data
                else:
                    logger.warning(f'{filename} is not a list')
                    return []
        except Exception as e:
            error = {'file': filename, 'error': str(e), 'timestamp': self.run_id}
            self.errors.append(error)
            logger.error(f'Failed to ingest {filename}: {e}')
            return []

    def validate_loans(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate loan data."""
        validation_errors = []
        
        # Check required fields
        required_fields = ['loan_id', 'customer_id', 'principal_balance', 'status']
        for field in required_fields:
            if field not in df.columns:
                validation_errors.append(f'Missing required field: {field}')
        
        # Check data types and ranges
        if 'principal_balance' in df.columns:
            invalid_amounts = df[df['principal_balance'] < 0]
            if len(invalid_amounts) > 0:
                validation_errors.append(f'Found {len(invalid_amounts)} loans with negative balance')
        
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
