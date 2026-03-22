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
from pathlib import Path

import pandas as pd

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.python.features.feature_store import FeatureStore
from backend.python.models.default_risk_model import DefaultRiskModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("retrain_pipeline")

def run_pipeline(input_path: Path, model_dir: Path, threshold_auc: float = 0.7) -> bool:
    logger.info("Starting retraining pipeline with input: %s", input_path)

    if not input_path.exists():
        logger.error("Input data not found: %s", input_path)
        return False

    # 1. Load Data
    df = pd.read_csv(input_path, low_memory=False)
    if df.empty:
        logger.error("Empty dataset provided")
        return False

    # 2. Feature Store - Compute and Save
    fs = FeatureStore()
    features_df = fs.compute_features(df)

    # We also need the target from the original df
    model_helper = DefaultRiskModel()
    y = model_helper.prepare_target(df)
    features_df["is_default"] = y

    version = input_path.stem  # Use filename or timestamp
    fs.save_features(features_df, version=version)
    logger.info("Features versioned as: %s", version)

    # 3. Train Model
    metrics = model_helper.train(df) # train() internally prepares features
    logger.info("Training complete. Metrics: %s", json.dumps(metrics, indent=2))

    # 4. Validation & Deployment
    current_auc = metrics.get("auc_roc", 0)
    if current_auc < threshold_auc:
        logger.warning("AUC (%.4f) below threshold (%.4f). Aborting deployment.", current_auc, threshold_auc)
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
    parser.add_argument("--input", type=Path, default=Path("data/samples/abaco_sample_data_20260202.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/risk"))
    parser.add_argument("--threshold", type=float, default=0.7)

    args = parser.parse_args()

    success = run_pipeline(args.input, args.output_dir, args.threshold)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
