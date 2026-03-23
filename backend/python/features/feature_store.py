"""Feature Store for loan and borrower variables.

Provides a centralized way to calculate, normalize, and version features
for predictive models. Features are decoupled from the models themselves
to allow reuse and reproducibility.
"""

from __future__ import annotations

import json
import logging
from contextlib import suppress
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

    def compute_features(
        self,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame | None = None,
        customer_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Calculate engineered features from raw data.

        Parameters
        ----------
        loan_df : pd.DataFrame
            Raw loan data. Should include 'loan_id' for mapping.
        payment_df : pd.DataFrame, optional
            Payment history data for behavioral features.
        customer_df : pd.DataFrame, optional
            Customer profile data (industry, scores).

        Returns
        -------
        pd.DataFrame
            Calculated features.
        """
        # We reuse the logic from ScorecardModel to ensure consistency
        from backend.python.models.scorecard_model import ScorecardModel

        # If dataframes are missing, we use empty ones to avoid errors in build_model_dataset
        p_df = payment_df if payment_df is not None else pd.DataFrame()
        c_df = customer_df if customer_df is not None else pd.DataFrame()

        # build_model_dataset performs normalization and merging
        enriched_df = ScorecardModel.build_model_dataset(loan_df.copy(), p_df.copy(), c_df.copy())

        # Select only feature columns (exclude IDs and target)
        exclude = ["is_default", "loan_id", "customer_id", "disbursement_date", "status", "current_status", "_is_late"]
        feature_cols = [c for c in enriched_df.columns if c not in exclude]

        features = enriched_df[feature_cols].copy()
        
        # Ensure unique columns (in case of overlap during merge)
        features = features.loc[:, ~features.columns.duplicated()]

        # Ensure numeric conversion
        for col in features.columns:
            if features[col].dtype == object:
                # Attempt to convert to numeric, if fail keep as is (could be categorical)
                with suppress(ValueError, TypeError):
                    features[col] = pd.to_numeric(features[col])

        # Drop non-numeric columns that couldn't be converted
        features = features.select_dtypes(include=[np.number, "bool"])

        # Preserve loan_id if present for the feature store mapping
        if "loan_id" in enriched_df.columns:
            features.insert(0, "loan_id", enriched_df["loan_id"])

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
