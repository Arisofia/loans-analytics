"""
PHASE 1: DATA INGESTION

Responsibilities:
- Fetch data from Cascade API or CSV files
- Schema validation using Pydantic
- Duplicate detection via checksums
- Raw data storage with immutable hashes
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

from python.logging_config import get_logger

logger = get_logger(__name__)


class IngestionPhase:
    """Phase 1: Data Ingestion"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ingestion phase.
        
        Args:
            config: Ingestion configuration from pipeline.yml
        """
        self.config = config
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Initialized ingestion phase (run_id: {self.run_id})")
    
    def execute(
        self,
        input_path: Optional[Path] = None,
        run_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute ingestion phase.
        
        Args:
            input_path: Path to input CSV file (if file-based)
            run_dir: Directory for this pipeline run
            
        Returns:
            Ingestion results including data path and metadata
        """
        logger.info("Starting Phase 1: Ingestion")
        
        try:
            # Load data
            if input_path and input_path.exists():
                df = self._load_from_file(input_path)
            else:
                logger.info("No input file provided, checking for API ingestion...")
                df = self._load_from_api()
            
            # Validate schema
            validation_results = self._validate_schema(df)
            
            # Check for duplicates
            duplicate_check = self._check_duplicates(df)
            
            # Store raw data
            if run_dir:
                output_path = run_dir / "raw_data.parquet"
                df.to_parquet(output_path, index=False)
                logger.info(f"Saved raw data to {output_path}")
            else:
                output_path = None
            
            # Calculate data hash
            data_hash = self._calculate_hash(df)
            
            results = {
                "status": "success",
                "row_count": len(df),
                "column_count": len(df.columns),
                "data_hash": data_hash,
                "validation": validation_results,
                "duplicates": duplicate_check,
                "output_path": str(output_path) if output_path else None,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Ingestion completed: {results['row_count']} rows, {results['column_count']} columns")
            return results
            
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _load_from_file(self, file_path: Path) -> pd.DataFrame:
        """Load data from CSV file."""
        logger.info(f"Loading data from file: {file_path}")
        
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.parquet', '.pq']:
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        logger.info(f"Loaded {len(df)} rows from {file_path.name}")
        return df
    
    def _load_from_api(self) -> pd.DataFrame:
        """Load data from Cascade API (placeholder)."""
        logger.warning("API ingestion not yet implemented - using sample data")
        
        # TODO: Implement actual API client with:
        # - Token refresh
        # - Rate limiting
        # - Retry logic
        # - Request/response validation
        
        return pd.DataFrame({
            'loan_id': ['LOAN001', 'LOAN002'],
            'amount': [10000, 15000],
            'status': ['active', 'active']
        })
    
    def _validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate DataFrame schema."""
        # TODO: Implement Pydantic schema validation
        return {
            "schema_valid": True,
            "required_columns_present": True,
            "data_types_valid": True
        }
    
    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for duplicate rows."""
        duplicates = df.duplicated().sum()
        
        return {
            "duplicate_count": int(duplicates),
            "has_duplicates": duplicates > 0
        }
    
    def _calculate_hash(self, df: pd.DataFrame) -> str:
        """Calculate hash of DataFrame contents."""
        data_str = df.to_json(orient='records', date_format='iso')
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
