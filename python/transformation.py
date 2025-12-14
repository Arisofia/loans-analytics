import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone

class DataTransformation:
    def __init__(self):
        # Coderabbit: Assign a unique run_id for each transformation instance for traceability (16 hex chars for lower collision risk)
        self.run_id = f"tx_{uuid.uuid4().hex[:16]}"
        self.transformations_count = 0

    def calculate_receivables_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate aggregate metrics for the portfolio."""
        return {
            "total_receivable": df["total_receivable_usd"].sum(),
            "total_eligible": df["total_eligible_usd"].sum(),
            "discounted_balance": df["discounted_balance_usd"].sum(),
        }

    def calculate_dpd_ratios(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate portfolio-level DPD ratios."""
        total = df["total_receivable_usd"].sum()
        if total == 0:
            return {}
        
        ratios = {}
        for col in ["dpd_0_7_usd", "dpd_7_30_usd", "dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd"]:
            if col in df.columns:
                ratios[col] = (df[col].sum() / total) * 100.0
        return ratios

    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw loan data into a KPI-ready dataset with ratios and metadata."""
        required = [
            "total_receivable_usd", "total_eligible_usd", "discounted_balance_usd",
            "dpd_0_7_usd", "dpd_7_30_usd", "dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd"
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Transformation failed: missing required columns: {missing}")

        for col in required:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column {col} must be numeric")

        kpi_df = df.copy()
        
        # Rename columns for KPI dataset
        kpi_df = kpi_df.rename(columns={
            "total_receivable_usd": "receivable_amount",
            "total_eligible_usd": "eligible_amount",
            "discounted_balance_usd": "discounted_amount"
        })

        # Calculate row-level percentages
        receivable = kpi_df["receivable_amount"].replace(0, np.nan)
        for col in ["dpd_0_7_usd", "dpd_7_30_usd", "dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd"]:
            if col in df.columns:
                kpi_df[f"{col}_pct"] = (df[col] / receivable).fillna(0.0) * 100
        
        kpi_df["_transform_run_id"] = self.run_id
        kpi_df["_transform_timestamp"] = datetime.now(timezone.utc).isoformat()
        
        self.transformations_count += 1
        return kpi_df

    def validate_transformations(self, original: pd.DataFrame, transformed: pd.DataFrame) -> bool:
        """Validate that the transformation preserved data integrity."""
        if len(original) != len(transformed):
            return False
        
        if "total_receivable_usd" in original.columns and "receivable_amount" in transformed.columns:
            orig_sum = original["total_receivable_usd"].sum()
            trans_sum = transformed["receivable_amount"].sum()
            if not np.isclose(orig_sum, trans_sum):
                return False
        
        return True