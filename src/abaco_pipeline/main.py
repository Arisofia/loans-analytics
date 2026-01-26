"""Minimal CLI surface for the historical `abaco_pipeline` entrypoint used in tests.

This intentionally implements only the features exercised by unit tests: a
`write-audit` subcommand that can either print an enriched payload or send it
via the `SupabaseWriter`.
"""

from __future__ import annotations  # noqa: E402

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Dict, List, Optional  # noqa: E402

from src.abaco_pipeline.output.supabase_writer import SupabaseAuth, SupabaseWriter  # noqa: E402


def _enrich_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(payload)
    payload.setdefault("config_version", "v1")
    payload.setdefault("kpi_def_version", "v1")

    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"])
        payload["git_sha"] = sha.decode().strip()
    except Exception:
        payload["git_sha"] = "unknown"

    return payload


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="abaco_pipeline")

    # historically this CLI accepted a global --config before the subcommand
    p.add_argument("--config", required=True)

    sub = p.add_subparsers(dest="command")

    write = sub.add_parser("write-audit")
    write.add_argument("--kpis-config", required=True)
    write.add_argument("--payload", required=True)
    write.add_argument("--dry-run", action="store_true")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "write-audit":
        payload_path = Path(args.payload)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        enriched = _enrich_payload(payload)

        if args.dry_run:
            print(json.dumps(enriched))
            return 0

        # Send to Supabase using environment defaults
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE")
        if not url or not key:
            # fail gracefully
            return 1

        auth = SupabaseAuth(url=url, service_role_key=key)
        writer = SupabaseWriter(auth)
        # upsert run and insert KPI values if present
        run = enriched.get("run")
        if run:
            writer.upsert_pipeline_run(run)
        kpi_values = enriched.get("kpi_values", [])
        writer.insert_kpi_values(kpi_values)

        return 0

    # unknown command
    return 1
