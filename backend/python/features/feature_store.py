"""Feature Store for loan and borrower variables.

Provides a centralized way to calculate, normalize, and version features
for predictive models. Features are decoupled from the models themselves
to allow reuse and reproducibility.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureStore:
    """Centralized feature management for loan risk models."""

    def __init__(self, storage_dir: str = "data/features") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate engineered features from raw data.

        Parameters
        ----------
        df : pd.DataFrame
            Raw loan data. Should include 'loan_id' for mapping.

        Returns
        -------
        pd.DataFrame
            Calculated features.
        """
        # Numeric base features
        numeric_cols = [
            "principal_amount",
            "interest_rate",
            "term_months",
            "collateral_value",
            "outstanding_balance",
            "tpv",
            "equifax_score",
            "last_payment_amount",
            "total_scheduled",
            "origination_fee",
            "days_past_due",
        ]

        features = pd.DataFrame()

        # Preserve loan_id if present
        if "loan_id" in df.columns:
            features["loan_id"] = df["loan_id"]

        for col in numeric_cols:
            if col in df.columns:
                features[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                features[col] = 0.0

        # Engineered features
        features["ltv_ratio"] = np.where(
            features["collateral_value"] > 0,
            features["outstanding_balance"] / features["collateral_value"] * 100,
            0.0,
        )
        features["payment_ratio"] = np.where(
            features["total_scheduled"] > 0,
            features["last_payment_amount"] / features["total_scheduled"] * 100,
            0.0,
        )

        # Normalization (optional, but requested by user)
        # For now, we'll just ensure they are filled
        features = features.fillna(0.0)

        return features

    def get_features_for_loan(self, loan_id: str) -> dict[str, Any] | None:
        """Retrieve features for a specific loan from the latest version.

        Parameters
        ----------
        loan_id : str
            Unique loan identifier.

        Returns
        -------
        dict or None
            Feature dictionary if found.
        """
        try:
            df = self.get_latest_features()
            if "loan_id" not in df.columns:
                return None

            loan_features = df[df["loan_id"] == loan_id]
            if loan_features.empty:
                return None

            return loan_features.iloc[0].drop("loan_id").to_dict()
        except Exception as e:
            logger.error("Error retrieving features for loan %s: %s", loan_id, e)
            return None

    def save_features(self, features: pd.DataFrame, version: str | None = None) -> Path:
        """Persist features to disk with versioning.

        Parameters
        ----------
        features : pd.DataFrame
            Calculated features to save.
        version : str, optional
            Explicit version name. Defaults to current timestamp.

        Returns
        -------
        Path
            Path where the features were saved.
        """
        if version is None:
            version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        version_dir = self.storage_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Save as Parquet (preferred for tabular data with schema) or CSV
        file_path = version_dir / "features.parquet"
        try:
            features.to_parquet(file_path, index=False)
        except ImportError:
            # Fallback to CSV if pyarrow/fastparquet is missing
            file_path = version_dir / "features.csv"
            features.to_csv(file_path, index=False)

        # Metadata
        metadata = {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "num_rows": len(features),
            "columns": list(features.columns),
        }
        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info("Saved version %s to %s", version, file_path)
        return file_path

    def get_latest_features(self) -> pd.DataFrame:
        """Retrieve the most recent version of features."""
        versions = sorted([d for d in self.storage_dir.iterdir() if d.is_dir()])
        if not versions:
            raise FileNotFoundError("No feature versions found")

        latest_dir = versions[-1]
        parquet_path = latest_dir / "features.parquet"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)

        csv_path = latest_dir / "features.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path)

        raise FileNotFoundError(f"No feature files found in {latest_dir}")
