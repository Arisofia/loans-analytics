from typing import List, Tuple, Dict, Any
import pandas as pd
from pandera import DataFrameSchema
from pydantic import ValidationError

def validate_schema(df: pd.DataFrame, schema_validator: DataFrameSchema) -> List[str]:
    errors: List[str] = []
    if schema_validator is None:
        return errors
    for idx, record in enumerate(df.to_dict(orient="records")):
        errors.extend(
            f"row {idx}: {error.message}" for error in schema_validator.iter_errors(record)
        )
    return errors

def validate_records(df: pd.DataFrame, record_model) -> Tuple[pd.DataFrame, List[str]]:
    records = df.to_dict(orient="records")
    validated_records = []
    errors: List[str] = []
    for idx, record in enumerate(records):
        try:
            clean_record = {str(k).strip().lower(): v for k, v in record.items()}
            if "loan_id" not in clean_record:
                clean_record["loan_id"] = f"auto_{idx}"
            validated_records.append(record_model(**clean_record).model_dump(by_alias=True))
        except Exception as exc:
            errors.append(f"row {idx}: {exc}")
    return pd.DataFrame(validated_records), errors

def deduplicate_data(df: pd.DataFrame, key_columns: List[str]) -> Tuple[pd.DataFrame, int]:
    if not key_columns:
        return df, 0
    before = len(df)
    deduped = df.drop_duplicates(subset=key_columns)
    return deduped, before - len(deduped)
