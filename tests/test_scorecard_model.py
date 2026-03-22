"""Tests for ScorecardModel — synthetic data matching Ábaco CSV schema.

These tests validate the full pipeline without requiring real data:
  - Dataset construction from loan + payment + customer CSVs
  - WoE/IV computation and feature selection
  - Logistic regression training and cross-validation
  - Score scaling (300–850)
  - Persistence (save/load roundtrip)
  - Single-loan inference

Run:
    pytest tests/test_scorecard_model.py -v
"""

from __future__ import annotations

import json
import random
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── Synthetic data generators ────────────────────────────────────────────────

INDUSTRIES = [
    "Comercio al por menor",
    "Otras actividades especializadas de construcción",
    "Transporte de carga",
    "Servicios de alimentación",
    "Manufactura textil",
    "Agricultura y ganadería",
    "Servicios profesionales",
]

LOAN_STATUSES = ["active", "closed", "defaulted", "active", "active", "closed"]  # weighted


def make_loan_df(n: int = 800, n_defaults: int = 80, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic loan_data.csv with realistic Ábaco schema."""
    rng = random.Random(seed)
    np.random.seed(seed)

    records = []
    for i in range(n):
        is_default = i < n_defaults
        status = "defaulted" if is_default else rng.choice(["active", "closed"])
        days_past_due = rng.randint(60, 365) if is_default else rng.randint(0, 15)

        principal = rng.uniform(5_000, 150_000)
        outstanding = principal * rng.uniform(0.3, 0.95) if not is_default else principal * rng.uniform(0.6, 1.0)
        collateral = principal * rng.uniform(0.8, 2.5)

        disbursement_days_ago = rng.randint(90, 900)
        disbursement_date = pd.Timestamp.today() - pd.Timedelta(days=disbursement_days_ago)

        records.append({
            "loan_id": f"LN-{i+1:05d}",
            "customer_id": f"CUST-{i+1:05d}",
            "disbursement_date": disbursement_date.strftime("%Y-%m-%d"),
            "principal_amount": round(principal, 2),
            "outstanding_balance": round(outstanding, 2),
            "collateral_value": round(collateral, 2),
            "interest_rate": round(rng.uniform(0.12, 0.42), 4),
            "term_months": rng.choice([6, 9, 12, 18, 24]),
            "days_past_due": days_past_due,
            "status": status,
            "last_payment_amount": round(rng.uniform(500, 5_000), 2),
            "total_scheduled": round(rng.uniform(1_000, 8_000), 2),
            "tpv": round(rng.uniform(50_000, 2_000_000), 2),
            "origination_fee": round(principal * rng.uniform(0.01, 0.03), 2),
        })

    df = pd.DataFrame(records)
    # Shuffle so defaults aren't all at top
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def make_payment_df(loan_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic real_payment.csv with late payment history."""
    rng = random.Random(seed)
    records = []

    for _, loan in loan_df.iterrows():
        is_defaulted = loan["status"] == "defaulted"
        n_payments = rng.randint(3, 18)

        disb_date = pd.Timestamp(loan["disbursement_date"])

        for p in range(n_payments):
            # Defaulted loans have more late payments
            if is_defaulted:
                is_late = rng.random() < 0.6
            else:
                is_late = rng.random() < 0.05

            payment_date = disb_date + pd.Timedelta(days=30 * (p + 1) + rng.randint(-5, 30))

            records.append({
                "loan_id": loan["loan_id"],
                "payment_date": payment_date.strftime("%Y-%m-%d"),
                "amount": round(rng.uniform(500, 6_000), 2),
                "status": "Late" if is_late else "On-time",
            })

    return pd.DataFrame(records)


def make_customer_df(loan_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic customer_data.csv with industry and credit score."""
    rng = random.Random(seed)
    records = []

    for _, loan in loan_df.iterrows():
        is_defaulted = loan["status"] == "defaulted"
        # Defaulted customers tend to have lower Equifax scores
        equifax = rng.randint(300, 580) if is_defaulted else rng.randint(550, 820)

        records.append({
            "customer_id": loan["customer_id"],
            "industry": rng.choice(INDUSTRIES),
            "equifax_score": equifax,
        })

    return pd.DataFrame(records)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sample_data():
    """Generate a consistent synthetic dataset for all tests."""
    loan_df = make_loan_df(n=800, n_defaults=80)
    payment_df = make_payment_df(loan_df)
    customer_df = make_customer_df(loan_df)
    return loan_df, payment_df, customer_df


@pytest.fixture(scope="module")
def trained_model(sample_data):
    """Train a scorecard on synthetic data — shared across tests."""
    from backend.python.models.scorecard_model import ScorecardModel

    loan_df, payment_df, customer_df = sample_data
    model = ScorecardModel()
    metrics = model.fit(loan_df, payment_df, customer_df, iv_threshold=0.01, cv_folds=3)
    return model, metrics


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDatasetConstruction:
    def test_target_created(self, sample_data):
        from backend.python.models.scorecard_model import ScorecardModel
        loan_df, payment_df, customer_df = sample_data
        df = ScorecardModel.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        assert "is_default" in df.columns
        assert df["is_default"].sum() > 0, "No defaults found — check status mapping"

    def test_behavioral_features_created(self, sample_data):
        from backend.python.models.scorecard_model import ScorecardModel
        loan_df, payment_df, customer_df = sample_data
        df = ScorecardModel.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        assert "n_late_payments" in df.columns, "Behavioral feature n_late_payments missing"
        assert "late_payment_rate" in df.columns
        assert "max_consecutive_late" in df.columns

    def test_customer_features_merged(self, sample_data):
        from backend.python.models.scorecard_model import ScorecardModel
        loan_df, payment_df, customer_df = sample_data
        df = ScorecardModel.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        assert "industry" in df.columns or "equifax_score" in df.columns, \
            "Customer features not merged"

    def test_ltv_ratio_computed(self, sample_data):
        from backend.python.models.scorecard_model import ScorecardModel
        loan_df, payment_df, customer_df = sample_data
        df = ScorecardModel.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        if "ltv_ratio" in df.columns:
            assert df["ltv_ratio"].notna().sum() > 0


class TestIVComputation:
    def test_iv_table_has_rows(self, trained_model):
        model, _ = trained_model
        assert len(model.iv_table) > 0, "IV table is empty"

    def test_iv_table_columns(self, trained_model):
        model, _ = trained_model
        required = {"feature", "iv", "predictive_power", "n_bins"}
        assert required.issubset(set(model.iv_table.columns))

    def test_iv_sorted_descending(self, trained_model):
        model, _ = trained_model
        ivs = model.iv_table["iv"].values
        assert all(ivs[i] >= ivs[i + 1] for i in range(len(ivs) - 1)), \
            "IV table is not sorted descending"

    def test_behavioral_features_have_iv(self, trained_model):
        model, _ = trained_model
        feat_names = set(model.iv_table["feature"].tolist())
        # At least one behavioral feature should appear in IV table
        behavioral = {"n_late_payments", "late_payment_rate", "max_consecutive_late"}
        overlap = feat_names & behavioral
        assert len(overlap) > 0, \
            f"No behavioral features in IV table. Found: {feat_names}"


class TestModelTraining:
    def test_metrics_present(self, trained_model):
        _, result = trained_model
        metrics = result.get("metrics", {})
        required = {"auc_roc", "gini_coefficient", "ks_statistic", "cv_auc_mean"}
        assert required.issubset(set(metrics.keys()))

    def test_auc_above_random(self, trained_model):
        _, result = trained_model
        metrics = result.get("metrics", {})
        assert metrics["auc_roc"] > 0.5, \
            f"AUC {metrics['auc_roc']:.4f} is at or below random chance"

    def test_gini_positive(self, trained_model):
        _, result = trained_model
        metrics = result.get("metrics", {})
        assert metrics["gini_coefficient"] > 0

    def test_ks_positive(self, trained_model):
        _, result = trained_model
        metrics = result.get("metrics", {})
        assert metrics["ks_statistic"] > 0

    def test_features_selected(self, trained_model):
        model, _ = trained_model
        assert len(model.selected_features) > 0, "No features selected"

    def test_scorecard_table_populated(self, trained_model):
        model, _ = trained_model
        assert not model.scorecard_table.empty, "Scorecard table is empty"
        required_cols = {"feature", "bin", "woe", "points", "event_rate"}
        assert required_cols.issubset(set(model.scorecard_table.columns))


class TestScoreScaling:
    def test_score_distribution_present(self, trained_model):
        _, metrics = trained_model
        sd = metrics.get("score_distribution", {})
        assert "defaults_mean_score" in sd
        assert "non_defaults_mean_score" in sd

    def test_defaults_score_lower(self, trained_model):
        """Core logic check: defaults should have lower scores than non-defaults."""
        _, metrics = trained_model
        sd = metrics.get("score_distribution", {})
        defaults_score = sd.get("defaults_mean_score", 999)
        non_defaults_score = sd.get("non_defaults_mean_score", 0)
        assert defaults_score < non_defaults_score, (
            f"Defaults score ({defaults_score}) should be < non-defaults ({non_defaults_score}). "
            "Score direction is inverted — check scaling logic."
        )

    def test_single_loan_score_in_range(self, trained_model, sample_data):
        model, _ = trained_model
        loan_df, payment_df, customer_df = sample_data

        # Build a sample loan feature dict from the first loan
        df = ScorecardModel.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        first_loan = df.iloc[0].to_dict()

        score = model.predict_score(first_loan)
        assert 300 <= score <= 850, f"Score {score} outside valid range [300, 850]"

    def test_single_loan_pd_in_range(self, trained_model, sample_data):
        from backend.python.models.scorecard_model import ScorecardModel as SC
        model, _ = trained_model
        loan_df, payment_df, customer_df = sample_data
        df = SC.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        first_loan = df.iloc[0].to_dict()
        pd_prob = model.predict_proba(first_loan)
        assert 0.0 <= pd_prob <= 1.0, f"PD probability {pd_prob} outside [0, 1]"


class TestPersistence:
    def test_save_and_load_roundtrip(self, trained_model, sample_data, tmp_path):
        from backend.python.models.scorecard_model import ScorecardModel as SC
        model, _ = trained_model
        loan_df, payment_df, customer_df = sample_data

        save_dir = str(tmp_path / "scorecard_test")
        model.save(save_dir)

        # Verify all expected files exist
        for fname in ["lr_model.pkl", "binning_map.pkl", "iv_table.csv",
                      "scorecard_table.csv", "metadata.json"]:
            assert (Path(save_dir) / fname).exists(), f"{fname} not saved"

        loaded = SC.load(save_dir)
        assert loaded.lr_model is not None
        assert len(loaded.selected_features) == len(model.selected_features)
        assert not loaded.iv_table.empty
        assert not loaded.scorecard_table.empty

    def test_loaded_model_produces_same_score(self, trained_model, sample_data, tmp_path):
        from backend.python.models.scorecard_model import ScorecardModel as SC
        model, _ = trained_model
        loan_df, payment_df, customer_df = sample_data

        df = SC.build_model_dataset(loan_df.copy(), payment_df.copy(), customer_df.copy())
        test_loan = df.iloc[5].to_dict()

        original_score = model.predict_score(test_loan)

        save_dir = str(tmp_path / "roundtrip_test")
        model.save(save_dir)
        loaded = SC.load(save_dir)
        loaded_score = loaded.predict_score(test_loan)

        assert original_score == loaded_score, \
            f"Score mismatch after load: {original_score} vs {loaded_score}"

    def test_metadata_json_valid(self, trained_model, tmp_path):
        model, _ = trained_model
        save_dir = str(tmp_path / "meta_test")
        model.save(save_dir)

        with open(Path(save_dir) / "metadata.json") as f:
            meta = json.load(f)

        assert "model_type" in meta
        assert "metrics" in meta
        assert "features" in meta
        assert meta["metrics"]["auc_roc"] > 0


# ── Import guard ──────────────────────────────────────────────────────────────
# Needed for the fixture type hint in test_single_loan_pd_in_range
from backend.python.models.scorecard_model import ScorecardModel  # noqa: E402


if __name__ == "__main__":
    import pytest as pt
    pt.main([__file__, "-v"])
