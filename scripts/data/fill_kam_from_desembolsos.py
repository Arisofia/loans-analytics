#!/usr/bin/env python3
"""Fill missing KAM values in manual overrides using DESEMBOLSOS (CJ/CL fallback)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from backend.src.infrastructure.google_sheets_adapter import ControlMoraSheetsAdapter


def _first_non_empty(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    result = pd.Series(index=df.index, dtype="object")
    for col in candidates:
        if col not in df.columns:
            continue
        candidate = df[col].astype(str).str.strip()
        candidate = candidate.mask(candidate.str.lower().isin({"", "nan", "none", "null"}))
        result = result.fillna(candidate)
    return result


def _build_kam_map(desembolsos_df: pd.DataFrame) -> pd.Series:
    kam_hunter = _first_non_empty(desembolsos_df, ["Cod_Kam_hunter", "CJ"])
    kam_farmer = _first_non_empty(desembolsos_df, ["Cod_Kam_farmer", "CL"])
    kam = kam_hunter.fillna(kam_farmer)
    client_id = _first_non_empty(desembolsos_df, ["CodCliente"]).astype(str).str.strip()
    mapped = pd.Series(kam.values, index=client_id).dropna()
    mapped = mapped[~mapped.index.str.lower().isin({"", "nan", "none", "null"})]
    return mapped


def run(args: argparse.Namespace) -> None:
    overrides_path = Path(args.overrides_csv)
    if not overrides_path.exists():
        raise FileNotFoundError(f"Overrides file not found: {overrides_path}")

    overrides_df = pd.read_csv(overrides_path, dtype=str)
    if "cod_cliente" not in overrides_df.columns:
        raise ValueError("Overrides CSV must include 'cod_cliente' column")
    if "kam" not in overrides_df.columns:
        overrides_df["kam"] = ""

    creds = args.credentials_path or os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    spreadsheet_id = args.spreadsheet_id or os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not creds or not spreadsheet_id:
        raise ValueError(
            "Google Sheets credentials missing. Set --credentials-path/--spreadsheet-id "
            "or GOOGLE_SHEETS_CREDENTIALS_PATH/GOOGLE_SHEETS_SPREADSHEET_ID."
        )

    adapter = ControlMoraSheetsAdapter(credentials_path=creds, spreadsheet_id=spreadsheet_id)
    desembolsos_df = pd.DataFrame(adapter.fetch_desembolsos_raw())
    kam_map = _build_kam_map(desembolsos_df)

    before_missing = overrides_df["kam"].fillna("").astype(str).str.strip().eq("").sum()

    empty_mask = overrides_df["kam"].fillna("").astype(str).str.strip().eq("")
    client_ids = overrides_df["cod_cliente"].astype(str).str.strip()
    overrides_df.loc[empty_mask, "kam"] = client_ids[empty_mask].map(kam_map).fillna("")

    after_missing = overrides_df["kam"].fillna("").astype(str).str.strip().eq("").sum()
    filled = int(before_missing - after_missing)

    overrides_df.to_csv(overrides_path, index=False)

    print(
        f"KAM backfill complete. Filled={filled}, still_missing={int(after_missing)}, total={len(overrides_df)}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fill missing KAM in manual overrides from DESEMBOLSOS Cod_Kam_farmer (CL)"
    )
    parser.add_argument(
        "--overrides-csv",
        default="data/raw/client_manual_overrides.csv",
        help="Path to manual overrides CSV with cod_cliente and kam columns",
    )
    parser.add_argument(
        "--credentials-path",
        default=None,
        help="Path to Google service account JSON (optional if env var is set)",
    )
    parser.add_argument(
        "--spreadsheet-id",
        default=None,
        help="Google Spreadsheet ID (optional if env var is set)",
    )
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
