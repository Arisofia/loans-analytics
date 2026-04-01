#!/usr/bin/env python3
"""Idempotent migration runner with SHA-256 checksum verification.

Usage:
    python scripts/maintenance/run_migrations.py [--db-url URL] [--dry-run]

Environment:
    DATABASE_URL — Postgres connection string (overridden by --db-url)

The runner maintains a ``migration_ledger`` table in the ``public`` schema that
records the filename, SHA-256 digest, and timestamp of every applied migration.
On each run it:
  1. Skips migrations that are already in the ledger *with the same checksum*.
  2. Aborts if a previously-applied migration file has been modified (checksum
     mismatch) — this protects against silent history rewrites.
  3. Applies pending migrations in the order defined by migration_index.yml.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path

import yaml

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT / "db" / "migrations"
INDEX_FILE = MIGRATIONS_DIR / "migration_index.yml"

_CREATE_LEDGER_SQL = """
CREATE TABLE IF NOT EXISTS public.migration_ledger (
    id          SERIAL PRIMARY KEY,
    filename    TEXT    NOT NULL UNIQUE,
    sha256      TEXT    NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def _load_ordered_migrations() -> list[str]:
    if not INDEX_FILE.exists():
        logger.error("migration_index.yml not found: %s", INDEX_FILE)
        sys.exit(1)
    data = yaml.safe_load(INDEX_FILE.read_text(encoding="utf-8"))
    migrations = data.get("ordered_migrations") if isinstance(data, dict) else None
    if not isinstance(migrations, list):
        logger.error("migration_index.yml must contain ordered_migrations as a list")
        sys.exit(1)
    return migrations


def _get_ledger(cur) -> dict[str, str]:
    """Return {filename: sha256} for all already-applied migrations."""
    cur.execute(
        "SELECT filename, sha256 FROM public.migration_ledger ORDER BY applied_at"
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def _record_migration(cur, filename: str, digest: str) -> None:
    cur.execute(
        "INSERT INTO public.migration_ledger (filename, sha256) VALUES (%s, %s)",
        (filename, digest),
    )


def run(db_url: str, dry_run: bool) -> int:
    """Apply pending migrations. Returns exit code (0 = success)."""
    try:
        import psycopg2  # type: ignore
    except ImportError:
        logger.error("psycopg2 is not installed. Run: pip install psycopg2-binary")
        return 1

    ordered = _load_ordered_migrations()

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    applied = 0
    skipped = 0
    errors = 0

    try:
        with conn.cursor() as cur:
            # Ensure ledger table exists (idempotent DDL)
            cur.execute(_CREATE_LEDGER_SQL)
            conn.commit()

            ledger = _get_ledger(cur)

        for filename in ordered:
            sql_path = MIGRATIONS_DIR / filename
            if not sql_path.exists():
                logger.error("Migration file not found: %s", sql_path)
                errors += 1
                continue

            digest = _sha256(sql_path)

            if filename in ledger:
                recorded_digest = ledger[filename]
                if recorded_digest != digest:
                    logger.error(
                        "CHECKSUM MISMATCH: %s was already applied with digest %s "
                        "but file now has digest %s — aborting.",
                        filename,
                        recorded_digest,
                        digest,
                    )
                    return 1
                logger.info("  [skip] %s (already applied)", filename)
                skipped += 1
                continue

            sql = sql_path.read_text(encoding="utf-8")
            logger.info("  [apply] %s  sha256=%s", filename, digest[:12])

            if dry_run:
                logger.info("    [DRY-RUN] would execute %d bytes of SQL", len(sql))
                applied += 1
                continue

            with conn.cursor() as cur:
                try:
                    cur.execute(sql)
                    _record_migration(cur, filename, digest)
                    conn.commit()
                    logger.info("    [OK] %s committed", filename)
                    applied += 1
                except Exception as exc:  # noqa: BLE001
                    conn.rollback()
                    logger.error("    [FAIL] %s: %s", filename, exc)
                    errors += 1
                    # Continue to report remaining files; caller decides on exit code
    finally:
        conn.close()

    label = "[DRY-RUN] " if dry_run else ""
    logger.info(
        "%sMigration run complete: %d applied, %d skipped, %d errors",
        label,
        applied,
        skipped,
        errors,
    )
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL"),
        help="Postgres connection string (default: $DATABASE_URL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print which migrations would be applied without executing them",
    )
    args = parser.parse_args()

    if not args.db_url:
        logger.error(
            "No database URL provided. Set DATABASE_URL or pass --db-url."
        )
        sys.exit(1)

    sys.exit(run(args.db_url, args.dry_run))


if __name__ == "__main__":
    main()
