"""
Default Risk Prediction Model using XGBoost.

Predicts the probability of loan default based on loan and borrower features.
Target: current_status == 'Default' (binary classification).

Features used (post-engineering):
  - principal_amount, interest_rate, term_months, collateral_value
  - outstanding_balance, tpv, equifax_score
  - last_payment_amount, total_scheduled, origination_fee
  - ltv_ratio (outstanding_balance / collateral_value)
  - payment_ratio (last_payment_amount / total_scheduled)
  - days_past_due (real-time risk signal)

Usage:
    # Training
    python scripts/train_default_risk_model.py

    # Inference
    from python.models.default_risk_model import DefaultRiskModel
    model = DefaultRiskModel.load("models/risk/default_risk_xgb.json")
    prob = model.predict_proba(loan_features_dict)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

logger = logging.getLogger(__name__)

# Features used for model training and inference
NUMERIC_FEATURES = [
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

ENGINEERED_FEATURES = [
    "ltv_ratio",
    "payment_ratio",
]

ALL_FEATURES = NUMERIC_FEATURES + ENGINEERED_FEATURES

TARGET_COL = "is_default"


class DefaultRiskModel:
    """XGBoost-based default risk prediction model."""

    def __init__(self, model: Optional[xgb.XGBClassifier] = None):
        self.model = model
        self.feature_names = ALL_FEATURES
        self.metadata: Dict[str, Any] = {}

    @staticmethod
    def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and engineer features from raw loan data."""
        features = pd.DataFrame()

        # Map column names (handle both raw CSV and API formats)
        col_map = {
            "Equifax Score": "equifax_score",
            "equifax_score": "equifax_score",
        }

        for col in NUMERIC_FEATURES:
            source_col = col_map.get(col, col)
            if source_col in df.columns:
                features[col] = pd.to_numeric(df[source_col], errors="coerce")
            elif col in df.columns:
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

        # Fill NaN with median (robust to outliers)
        for col in ALL_FEATURES:
            if features[col].isna().any():
                median_val = features[col].median()
                features[col] = features[col].fillna(
                    median_val if not np.isnan(median_val) else 0.0
                )

        return features[ALL_FEATURES]

    @staticmethod
    def prepare_target(df: pd.DataFrame) -> pd.Series:
        """Prepare binary target: 1 = Default, 0 = Not Default."""
        status_col = None
        for col in ["current_status", "status"]:
            if col in df.columns:
                status_col = col
                break

        if status_col is None:
            raise ValueError("No status column found in data")

        return (df[status_col].str.strip().str.lower() == "default").astype(int)

    def train(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42,
        exclude_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Train the model on loan data and return evaluation metrics."""
        logger.info("Preparing features and target...")
        X = self.prepare_features(df)
        y = self.prepare_target(df)

        # Drop excluded features (e.g. days_past_due for origination model)
        if exclude_features:
            X = X.drop(columns=[c for c in exclude_features if c in X.columns])
            self.feature_names = list(X.columns)

        # Class imbalance ratio for scale_pos_weight
        n_neg = (y == 0).sum()
        n_pos = (y == 1).sum()
        scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

        logger.info(
            "Dataset: %d samples, %d defaults (%.2f%%), scale_pos_weight=%.1f",
            len(y),
            n_pos,
            n_pos / len(y) * 100,
            scale_pos_weight,
        )

        # Train/test split (stratified)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )

        # XGBoost classifier
        self.model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric="auc",
            random_state=random_state,
            tree_method="hist",
        )

        logger.info("Training XGBoost model...")
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_proba)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        # Feature importance
        used_features = list(X_train.columns)
        importance = dict(zip(used_features, self.model.feature_importances_.tolist()))
        importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        # Cross-validation AUC
        cv_aucs = []
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        for train_idx, val_idx in skf.split(X, y):
            X_cv_train, X_cv_val = X.iloc[train_idx], X.iloc[val_idx]
            y_cv_train, y_cv_val = y.iloc[train_idx], y.iloc[val_idx]

            cv_model = xgb.XGBClassifier(
                n_estimators=300,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos_weight,
                eval_metric="auc",
                random_state=random_state,
                tree_method="hist",
            )
            cv_model.fit(X_cv_train, y_cv_train, verbose=False)
            cv_proba = cv_model.predict_proba(X_cv_val)[:, 1]
            cv_aucs.append(roc_auc_score(y_cv_val, cv_proba))

        metrics = {
            "auc_roc": round(auc, 4),
            "cv_auc_mean": round(np.mean(cv_aucs), 4),
            "cv_auc_std": round(np.std(cv_aucs), 4),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "n_defaults_train": int(y_train.sum()),
            "n_defaults_test": int(y_test.sum()),
            "feature_importance": importance_sorted,
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
        }

        self.metadata = {
            "model_type": "XGBClassifier",
            "n_estimators": 300,
            "max_depth": 5,
            "features": ALL_FEATURES,
            "metrics": metrics,
        }

        logger.info(
            "Model trained: AUC=%.4f, CV AUC=%.4f +/- %.4f", auc, np.mean(cv_aucs), np.std(cv_aucs)
        )
        return metrics

    def predict_proba(self, loan_data: Dict[str, Any]) -> float:
        """Predict default probability for a single loan."""
        if self.model is None:
            raise RuntimeError("Model not trained or loaded")

        df = pd.DataFrame([loan_data])
        X = self.prepare_features(df)
        # Only keep features the model was trained on
        X = X[[c for c in self.feature_names if c in X.columns]]
        proba = self.model.predict_proba(X)[:, 1]
        return float(proba[0])

    def predict_batch(self, df: pd.DataFrame) -> pd.Series:
        """Predict default probabilities for a batch of loans."""
        if self.model is None:
            raise RuntimeError("Model not trained or loaded")

        X = self.prepare_features(df)
        X = X[[c for c in self.feature_names if c in X.columns]]
        return pd.Series(self.model.predict_proba(X)[:, 1], index=df.index)

    def save(self, model_dir: str = "models/risk") -> str:
        """Save model and metadata to disk."""
        if self.model is None:
            raise RuntimeError("No model to save")

        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)

        model_path = path / "default_risk_xgb.json"
        self.model.save_model(str(model_path))

        meta_path = path / "default_risk_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(self.metadata, f, indent=2, default=str)

        logger.info("Model saved to %s", model_path)
        return str(model_path)

    @classmethod
    def load(cls, model_path: str = "models/risk/default_risk_xgb.json") -> "DefaultRiskModel":
        """Load a trained model from disk."""
        model = xgb.XGBClassifier()
        model.load_model(model_path)

        instance = cls(model=model)

        meta_path = Path(model_path).parent / "default_risk_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                instance.metadata = json.load(f)

        logger.info("Model loaded from %s", model_path)
        return instance
