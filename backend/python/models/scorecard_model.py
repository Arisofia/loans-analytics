"""Credit Scorecard Model using WoE (Weight of Evidence) / IV (Information Value).

Architecture:
  1. Optimal binning per variable (OptBinning) — finds statistically optimal
     bin boundaries that maximize WoE separation between defaults/non-defaults.
  2. IV filter — removes features with IV < 0.02 (no predictive power).
  3. Logistic Regression on WoE-transformed features — produces calibrated
     probability estimates and interpretable scorecard points.
  4. Score scaling — maps probabilities to a 300-850 point scale (credit
     bureau convention: higher = lower risk).

Why scorecard first (over XGBoost alone):
  - 301 defaults / 18k+ loans (~1.7% default rate) — low volume for
    ensemble methods; LR is more stable at this sample size.
  - WoE transformation handles non-linearity + outliers without feature
    engineering assumptions.
  - Output is directly interpretable by credit committees (points per bin).
  - IV table is the definitive feature selection input for the XGBoost
    model in Phase 2.

Usage:
    # Training
    model = ScorecardModel()
    result = model.fit(loan_df, payment_df, customer_df)
    model.save("models/scorecard")

    # Inference
    model = ScorecardModel.load("models/scorecard")
    score = model.predict_score(loan_features_dict)
    pd_prob = model.predict_proba(loan_features_dict)
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

# ── Score scaling parameters ────────────────────────────────────────────────
# Maps ln(odds) to 300–850 scale (standard credit bureau convention)
# PDO = 20 (Points to Double Odds), Base score = 600 at odds 50:1
BASE_SCORE = 600
PDO = 20
BASE_ODDS = 50.0

# ── IV thresholds ────────────────────────────────────────────────────────────
IV_USELESS = 0.02
IV_WEAK = 0.1
IV_MEDIUM = 0.3


class ScorecardModel:
    """WoE/IV logistic regression scorecard for credit default prediction."""

    def __init__(self) -> None:
        self.binning_map: Dict[str, Any] = {}      # feature -> OptimalBinning object
        self.iv_table: pd.DataFrame = pd.DataFrame()
        self.selected_features: List[str] = []
        self.lr_model: Optional[LogisticRegression] = None
        self.scorecard_table: pd.DataFrame = pd.DataFrame()
        self.metadata: Dict[str, Any] = {}
        self.feature_names_woe: List[str] = []     # WoE column names

    # ── Data preparation ────────────────────────────────────────────────────

    @staticmethod
    def build_model_dataset(
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        customer_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge loan, payment history, and customer data into a flat model table.

        Behavioral features engineered from payment history:
          - n_late_payments: total late payments in loan lifetime
          - late_payment_rate: n_late / total payments made
          - max_consecutive_late: longest streak of consecutive late payments
          - first_late_dpd: days_past_due at first late event
          - payment_volatility: std of payment amounts (normalized by scheduled)
          - days_to_first_late: days from disbursement to first late payment

        These behavioral signals are typically more predictive than
        origination-time features alone.
        """
        # ── Normalize column names ──────────────────────────────────────────
        # ── Normalize column names ─────────────────────────────────────────
        # list comprehension: safe for RangeIndex (empty DFs in inference path)
        def _norm_cols(df: "pd.DataFrame") -> None:
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        _norm_cols(loan_df)
        _norm_cols(payment_df)
        _norm_cols(customer_df)

        # ── Column resolver: finds first col whose name contains any pattern ─
        def _find(df: "pd.DataFrame", *patterns: str) -> "Optional[str]":
            for col in df.columns:
                for pat in patterns:
                    if pat in col:
                        return col
            return None

        # ── Target variable ──────────────────────────────────────────────────
        # Matches: loan_status, status, current_status, estado, estatus
        status_col = _find(loan_df, "status", "estado", "estatus")
        if status_col is None:
            raise ValueError(
                "No status column found in loan_df. "
                "Expected a column containing 'status' or 'estado'."
            )

        loan_df["is_default"] = (
            loan_df[status_col].str.strip().str.lower()
            .isin(["default", "defaulted", "mora", "en_mora", "castigado"])
            .astype(int)
        )

        # ── Days past due ────────────────────────────────────────────────────
        # Matches: days_past_due, days_in_default, dpd, dias_mora
        dpd_col = _find(loan_df, "days_past_due", "days_in_default", "dpd", "dias_mora", "dias_en_mora")
        if dpd_col:
            loan_df["days_past_due"] = pd.to_numeric(loan_df[dpd_col], errors="coerce").fillna(0)
        else:
            loan_df["days_past_due"] = 0.0

        # ── Outstanding balance ───────────────────────────────────────────────
        # Matches: outstanding_balance, outstanding_loan_value
        outstanding_col = _find(loan_df, "outstanding")
        if outstanding_col and outstanding_col != "outstanding_balance":
            loan_df["outstanding_balance"] = pd.to_numeric(loan_df[outstanding_col], errors="coerce")

        # ── Collateral value ──────────────────────────────────────────────────
        collateral_col = _find(loan_df, "collateral", "garantia", "garantía")
        if collateral_col and collateral_col != "collateral_value":
            loan_df["collateral_value"] = pd.to_numeric(loan_df[collateral_col], errors="coerce")

        # ── Interest rate ─────────────────────────────────────────────────────
        # Matches: interest_rate, interest_rate_apr, apr, tasa
        rate_col = _find(loan_df, "interest_rate", "interest", "tasa_interes", "tasa", "apr")
        if rate_col and rate_col != "interest_rate":
            loan_df["interest_rate"] = pd.to_numeric(loan_df[rate_col], errors="coerce")

        # ── Principal amount ──────────────────────────────────────────────────
        principal_col = _find(
            loan_df, "principal_amount", "principal", "loan_amount", "monto_prestamo", "monto_desembolsado"
        )
        if principal_col and principal_col != "principal_amount":
            loan_df["principal_amount"] = pd.to_numeric(loan_df[principal_col], errors="coerce")

        # ── Origination date ──────────────────────────────────────────────────
        date_col = _find(loan_df, "disburs", "originat", "fecha_desembolso")
        if date_col:
            loan_df[date_col] = pd.to_datetime(loan_df[date_col], errors="coerce")
            loan_df["loan_age_days"] = (
                pd.Timestamp.today() - loan_df[date_col]
            ).dt.days.clip(lower=0)
            loan_df["vintage_quarter"] = loan_df[date_col].dt.to_period("Q").astype(str)

        # ── LTV ratio ─────────────────────────────────────────────────────────
        if "outstanding_balance" in loan_df.columns and "collateral_value" in loan_df.columns:
            loan_df["ltv_ratio"] = np.where(
                pd.to_numeric(loan_df["collateral_value"], errors="coerce").fillna(0) > 0,
                pd.to_numeric(loan_df["outstanding_balance"], errors="coerce").fillna(0)
                / pd.to_numeric(loan_df["collateral_value"], errors="coerce").fillna(1) * 100,
                np.nan,
            )

        # ── Payment ratio ─────────────────────────────────────────────────────
        if "last_payment_amount" in loan_df.columns and "total_scheduled" in loan_df.columns:
            loan_df["payment_ratio"] = np.where(
                pd.to_numeric(loan_df["total_scheduled"], errors="coerce").fillna(0) > 0,
                pd.to_numeric(loan_df["last_payment_amount"], errors="coerce").fillna(0)
                / pd.to_numeric(loan_df["total_scheduled"], errors="coerce").fillna(1) * 100,
                np.nan,
            )

        # ── Behavioral features from payment history ──────────────────────────
        # loan_id in payment file: matches loan_id, prestamo_id, id_prestamo, loan
        loan_id_col_pay = _find(payment_df, "loan_id", "prestamo_id", "id_prestamo")
        # loan_id in loan file
        loan_id_col_loan = _find(loan_df, "loan_id", "id_prestamo", "prestamo_id")

        if loan_id_col_pay and loan_id_col_loan:
            status_pay_col = _find(payment_df, "status", "estado", "estatus")
            # Matches: true_total_payment, amount, true_payment_amount, monto, valor
            amount_pay_col = _find(payment_df, "total_payment", "true_total", "amount", "monto", "valor")
            date_pay_col = next(
                (c for c in payment_df.columns if "date" in c or "fecha" in c),
                None,
            )

            if status_pay_col:
                payment_df["_is_late"] = (
                    payment_df[status_pay_col].str.strip().str.lower()
                    .isin(["late", "tardio", "tardío", "mora", "atrasado"])
                    .astype(int)
                )

                beh = payment_df.groupby(loan_id_col_pay).agg(
                    n_payments=("_is_late", "count"),
                    n_late_payments=("_is_late", "sum"),
                ).reset_index()
                beh.columns = [loan_id_col_loan, "n_payments", "n_late_payments"]
                beh["late_payment_rate"] = np.where(
                    beh["n_payments"] > 0,
                    beh["n_late_payments"] / beh["n_payments"],
                    0.0,
                )

                # Max consecutive late payments
                def max_consecutive(series: pd.Series) -> int:
                    max_c = cur_c = 0
                    for v in series:
                        if v == 1:
                            cur_c += 1
                            max_c = max(max_c, cur_c)
                        else:
                            cur_c = 0
                    return max_c

                consec = (
                    payment_df.sort_values([loan_id_col_pay, date_pay_col] if date_pay_col else [loan_id_col_pay])
                    .groupby(loan_id_col_pay)["_is_late"]
                    .apply(max_consecutive)
                    .reset_index()
                )
                consec.columns = [loan_id_col_loan, "max_consecutive_late"]
                beh = beh.merge(consec, on=loan_id_col_loan, how="left")

                # Payment amount volatility
                if amount_pay_col:
                    payment_df[amount_pay_col] = pd.to_numeric(payment_df[amount_pay_col], errors="coerce")
                    vol = (
                        payment_df.groupby(loan_id_col_pay)[amount_pay_col]
                        .std()
                        .reset_index()
                    )
                    vol.columns = [loan_id_col_loan, "payment_amount_std"]
                    beh = beh.merge(vol, on=loan_id_col_loan, how="left")

                # Days to first late payment
                if date_pay_col and date_col:
                    payment_df[date_pay_col] = pd.to_datetime(payment_df[date_pay_col], errors="coerce")
                    first_late = (
                        payment_df[payment_df["_is_late"] == 1]
                        .sort_values(date_pay_col)
                        .groupby(loan_id_col_pay)[date_pay_col]
                        .first()
                        .reset_index()
                    )
                    first_late.columns = [loan_id_col_loan, "_first_late_date"]

                    loan_df = loan_df.merge(first_late, on=loan_id_col_loan, how="left")
                    loan_df["days_to_first_late"] = (
                        loan_df["_first_late_date"] - loan_df[date_col]
                    ).dt.days
                    loan_df.drop(columns=["_first_late_date"], inplace=True)

                loan_df = loan_df.merge(beh, on=loan_id_col_loan, how="left")
                logger.info(
                    "Behavioral features added: n_late_payments, late_payment_rate, "
                    "max_consecutive_late, payment_amount_std"
                )

        # ── Customer features ────────────────────────────────────────────────
        cust_id_col_cust = next(
            (c for c in customer_df.columns if "customer_id" in c or "cliente_id" in c or "borrower_id" in c),
            None,
        )
        cust_id_col_loan = next(
            (c for c in loan_df.columns if "customer_id" in c or "cliente_id" in c or "borrower_id" in c),
            None,
        )

        if cust_id_col_cust and cust_id_col_loan:
            industry_col = next(
                (c for c in customer_df.columns if "industry" in c or "sector" in c or "giro" in c),
                None,
            )
            score_col = next(
                (c for c in customer_df.columns if "equifax" in c or "score" in c or "buro" in c),
                None,
            )

            keep_cols = [cust_id_col_cust]
            if industry_col:
                keep_cols.append(industry_col)
                customer_df[industry_col] = customer_df[industry_col].str.strip()
            if score_col:
                keep_cols.append(score_col)
                customer_df[score_col] = pd.to_numeric(customer_df[score_col], errors="coerce")

            loan_df = loan_df.merge(
                customer_df[keep_cols].rename(columns={cust_id_col_cust: cust_id_col_loan}),
                on=cust_id_col_loan,
                how="left",
            )
            logger.info("Customer features merged: %s", keep_cols)

        logger.info(
            "Model dataset: %d rows, %d defaults (%.2f%%), %d features",
            len(loan_df),
            loan_df["is_default"].sum(),
            loan_df["is_default"].mean() * 100,
            len(loan_df.columns),
        )
        return loan_df

    # ── WoE / IV ────────────────────────────────────────────────────────────

    def compute_iv_table(
        self,
        df: pd.DataFrame,
        candidate_features: List[str],
        target: str = "is_default",
    ) -> pd.DataFrame:
        """Compute WoE and IV for each candidate feature using OptimalBinning.

        Returns a DataFrame sorted by IV descending with columns:
          feature, iv, predictive_power, n_bins, woe_range
        """
        try:
            from optbinning import OptimalBinning
        except ImportError as exc:
            raise ImportError("pip install optbinning") from exc

        records = []
        self.binning_map = {}

        for feat in candidate_features:
            if feat not in df.columns:
                continue
            series = df[feat]
            y = df[target]

            # Drop rows where feature is null
            mask = series.notna()
            x_clean = series[mask].values
            y_clean = y[mask].values

            if len(np.unique(x_clean)) < 2:
                continue

            dtype = "categorical" if series.dtype == object else "numerical"

            try:
                ob = OptimalBinning(
                    name=feat,
                    dtype=dtype,
                    solver="cp",
                    max_n_bins=8,
                    min_bin_size=0.03,  # at least 3% of population per bin
                )
                ob.fit(x_clean, y_clean)
                bt = ob.binning_table.build()

                # IV is the sum of all bin IVs (last row is "Totals")
                iv_val = float(bt.loc[bt.index[:-1], "IV"].sum())

                # WoE range for interpretability
                woe_vals = bt.loc[bt.index[:-1], "WoE"].dropna()
                woe_range = round(float(woe_vals.max() - woe_vals.min()), 4) if len(woe_vals) > 0 else 0.0

                n_bins = len(bt) - 1  # exclude Totals row

                self.binning_map[feat] = ob

                if iv_val < IV_USELESS:
                    power = "Useless"
                elif iv_val < IV_WEAK:
                    power = "Weak"
                elif iv_val < IV_MEDIUM:
                    power = "Medium"
                else:
                    power = "Strong"

                records.append({
                    "feature": feat,
                    "iv": round(iv_val, 4),
                    "predictive_power": power,
                    "n_bins": n_bins,
                    "woe_range": woe_range,
                    "dtype": dtype,
                })

            except Exception as e:
                logger.warning("Binning failed for %s: %s", feat, e)
                continue

        iv_df = pd.DataFrame(records).sort_values("iv", ascending=False).reset_index(drop=True)
        self.iv_table = iv_df
        return iv_df

    def _transform_woe(
        self,
        df: pd.DataFrame,
        features: List[str],
    ) -> pd.DataFrame:
        """Transform features to WoE values using fitted OptimalBinning objects."""
        woe_df = pd.DataFrame(index=df.index)
        for feat in features:
            if feat not in self.binning_map:
                continue
            ob = self.binning_map[feat]
            series = df[feat]
            mask = series.notna()
            woe_col = np.zeros(len(df))

            if mask.sum() > 0:
                try:
                    woe_vals = ob.transform(series[mask].values, metric="woe")
                    woe_col[mask.values] = woe_vals
                except Exception:
                    pass

            woe_df[f"{feat}_woe"] = woe_col

        return woe_df

    # ── Score scaling ────────────────────────────────────────────────────────

    @staticmethod
    def _scale_score(log_odds: np.ndarray) -> np.ndarray:
        """Map log-odds to 300–850 scale.

        Convention: higher score = lower risk (standard credit bureau direction).
        Higher log-odds means higher PD, so we SUBTRACT to invert direction.

        factor = PDO / ln(2)
        offset = BASE_SCORE + factor * ln(BASE_ODDS)
        score  = offset - factor * log_odds
        """
        factor = PDO / np.log(2)
        offset = BASE_SCORE + factor * np.log(BASE_ODDS)
        scores = offset - factor * log_odds
        return np.clip(scores, 300, 850).astype(int)

    # ── Fit ─────────────────────────────────────────────────────────────────

    def fit(
        self,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        customer_df: pd.DataFrame,
        iv_threshold: float = IV_USELESS,
        cv_folds: int = 5,
    ) -> Dict[str, Any]:
        """Full training pipeline: merge → feature engineering → IV → LR → scorecard.

        Returns dict with metrics and IV table.
        """
        logger.info("Building model dataset...")
        model_df = self.build_model_dataset(loan_df, payment_df, customer_df)

        target = "is_default"

        # ── Candidate features ────────────────────────────────────────────
        exclude = {
            target, "loan_id", "customer_id", "borrower_id", "id_prestamo",
            "status", "current_status", "estado", "_first_late_date",
            "vintage_quarter",  # kept for monitoring, not model input
        }
        candidates = [
            c for c in model_df.columns
            if c not in exclude and not c.startswith("_")
        ]

        logger.info("Computing IV for %d candidate features...", len(candidates))
        iv_table = self.compute_iv_table(model_df, candidates, target=target)

        # ── Feature selection by IV ───────────────────────────────────────
        selected = iv_table[iv_table["iv"] >= iv_threshold]["feature"].tolist()
        logger.info(
            "Features selected (IV >= %.3f): %d / %d",
            iv_threshold, len(selected), len(candidates),
        )
        if len(selected) == 0:
            raise ValueError(
                f"No features with IV >= {iv_threshold}. "
                "Check data quality or lower the threshold."
            )

        self.selected_features = selected

        # ── WoE transformation ────────────────────────────────────────────
        logger.info("Transforming features to WoE space...")
        woe_df = self._transform_woe(model_df, selected)
        self.feature_names_woe = list(woe_df.columns)

        y = model_df[target].values
        X_woe = woe_df.values

        # ── Logistic Regression ───────────────────────────────────────────
        logger.info("Training Logistic Regression on WoE features...")
        self.lr_model = LogisticRegression(
            C=0.1,          # regularisation — conservative for small default count
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",
            random_state=42,
        )
        self.lr_model.fit(X_woe, y)

        # ── Cross-validation ──────────────────────────────────────────────
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_aucs = cross_val_score(
            self.lr_model, X_woe, y,
            cv=skf, scoring="roc_auc",
        )

        # ── Holdout metrics ───────────────────────────────────────────────
        y_proba = self.lr_model.predict_proba(X_woe)[:, 1]
        auc = roc_auc_score(y, y_proba)
        gini = 2 * auc - 1

        from scipy.stats import ks_2samp
        ks_stat, _ = ks_2samp(y_proba[y == 1], y_proba[y == 0])

        # ── Score scaling ─────────────────────────────────────────────────
        log_odds = np.log(y_proba / (1 - y_proba + 1e-9))
        scores = self._scale_score(log_odds)
        model_df["predicted_score"] = scores
        model_df["predicted_pd"] = y_proba

        # Score distribution by default status
        score_stats = {
            "defaults_mean_score": int(model_df[model_df[target] == 1]["predicted_score"].mean()),
            "non_defaults_mean_score": int(model_df[model_df[target] == 0]["predicted_score"].mean()),
            "score_p25": int(np.percentile(scores, 25)),
            "score_p50": int(np.percentile(scores, 50)),
            "score_p75": int(np.percentile(scores, 75)),
        }

        # ── Scorecard table ───────────────────────────────────────────────
        self.scorecard_table = self._build_scorecard_table()

        metrics = {
            "auc_roc": round(auc, 4),
            "gini_coefficient": round(gini, 4),
            "ks_statistic": round(ks_stat, 4),
            "cv_auc_mean": round(float(cv_aucs.mean()), 4),
            "cv_auc_std": round(float(cv_aucs.std()), 4),
            "n_features_selected": len(selected),
            "n_samples": len(y),
            "n_defaults": int(y.sum()),
            "default_rate": round(float(y.mean()) * 100, 2),
            "score_distribution": score_stats,
        }

        self.metadata = {
            "model_type": "WoE_LogisticRegression",
            "features": selected,
            "iv_threshold": iv_threshold,
            "regularisation_C": 0.1,
            "score_scale": {"base": BASE_SCORE, "pdo": PDO, "base_odds": BASE_ODDS},
            "metrics": metrics,
        }

        logger.info(
            "Scorecard trained: AUC=%.4f, KS=%.4f, Gini=%.4f, CV AUC=%.4f±%.4f",
            auc, ks_stat, gini, cv_aucs.mean(), cv_aucs.std(),
        )
        return metrics

    def _build_scorecard_table(self) -> pd.DataFrame:
        """Build human-readable scorecard: feature | bin | woe | points."""
        if self.lr_model is None:
            return pd.DataFrame()

        rows = []
        factor = PDO / np.log(2)
        n_features = len(self.selected_features)
        intercept_per_feature = self.lr_model.intercept_[0] / n_features if n_features > 0 else 0

        for i, feat in enumerate(self.selected_features):
            if feat not in self.binning_map:
                continue
            ob = self.binning_map[feat]
            coef = self.lr_model.coef_[0][i]
            bt = ob.binning_table.build()

            for _, row in bt.iloc[:-1].iterrows():  # exclude Totals row
                woe_val = row.get("WoE", 0.0)
                if pd.isna(woe_val):
                    continue
                # Points = -(coef * WoE + intercept/n_features) * factor
                points = -(coef * woe_val + intercept_per_feature) * factor
                rows.append({
                    "feature": feat,
                    "bin": str(row.get("Bin", "")),
                    "count": int(row.get("Count", 0)),
                    "event_rate": round(float(row.get("Event rate", 0)) * 100, 2),
                    "woe": round(float(woe_val), 4),
                    "iv_bin": round(float(row.get("IV", 0)), 4),
                    "points": round(float(points), 1),
                })

        return pd.DataFrame(rows)

    # ── Inference ────────────────────────────────────────────────────────────

    def predict_proba(self, loan_data: Dict[str, Any]) -> float:
        """Return probability of default for a single loan."""
        if self.lr_model is None:
            raise RuntimeError("Model not trained or loaded")

        row = pd.DataFrame([loan_data])
        woe_df = self._transform_woe(row, self.selected_features)
        # Ensure column order matches training
        for col in self.feature_names_woe:
            if col not in woe_df.columns:
                woe_df[col] = 0.0
        woe_df = woe_df[self.feature_names_woe]
        return float(self.lr_model.predict_proba(woe_df.values)[:, 1][0])

    def predict_score(self, loan_data: Dict[str, Any]) -> int:
        """Return 300–850 credit score (higher = lower risk)."""
        pd_prob = self.predict_proba(loan_data)
        pd_prob = max(1e-6, min(1 - 1e-6, pd_prob))
        log_odds = np.log(pd_prob / (1 - pd_prob))
        return int(self._scale_score(np.array([log_odds]))[0])

    # ── Persistence ──────────────────────────────────────────────────────────

    def save(self, model_dir: str = "models/scorecard") -> str:
        """Persist model, binning objects, scorecard table, and metadata."""
        import pickle

        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)

        # LR model
        with open(path / "lr_model.pkl", "wb") as f:
            pickle.dump(self.lr_model, f)

        # Binning map (OptimalBinning objects)
        with open(path / "binning_map.pkl", "wb") as f:
            pickle.dump(self.binning_map, f)

        # IV table
        self.iv_table.to_csv(path / "iv_table.csv", index=False)

        # Scorecard table
        self.scorecard_table.to_csv(path / "scorecard_table.csv", index=False)

        # Metadata
        with open(path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2, default=str)

        logger.info("Scorecard saved to %s", path)
        return str(path)

    @classmethod
    def load(cls, model_dir: str = "models/scorecard") -> "ScorecardModel":
        """Load a saved scorecard model."""
        import pickle

        path = Path(model_dir)
        if not path.exists():
            raise FileNotFoundError(f"Model directory not found: {path}")

        instance = cls()

        with open(path / "lr_model.pkl", "rb") as f:
            instance.lr_model = pickle.load(f)

        with open(path / "binning_map.pkl", "rb") as f:
            instance.binning_map = pickle.load(f)

        instance.iv_table = pd.read_csv(path / "iv_table.csv")
        instance.scorecard_table = pd.read_csv(path / "scorecard_table.csv")

        with open(path / "metadata.json") as f:
            instance.metadata = json.load(f)

        instance.selected_features = instance.metadata.get("features", [])
        instance.feature_names_woe = [f"{f}_woe" for f in instance.selected_features]

        logger.info("Scorecard loaded from %s", path)
        return instance
