"""
Train the Default Risk XGBoost model on real loan data.

Trains two model variants:
1. Real-time risk scorer (includes days_past_due) — for live portfolio monitoring
2. Origination model (excludes DPD) — for underwriting/pre-disbursement scoring

Usage:
    cd project_root
    python scripts/train_default_risk_model.py

Output:
    models/risk/default_risk_xgb.json               — Real-time model
    models/risk/default_risk_metadata.json           — Real-time metrics
    models/risk/origination_risk_xgb.json            — Origination model
    models/risk/origination_risk_metadata.json       — Origination metrics
"""

import json
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from python.models.default_risk_model import DefaultRiskModel  # noqa: E402


def print_metrics(metrics, model_name, auc_target=0.75):
    print(f"\n{'=' * 60}")
    print(f"  {model_name}")
    print(f"{'=' * 60}")
    print(f"  AUC-ROC (test):     {metrics['auc_roc']:.4f}")
    print(f"  AUC-ROC (5-fold CV): {metrics['cv_auc_mean']:.4f} +/- {metrics['cv_auc_std']:.4f}")
    print(f"  Accuracy:           {metrics['accuracy']:.4f}")
    print(f"  Precision:          {metrics['precision']:.4f}")
    print(f"  Recall:             {metrics['recall']:.4f}")
    print(f"  F1 Score:           {metrics['f1_score']:.4f}")
    print(f"  Train/Test:         {metrics['train_size']:,} / {metrics['test_size']:,}")
    print(f"  Defaults (test):    {metrics['n_defaults_test']}")

    status = "PASS" if metrics["auc_roc"] >= auc_target else "FAIL"
    print(f"\n  AUC >= {auc_target}: {status}")

    print("\n  Feature Importance (top 10):")
    for i, (feat, imp) in enumerate(metrics["feature_importance"].items()):
        if i >= 10:
            break
        importance_bar = "#" * int(imp * 50)
        print(f"    {feat:25s} {imp:.4f} {importance_bar}")


def main():
    data_path = project_root / "data" / "raw" / "abaco_real_data_20260202.csv"

    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Rows: {df.shape[0]:,}, Columns: {df.shape[1]}")

    # Rename columns for model compatibility
    if "Equifax Score" in df.columns:
        df["equifax_score"] = df["Equifax Score"]

    print("\nTarget distribution:")
    status_counts = df["current_status"].value_counts()
    for status, count in status_counts.items():
        pct = count / len(df) * 100
        print(f"  {status}: {count:,} ({pct:.1f}%)")

    # --- Model 1: Real-time risk scorer (all features including DPD) ---
    print("\n[1/2] Training REAL-TIME risk model (includes DPD)...")
    rt_model = DefaultRiskModel()
    rt_metrics = rt_model.train(df)
    print_metrics(rt_metrics, "REAL-TIME RISK SCORER (with DPD)")
    rt_model.save("models/risk")

    # --- Model 2: Origination model (no DPD — true predictive power) ---
    print("\n[2/2] Training ORIGINATION risk model (excludes DPD)...")
    orig_model = DefaultRiskModel()
    orig_metrics = orig_model.train(df, exclude_features=["days_past_due"])
    print_metrics(orig_metrics, "ORIGINATION RISK MODEL (without DPD)")

    # Save origination model with different filenames
    orig_path = Path("models/risk")
    orig_path.mkdir(parents=True, exist_ok=True)
    orig_model.model.save_model(str(orig_path / "origination_risk_xgb.ubj"))

    with open(orig_path / "origination_risk_metadata.json", "w") as f:
        json.dump(orig_model.metadata, f, indent=2, default=str)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(
        f"  Real-time model:   AUC={rt_metrics['auc_roc']:.4f}  (models/risk/default_risk_xgb.json)"
    )
    print(
        f"  Origination model: AUC={orig_metrics['auc_roc']:.4f}  "
        f"(models/risk/origination_risk_xgb.json)"
    )

    if rt_metrics["auc_roc"] == 1.0:
        print("\n  NOTE: Real-time AUC=1.0 is expected — days_past_due is definitionally")
        print("        linked to default status. The origination model shows true")
        print("        predictive power from borrower/loan features alone.")

    # Inference test with origination model
    print("\nOrigination model inference test (3 loans each status):")
    for status_val in ["Current", "Complete", "Default"]:
        subset = df[df["current_status"] == status_val].head(3)
        for _, row in subset.iterrows():
            row_dict = row.to_dict()
            prob = orig_model.predict_proba(row_dict)
            loan_id = row_dict.get("loan_id", "?")
            print(f"  Loan {loan_id:15s} | {status_val:10s} | P(default)={prob:.4f}")


if __name__ == "__main__":
    main()
