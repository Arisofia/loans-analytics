

import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


class DataIngestionEngine:
    REQUIRED_COLUMNS = {
        "synthetic": ["customer", "balance", "limit", "revenue", "dpd"],
        "financial": ["customer", "balance", "limit", "dpd", "facility_amount"],
        "invoices": ["invoice_id", "customer", "amount", "invoice_date"],
    }

    def __init__(self, supabase_url: str, supabase_key: str, gdrive_credentials: Dict):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.gdrive_credentials = gdrive_credentials

    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [re.sub(r"\s+", "_", col.strip().lower()) for col in df.columns]
        return df

    @staticmethod
    def convert_numeric_tolerant(series: pd.Series) -> pd.Series:
        return pd.to_numeric(series.replace({"": None, "-": None}), errors="coerce")

    @staticmethod
    def standardize_dates(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.columns:
            if "date" in col:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    def normalize_dataframe(self, df: pd.DataFrame, source_name: str) -> Tuple[pd.DataFrame, int]:
        normalized = self.normalize_columns(df)
        normalized = self.standardize_dates(normalized)

        for col in normalized.select_dtypes(include=["object"]).columns:
            if col not in {"customer"}:
                continue
            normalized[col] = normalized[col].str.strip()

        numeric_pattern = re.compile(r"^-?\d+(?:\.\d+)?$")
        for col in normalized.columns:
            if normalized[col].dtype == object and normalized[col].str.match(numeric_pattern).any():
                normalized[col] = self.convert_numeric_tolerant(normalized[col])

        valid, missing = self.validate_required_columns(normalized, source_name)
        quality_score = self.calculate_data_quality_score(normalized)
        normalized["source"] = source_name
        return normalized, quality_score if valid else max(0, quality_score - len(missing) * 5)

    def validate_required_columns(self, df: pd.DataFrame, source_type: str) -> Tuple[bool, List[str]]:
        expected = self.REQUIRED_COLUMNS.get(source_type, [])
        missing = [col for col in expected if col not in df.columns]
        return not missing, missing

    def calculate_data_quality_score(self, df: pd.DataFrame) -> int:
        completeness = df.notna().mean().mean()
        uniqueness = df.nunique().mean() / max(len(df), 1)
        quality = (completeness * 0.7 + uniqueness * 0.3) * 100
        return int(round(quality))

    def detect_source_type(self, filename: str) -> Optional[str]:
        filename_lower = filename.lower()
        if "invoice" in filename_lower:
            return "invoices"
        if filename_lower.endswith((".csv", ".xlsx")):
            return "financial"
        return None

    def get_table_name(self, source_type: str) -> str:
        return f"raw_{source_type}" if source_type else "raw_unknown"

    def ingest_from_drive(self, folder_id: str) -> Dict:
        return {
            "folder_id": folder_id,
            "status": "queued",
            "message": "Drive ingestion is simulated in this environment",
        }
