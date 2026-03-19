#!/usr/bin/env python3
"""
Initialise the DuckDB star schema.

Usage: python scripts/data/init_duckdb_schema.py [--db PATH]
"""

from __future__ import annotations

import argparse
import pathlib
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise DuckDB star schema")
    parser.add_argument(
        "--db",
        default="data/duckdb/analytics.duckdb",
        help="Path to DuckDB database file (default: data/duckdb/analytics.duckdb)",
    )
    args = parser.parse_args()

    try:
        import duckdb
    except ImportError:
        print("ERROR: duckdb is not installed. Run: pip install duckdb", file=sys.stderr)
        sys.exit(1)

    db_path = pathlib.Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    ddl_path = pathlib.Path("db/star_schema/duckdb/create_star_schema_duckdb.sql")
    if not ddl_path.exists():
        print(f"ERROR: DDL file not found: {ddl_path}", file=sys.stderr)
        sys.exit(1)

    con = duckdb.connect(str(db_path))
    try:
        con.execute(ddl_path.read_text())
        print(f"✅  DuckDB star schema initialised → {db_path}")
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        print("   Tables created:", [t[0] for t in tables])
    finally:
        con.close()


if __name__ == "__main__":
    main()
