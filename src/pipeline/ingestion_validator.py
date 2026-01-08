from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from src.pipeline.models import LoanRecord

class IngestionValidator:
    """Consolidated validation engine for ingestion data quality."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schema_validator = self._load_json_schema()

    def _load_json_schema(self) -> Optional[Draft202012Validator]:
        schema_path = self.config.get("validation", {}).get("schema_path")
        if not schema_path or not Path(schema_path).exists():
            return None
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        return Draft202012Validator(schema)

    def validate_schema(self, df: pd.DataFrame) -> List[str]:
        """JSON Schema validation for individual records."""
        errors: List[str] = []
        if not self.schema_validator:
            return errors
        for idx, record in enumerate(df.to_dict(orient="records")):
            for error in self.schema_validator.iter_errors(record):
                errors.append(f"row {idx}: {error.message}")
        return errors

    def validate_pandera(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Pandera contract validation."""
        try:
            # Deferred import to avoid circular dependency with analytics.schema
            from src.analytics.schema import LoanTapeSchema
            
            # Only validate if required columns for schema are present
            schema_cols = ["loan_id", "outstanding_balance", "dpd"]
            present = [c for c in schema_cols if c in df.columns]
            
            if len(present) < len(schema_cols):
                if not any(c in df.columns for c in ["outstanding_balance", "total_receivable_usd"]):
                     return df, []

            validated_df = LoanTapeSchema.validate(df)
            return validated_df, []
        except Exception as exc:
            # Distinguish between critical contract violations and simple schema mismatches
            is_contract = "contract" in str(exc).lower() or "future" in str(exc).lower()
            prefix = "[CRITICAL CONTRACT VIOLATION]" if is_contract else "[SCHEMA MISMATCH]"
            return df, [f"{prefix} {exc}"]

    def validate_models(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Pydantic model validation for deep data integrity."""
        records = df.to_dict(orient="records")
        validated_records = []
        errors: List[str] = []

        for idx, record in enumerate(records):
            try:
                # Normalize keys and ensure core fields exist
                clean_record = {str(k).strip().lower(): v for k, v in record.items()}
                if "loan_id" not in clean_record:
                    clean_record["loan_id"] = f"agg_{idx}"
                
                # Ensure core numeric fields exist for LoanRecord if missing from input
                for field in ["total_receivable_usd", "total_eligible_usd", "discounted_balance_usd"]:
                    if field not in clean_record:
                        clean_record[field] = 0.0
                
                validated_records.append(LoanRecord(**clean_record).model_dump(by_alias=True))
            except ValidationError as exc:
                errors.append(f"row {idx}: {exc}")

        return pd.DataFrame(validated_records) if validated_records else df, errors

    def detect_looker_schema_drift(self, columns: set[str]) -> Dict[str, List[str]]:
        """Detect drift in Looker export schemas."""
        par_required = {
            "reporting_date",
            "par_7_balance_usd",
            "par_30_balance_usd",
            "par_60_balance_usd",
            "par_90_balance_usd",
        }
        dpd_required = {"dpd", "outstanding_balance"}
        dpd_alt = {"dpd", "outstanding_balance_usd"}
        dpd_alt_two = {"days_past_due", "outstanding_balance"}

        lower_columns = {c.lower() for c in columns}
        
        if lower_columns.issuperset(par_required):
            return {"missing": [], "unexpected": []}
        if (
            lower_columns.issuperset(dpd_required)
            or lower_columns.issuperset(dpd_alt)
            or lower_columns.issuperset(dpd_alt_two)
        ):
            return {"missing": [], "unexpected": []}

        missing_sets = [
            sorted(list(par_required - lower_columns)),
            sorted(list(dpd_required - lower_columns)),
            sorted(list(dpd_alt - lower_columns)),
            sorted(list(dpd_alt_two - lower_columns)),
        ]
        return {
            "missing": sorted({item for subset in missing_sets for item in subset}),
            "unexpected": [],
        }
