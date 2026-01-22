#!/usr/bin/env python3
import re
from pathlib import Path

import pandas as pd

# === CONFIG ===
DATA_ROOT = Path("data")  # change if your files live elsewhere
OUTPUT_SQL = Path("generated_tables.sql")
DEFAULT_SCHEMA = "public"  # or "analytics" if you prefer


def normalize_name(name: str) -> str:
    """Normalize column/table names for Postgres."""
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.lower().strip("_")


def infer_pg_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "NUMERIC"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TIMESTAMP"
    return "TEXT"


def generate_create_table_sql(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, nrows=200)
    elif suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(path, nrows=200)
    else:
        return ""
    table_name = normalize_name(path.stem)
    full_table_name = f"{DEFAULT_SCHEMA}.{table_name}"
    cols_sql = []
    for col in df.columns:
        col_name = normalize_name(str(col))
        if not col_name:
            continue
        pg_type = infer_pg_type(df[col])
        cols_sql.append(f'    "{col_name}" {pg_type}')
    if not cols_sql:
        return ""
    cols_block = ",\n".join(cols_sql)
    ddl = f"""CREATE TABLE IF NOT EXISTS {full_table_name} (
{cols_block}
);

"""
    return ddl


def main():
    sql_fragments = []
    for path in DATA_ROOT.rglob("*"):
        if path.suffix.lower() not in {".csv", ".xls", ".xlsx"}:
            continue
        ddl = generate_create_table_sql(path)
        if ddl:
            print(f"Generated DDL for: {path}")
            sql_fragments.append(f"-- Source file: {path}\n{ddl}")
    if not sql_fragments:
        print("No CSV/XLS/XLSX files found in", DATA_ROOT)
        return
    OUTPUT_SQL.write_text("\n".join(sql_fragments), encoding="utf-8")
    print(f"\nSaved all CREATE TABLE statements to {OUTPUT_SQL}")


if __name__ == "__main__":
    main()
