#!/usr/bin/env python3
"""Automated retraining pipeline for the Default Risk Model.

Steps:
1. Load historical data.
2. Calculate and version features via FeatureStore.
3. Train a new model.
4. Compare performance metrics.
5. Deploy (persist) if metrics meet thresholds.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("retrain_pipeline")


def run_pipeline(
    loan_path: Path,
    payment_path: Optional[Path] = None,
    customer_path: Optional[Path] = None,
    model_dir: Path = Path("models/risk"),
    threshold_auc: float = 0.7,
    iv_threshold: float = 0.02,
) -> bool:
    from backend.python.features.feature_store import FeatureStore
    from backend.python.models.default_risk_model import DefaultRiskModel
    from backend.python.models.scorecard_model import ScorecardModel

    logger.info("Starting retraining pipeline...")

    if not loan_path.exists():
        logger.error("Loan data not found: %s", loan_path)
        return False

    # 1. Load Data
    loan_df = pd.read_csv(loan_path, low_memory=False)
    payment_df = pd.read_csv(payment_path, low_memory=False) if payment_path and payment_path.exists() else pd.DataFrame()
    customer_df = pd.read_csv(customer_path, low_memory=False) if customer_path and customer_path.exists() else pd.DataFrame()

    if loan_df.empty:
        logger.error("Empty loan dataset provided")
        return False

    # 2. Phase 1: Feature Selection via Scorecard IV
    logger.info("Phase 1: Analyzing predictive power (IV)...")
    scorecard = ScorecardModel()
    # scorecard.fit internally builds model dataset and computes IV
    try:
        scorecard.fit(
            loan_df=loan_df,
            payment_df=payment_df,
            customer_df=customer_df,
            iv_threshold=iv_threshold
        )
        selected_features = scorecard.selected_features
        logger.info("Selected %d features based on IV >= %.3f", len(selected_features), iv_threshold)
    except Exception as e:
        logger.error("Scorecard fit failed: %s", e)
        selected_features = None

    # 3. Feature Store - Compute and Save
    fs = FeatureStore()
    features_df = fs.compute_features(loan_df, payment_df, customer_df)

    # Add target for persistence
    model_helper = DefaultRiskModel()
    y = model_helper.prepare_target(loan_df)
    features_df["is_default"] = y

    version = f"retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    fs.save_features(features_df, version=version)
    logger.info("Features versioned as: %s", version)

    # 4. Phase 2: Train XGBoost Model
    logger.info("Phase 2: Training XGBoost model...")
    metrics = model_helper.train(
        df=loan_df,
        payment_df=payment_df,
        customer_df=customer_df,
        selected_features=selected_features
    )
    logger.info("Training complete. Metrics: %s", json.dumps(metrics, indent=2))

    # 5. Validation & Deployment
    current_auc = metrics.get("auc_roc", 0)
    if current_auc < threshold_auc:
        logger.warning(
            "AUC (%.4f) below threshold (%.4f). Aborting deployment.", current_auc, threshold_auc
        )
        return False

    # Save model
    model_path = model_helper.save(str(model_dir))
    logger.info("Model deployed to: %s", model_path)

    # Save validation report
    report_path = model_dir / "latest_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return True


def main():
    parser = argparse.ArgumentParser(description="Retrain PD model")
    parser.add_argument(
        "--loans", "--input", type=Path, default=Path("data/samples/abaco_sample_data_20260202.csv")
    )
    parser.add_argument("--payments", type=Path, default=None)
    parser.add_argument("--customers", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("models/risk"))
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--iv-threshold", type=float, default=0.02)

    args = parser.parse_args()

    success = run_pipeline(
        loan_path=args.loans,
        payment_path=args.payments,
        customer_path=args.customers,
        model_dir=args.output_dir,
        threshold_auc=args.threshold,
        iv_threshold=args.iv_threshold,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
