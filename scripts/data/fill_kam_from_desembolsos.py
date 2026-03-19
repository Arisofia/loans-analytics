#!/usr/bin/env python3
"""Fill missing KAM values in manual overrides using DESEMBOLSOS (CJ/CL fallback)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import unicodedata

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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


def _normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_kam_maps(desembolsos_df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    kam_hunter = _first_non_empty(desembolsos_df, ["Cod_Kam_hunter", "Cod_Kam_hunter_", "CJ"])
    kam_farmer = _first_non_empty(
        desembolsos_df,
        ["Cod_Kam_farmer", "Cod_Kam_farmer_", "CL"],
    )
    kam = kam_hunter.fillna(kam_farmer)

    # Prefer numeric customer code when available; fallback to CJ/Cliente_ textual key.
    client_id = _first_non_empty(
        desembolsos_df,
        ["CodCliente", "CodCliente_"],
    ).astype(str).str.strip()
    client_name = _first_non_empty(
        desembolsos_df,
        ["Cliente_", "Cliente", "CJ"],
    ).astype(str).str.strip()

    mapped = pd.DataFrame({"cod_cliente": client_id, "client_name": client_name, "kam": kam})
    mapped["cod_cliente"] = mapped["cod_cliente"].astype(str).str.strip()
    mapped["client_name"] = mapped["client_name"].astype(str).str.strip()
    mapped["client_name_norm"] = mapped["client_name"].map(_normalize_name)
    mapped["kam"] = mapped["kam"].astype(str).str.strip()
    mapped = mapped[~mapped["kam"].str.lower().isin({"", "nan", "none", "null"})]

    map_by_code_df = mapped[
        ~mapped["cod_cliente"].str.lower().isin({"", "nan", "none", "null"})
    ].drop_duplicates(subset=["cod_cliente"], keep="first")
    map_by_name_df = mapped[
        ~mapped["client_name_norm"].str.lower().isin({"", "nan", "none", "null"})
    ].drop_duplicates(subset=["client_name_norm"], keep="first")

    map_by_code = pd.Series(map_by_code_df["kam"].values, index=map_by_code_df["cod_cliente"])
    map_by_name = pd.Series(
        map_by_name_df["kam"].values,
        index=map_by_name_df["client_name_norm"],
    )
    return map_by_code, map_by_name


def _build_overrides_from_intermedia(intermedia_df: pd.DataFrame) -> pd.DataFrame:
    cod_cliente = _first_non_empty(intermedia_df, ["CodCliente", "cod_cliente"]).astype(str).str.strip()
    cliente = _first_non_empty(intermedia_df, ["Cliente", "cliente", "client_name"]).astype(str).str.strip()
    base = pd.DataFrame({"cod_cliente": cod_cliente, "cliente": cliente})
    base = base[
        ~base["cod_cliente"].str.lower().isin({"", "nan", "none", "null"})
    ].drop_duplicates(subset=["cod_cliente"], keep="first")
    base["industry"] = ""
    base["kam"] = ""
    base["lt_customer_id"] = ""
    base = base.sort_values("cod_cliente").reset_index(drop=True)
    return base


def run(args: argparse.Namespace) -> None:
    overrides_path = Path(args.overrides_csv)

    creds = args.credentials_path or os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    spreadsheet_id = args.spreadsheet_id or os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not creds or not spreadsheet_id:
        raise ValueError(
            "Google Sheets credentials missing. Set --credentials-path/--spreadsheet-id "
            "or GOOGLE_SHEETS_CREDENTIALS_PATH/GOOGLE_SHEETS_SPREADSHEET_ID."
        )

    adapter = ControlMoraSheetsAdapter(credentials_path=creds, spreadsheet_id=spreadsheet_id)
    desembolsos_df = pd.DataFrame(adapter.fetch_desembolsos_raw())
    kam_map_by_code, kam_map_by_name = _build_kam_maps(desembolsos_df)
    intermedia_df = pd.DataFrame(adapter.fetch_intermedia_raw())

    if overrides_path.exists():
        overrides_df = pd.read_csv(overrides_path, dtype=str)
        source = f"existing file ({overrides_path})"
    else:
        overrides_df = _build_overrides_from_intermedia(intermedia_df)
        source = "auto-generated from INTERMEDIA"

    if "cod_cliente" not in overrides_df.columns:
        raise ValueError("Overrides CSV must include 'cod_cliente' column")
    if "kam" not in overrides_df.columns:
        overrides_df["kam"] = ""
    if "industry" not in overrides_df.columns:
        overrides_df["industry"] = ""
    if "lt_customer_id" not in overrides_df.columns:
        overrides_df["lt_customer_id"] = ""
    if "cliente" not in overrides_df.columns:
        inter_cliente = _first_non_empty(intermedia_df, ["Cliente", "cliente", "client_name"]).astype(str).str.strip()
        inter_cod = _first_non_empty(intermedia_df, ["CodCliente", "cod_cliente"]).astype(str).str.strip()
        inter_map_df = pd.DataFrame({"cod_cliente": inter_cod, "cliente": inter_cliente})
        inter_map_df = inter_map_df[
            ~inter_map_df["cod_cliente"].str.lower().isin({"", "nan", "none", "null"})
        ].drop_duplicates(subset=["cod_cliente"], keep="first")
        inter_map = pd.Series(inter_map_df["cliente"].values, index=inter_map_df["cod_cliente"])
        overrides_df["cliente"] = overrides_df["cod_cliente"].astype(str).str.strip().map(inter_map).fillna("")

    before_missing = overrides_df["kam"].fillna("").astype(str).str.strip().eq("").sum()

    empty_mask = overrides_df["kam"].fillna("").astype(str).str.strip().eq("")
    client_ids = overrides_df["cod_cliente"].astype(str).str.strip()
    by_code_values = client_ids[empty_mask].map(kam_map_by_code).fillna("")

    cliente_norm = overrides_df["cliente"].fillna("").astype(str).map(_normalize_name)
    by_name_values = cliente_norm[empty_mask].map(kam_map_by_name).fillna("")

    overrides_df.loc[empty_mask, "kam"] = by_code_values.where(
        by_code_values.astype(str).str.strip().ne(""),
        by_name_values,
    )

    after_missing = overrides_df["kam"].fillna("").astype(str).str.strip().eq("").sum()
    filled = int(before_missing - after_missing)

    overrides_df.to_csv(overrides_path, index=False)

    print(
        f"KAM backfill complete from {source}. Filled={filled}, "
        f"still_missing={int(after_missing)}, total={len(overrides_df)}"
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
