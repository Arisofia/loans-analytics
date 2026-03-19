"""Profile imported loan tape CSVs and generate mapping/consistency report."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.src.zero_cost.loan_tape_loader import (
    LoanTapeLoader,
    _COLLATERAL_ALIASES,
    _CUSTOMER_ALIASES,
    _LOAN_ALIASES,
    _REAL_PAYMENT_ALIASES,
    _SCHEDULE_ALIASES,
    _slugify,
)


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig", low_memory=False)


def _mapping_rows(df: pd.DataFrame, alias_map: dict[str, str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for col in df.columns:
        canonical = alias_map.get(_slugify(col))
        if canonical:
            rows.append((col, canonical))
    return rows


def _loan_set(df: pd.DataFrame, col: str = "loan_id") -> set[str]:
    if col not in df.columns:
        return set()
    values = df[col].dropna().astype(str).str.strip()
    return {v for v in values if v}


def _write_mapping_section(lines: list[str], title: str, mappings: list[tuple[str, str]]) -> None:
    lines.append(f"## {title}")
    if not mappings:
        lines.append("No se detectaron mapeos automáticos para este dataset.")
        lines.append("")
        return

    lines.append("| Raw Column | Canonical Column |")
    lines.append("|---|---|")
    for raw, canonical in mappings:
        lines.append(f"| {raw} | {canonical} |")
    lines.append("")


def main() -> None:
    data_dir = Path("data/abaco")
    out_path = Path("docs/analytics/loan_tape_import_report_2026-03-19.md")

    raw_files = {
        "loan_data": data_dir / "loan_data.csv",
        "payment_schedule": data_dir / "payment_schedule.csv",
        "real_payment": data_dir / "real_payment.csv",
        "customer_data": data_dir / "customer_data.csv",
        "collateral": data_dir / "collateral.csv",
    }

    for key, file_path in raw_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required file for report: {key} -> {file_path}")

    raw_frames = {key: _load_csv(path) for key, path in raw_files.items()}

    loader = LoanTapeLoader(data_dir=data_dir)
    canonical = loader.load_all(data_dir)

    dim_loan = canonical["dim_loan"]
    fact_schedule = canonical["fact_schedule"]
    fact_real_payment = canonical["fact_real_payment"]
    dim_customer = canonical.get("dim_customer", pd.DataFrame())
    dim_collateral = canonical.get("dim_collateral", pd.DataFrame())

    loan_ids = _loan_set(dim_loan)
    sched_ids = _loan_set(fact_schedule)
    real_ids = _loan_set(fact_real_payment)
    coll_ids = _loan_set(dim_collateral)

    lines: list[str] = []
    lines.append("# Loan Tape Import Report (2026-03-19)")
    lines.append("")
    lines.append(f"Generated at: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    lines.append("## Raw Dataset Profile")
    lines.append("| Dataset | Rows | Columns |")
    lines.append("|---|---:|---:|")
    for name, df in raw_frames.items():
        lines.append(f"| {name} | {len(df)} | {len(df.columns)} |")
    lines.append("")

    lines.append("## Canonical Output Profile (LoanTapeLoader)")
    lines.append("| Table | Rows | Columns |")
    lines.append("|---|---:|---:|")
    lines.append(f"| dim_loan | {len(dim_loan)} | {len(dim_loan.columns)} |")
    lines.append(f"| fact_schedule | {len(fact_schedule)} | {len(fact_schedule.columns)} |")
    lines.append(f"| fact_real_payment | {len(fact_real_payment)} | {len(fact_real_payment.columns)} |")
    lines.append(f"| dim_customer | {len(dim_customer)} | {len(dim_customer.columns)} |")
    lines.append(f"| dim_collateral | {len(dim_collateral)} | {len(dim_collateral.columns)} |")
    lines.append("")

    lines.append("## Loan ID Cross-Validation")
    lines.append(f"- loan_ids in dim_loan: {len(loan_ids)}")
    lines.append(f"- loan_ids in fact_schedule: {len(sched_ids)}")
    lines.append(f"- loan_ids in fact_real_payment: {len(real_ids)}")
    lines.append(f"- loan_ids in dim_collateral: {len(coll_ids)}")
    lines.append(f"- schedule not in dim_loan: {len(sched_ids - loan_ids)}")
    lines.append(f"- real_payment not in dim_loan: {len(real_ids - loan_ids)}")
    lines.append(f"- collateral not in dim_loan: {len(coll_ids - loan_ids)}")
    lines.append(f"- dim_loan not in schedule: {len(loan_ids - sched_ids)}")
    lines.append(f"- dim_loan not in real_payment: {len(loan_ids - real_ids)}")
    lines.append("")

    _write_mapping_section(
        lines,
        "Mapping - loan_data.csv",
        _mapping_rows(raw_frames["loan_data"], _LOAN_ALIASES),
    )
    _write_mapping_section(
        lines,
        "Mapping - payment_schedule.csv",
        _mapping_rows(raw_frames["payment_schedule"], _SCHEDULE_ALIASES),
    )
    _write_mapping_section(
        lines,
        "Mapping - real_payment.csv",
        _mapping_rows(raw_frames["real_payment"], _REAL_PAYMENT_ALIASES),
    )
    _write_mapping_section(
        lines,
        "Mapping - customer_data.csv",
        _mapping_rows(raw_frames["customer_data"], _CUSTOMER_ALIASES),
    )
    _write_mapping_section(
        lines,
        "Mapping - collateral.csv",
        _mapping_rows(raw_frames["collateral"], _COLLATERAL_ALIASES),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Report written: {out_path}")


if __name__ == "__main__":
    main()
