from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

BLANK_TOKENS = {"", "nan", "none", "null", "missing", "n/a"}
KPI_RELEVANT_NUMERIC_COLUMNS = (
    "outstanding_balance",
    "current_balance",
    "disbursement_amount",
    "funded_amount",
    "amount",
    "dpd",
    "days_past_due",
)


def _read_tabular(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def _to_numeric_series(df: pd.DataFrame, candidates: tuple[str, ...]) -> pd.Series:
    col = next((name for name in candidates if name in df.columns), None)
    if col is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def _normalize_status(df: pd.DataFrame) -> pd.Series:
    if "status" not in df.columns:
        return pd.Series(["active"] * len(df), index=df.index, dtype="string")
    return df["status"].astype("string").str.strip().str.lower()


def _blank_counts(df: pd.DataFrame) -> dict[str, int]:
    blank_summary: dict[str, int] = {}
    for column in df.columns:
        normalized = df[column].astype("string").str.strip().str.lower()
        blank_summary[column] = int((normalized.isna() | normalized.isin(BLANK_TOKENS)).sum())
    return blank_summary


def _negative_counts(df: pd.DataFrame) -> dict[str, int]:
    result: dict[str, int] = {}
    for column in KPI_RELEVANT_NUMERIC_COLUMNS:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        result[column] = int((series < 0).sum())
    return result


def _calculate_core_kpis(df: pd.DataFrame) -> dict[str, float | None]:
    balance = _to_numeric_series(df, ("outstanding_balance", "current_balance", "amount", "funded_amount")).fillna(0.0)
    dpd = _to_numeric_series(df, ("dpd", "days_past_due")).fillna(0.0)
    status = _normalize_status(df)

    total_balance = float(balance.sum())
    if total_balance <= 0:
        return {
            "par_30": None,
            "par_60": None,
            "par_90": None,
            "npl_ratio": None,
            "default_rate": None,
        }

    delinquent_mask = (dpd >= 30) | status.isin(["delinquent", "defaulted"])
    par30 = float(balance[delinquent_mask].sum() / total_balance * 100)
    par60 = float(balance[dpd >= 60].sum() / total_balance * 100)
    par90 = float(balance[dpd >= 90].sum() / total_balance * 100)
    default_rate = float((status == "defaulted").mean() * 100)

    return {
        "par_30": round(par30, 4),
        "par_60": round(par60, 4),
        "par_90": round(par90, 4),
        "npl_ratio": round(par30, 4),
        "default_rate": round(default_rate, 4),
    }


def build_validation_report(df: pd.DataFrame, source_path: Path) -> dict[str, Any]:
    blanks = _blank_counts(df)
    negatives = _negative_counts(df)
    kpis = _calculate_core_kpis(df)
    return {
        "source": str(source_path),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "blank_counts": blanks,
        "negative_counts": negatives,
        "core_kpis_from_real_file": kpis,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate blank/negative values and compute KPI baselines from real files"
    )
    parser.add_argument("--input", type=Path, required=True, help="Path to CSV/Parquet real data file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    df = _read_tabular(args.input)
    report = build_validation_report(df=df, source_path=args.input)

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output is None:
        print(payload)
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
    print(f"Validation report written to {args.output}")


if __name__ == "__main__":
    main()
