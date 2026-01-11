"""CLI entrypoint for the Abaco canonical pipeline (v2 scaffold)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.compliance import (build_compliance_report, create_access_log_entry,
                            mask_pii_in_dataframe, write_compliance_report)

from .ingestion.archive import archive_file
from .logging import configure_logging
from .output.manifests import RunManifest, write_manifest
from .output.supabase_writer import SupabaseAuth, SupabaseWriter
from .quality.gates import (check_referential_integrity, compute_completeness,
                            compute_freshness_hours)


def _load_yaml_config(path: Path) -> dict:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "YAML config requested but PyYAML is not installed. Install pyyaml to use this command."
        ) from exc

    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Payload file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:  # pragma: no cover
        return "unknown"


def _kpi_def_version(kpis_path: Path) -> str:
    cfg = _load_yaml_config(kpis_path)
    return str(cfg.get("version") or "unknown")


def _enrich_audit_payload(
    payload: dict,
    *,
    config_version: str,
    git_sha: str,
    kpi_def_version: str,
) -> dict:
    run_payload = payload.get("run") or {}
    run_payload["config_version"] = config_version
    run_payload["git_sha"] = git_sha
    payload["run"] = run_payload

    kpis = payload.get("kpi_values") or []
    for entry in kpis:
        entry.setdefault("kpi_def_version", kpi_def_version)
    payload["kpi_values"] = kpis
    return payload


def _write_audit_payload(payload: dict, *, schema: str = "analytics") -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE are required to publish audit data"
        )

    writer = SupabaseWriter(SupabaseAuth(url=url, service_role_key=key), schema=schema)
    run = payload.get("run") or {}
    raw_artifacts = payload.get("raw_artifacts") or []
    kpis = payload.get("kpi_values") or []
    quality = payload.get("data_quality") or {}

    writer.upsert_pipeline_run(run)
    writer.insert_raw_artifacts(raw_artifacts)
    writer.insert_kpi_values(kpis)
    if quality:
        writer.upsert_data_quality(quality)


def cmd_print_config(args: argparse.Namespace) -> int:
    cfg = _load_yaml_config(Path(args.config))
    print(json.dumps(cfg, indent=2, sort_keys=True))
    return 0


def cmd_write_audit(args: argparse.Namespace) -> int:
    payload = _load_json(Path(args.payload))
    cfg = _load_yaml_config(Path(args.config))
    config_version = str(cfg.get("version") or "unknown")
    enriched = _enrich_audit_payload(
        payload,
        config_version=config_version,
        git_sha=_git_sha(),
        kpi_def_version=_kpi_def_version(Path(args.kpis_config)),
    )

    if args.dry_run:
        print(json.dumps(enriched, indent=2, sort_keys=True))
        return 0

    _write_audit_payload(enriched, schema=args.schema)
    return 0


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _select_looker_source(looker_cfg: dict, endpoints: list[str] | None) -> Path:
    loans_par = (
        Path(looker_cfg.get("loans_par_path", "")) if looker_cfg.get("loans_par_path") else None
    )
    loans_fallback = (
        Path(looker_cfg.get("loans_path", "")) if looker_cfg.get("loans_path") else None
    )

    if endpoints:
        if "loan_par_balances" in endpoints and loans_par and loans_par.exists():
            return loans_par
        if "loans" in endpoints and loans_fallback:
            return loans_fallback

    if loans_par and loans_par.exists():
        return loans_par
    if loans_fallback:
        return loans_fallback
    raise FileNotFoundError("Looker loans file path is not configured")


def _detect_looker_schema_drift(columns: set[str]) -> dict[str, list[str]]:
    par_required = {
        "reporting_date",
        "par_7_balance_usd",
        "par_30_balance_usd",
        "par_60_balance_usd",
        "par_90_balance_usd",
    }
    dpd_required = {"dpd", "outstanding_balance"}
    dpd_alt = {"dpd", "outstanding_balance_usd"}
    dpd_alt_two = {"days_past_due", "outstanding_balance"}

    if columns.issuperset(par_required):
        return {"missing": [], "unexpected": []}
    if (
        columns.issuperset(dpd_required)
        or columns.issuperset(dpd_alt)
        or columns.issuperset(dpd_alt_two)
    ):
        return {"missing": [], "unexpected": []}

    missing_sets = [
        sorted(list(par_required - columns)),
        sorted(list(dpd_required - columns)),
        sorted(list(dpd_alt - columns)),
        sorted(list(dpd_alt_two - columns)),
    ]
    return {
        "missing": sorted({item for subset in missing_sets for item in subset}),
        "unexpected": [],
    }


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _load_yaml_config(Path(args.config))
    config_version = str(cfg.get("version") or "unknown")
    git_sha = _git_sha()

    run_cfg = cfg.get("run", {}) or {}
    artifacts_dir = Path(run_cfg.get("artifacts_dir", "logs/runs"))
    raw_archive_dir = Path(run_cfg.get("raw_archive_dir", "data/archives/cascade"))
    state_file = Path(args.state_file or run_cfg.get("state_file", "logs/runs/state.json"))

    pipeline_cfg = (cfg.get("pipeline", {}) or {}).get("phases", {}) or {}
    ingestion_cfg = pipeline_cfg.get("ingestion", {}) or {}
    ingest_source = ingestion_cfg.get("source", "file")

    endpoints = [e.strip() for e in (args.endpoints or "").split(",") if e.strip()]
    loans_path = None
    financials_path = None

    if args.input:
        loans_path = Path(args.input)
    elif ingest_source == "looker":
        looker_cfg = ingestion_cfg.get("looker", {}) or {}
        loans_path = _select_looker_source(looker_cfg, endpoints or None)
        financials_value = looker_cfg.get("financials_path")
        if financials_value:
            financials_path = Path(str(financials_value))
    elif ingest_source == "file":
        file_cfg = ingestion_cfg.get("file", {}) or {}
        default_path = file_cfg.get("default_path")
        if default_path:
            loans_path = Path(default_path)
    else:
        raise ValueError(f"Unsupported ingestion source: {ingest_source}")

    if loans_path is None:
        raise FileNotFoundError("No input file configured for ingestion")
    if not loans_path.exists():
        raise FileNotFoundError(f"Input file not found: {loans_path}")

    started_at = datetime.now(timezone.utc)
    archive_result = archive_file(raw_archive_dir, loans_path)
    source_hash = archive_result.sha256

    run_id_strategy = run_cfg.get("id_strategy", "timestamp")
    if args.run_id:
        run_id = args.run_id
    elif run_id_strategy == "deterministic" and source_hash:
        run_id = f"run_{source_hash[:12]}"
    else:
        run_id = f"run_{started_at.strftime('%Y%m%d_%H%M%S')}"

    run_dir = artifacts_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    state = _load_state(state_file)
    state_key = f"{ingest_source}:{loans_path.name}"
    last_hash = (state.get("raw_hashes") or {}).get(state_key)
    if last_hash == source_hash and not args.force:
        summary = {
            "run_id": run_id,
            "status": "skipped",
            "reason": "idempotent",
            "config_version": config_version,
            "git_sha": git_sha,
            "input": {
                "path": str(loans_path),
                "sha256": source_hash,
                "archive_path": str(archive_result.path),
            },
            "started_at": started_at.isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }
        (run_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (artifacts_dir / "latest.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, sort_keys=True))
        return 0

    schema_diff = {}
    schema_drift = False
    if ingest_source == "looker":
        try:
            import pandas as pd

            header_cols = pd.read_csv(loans_path, nrows=0).columns
            schema_diff = _detect_looker_schema_drift({c.lower() for c in header_cols})
            schema_drift = bool(schema_diff.get("missing"))
        except Exception:
            schema_diff = {}
            schema_drift = False

    if schema_drift and args.validate:
        schema_payload = {
            "run_id": run_id,
            "status": "schema_drift",
            "diff": schema_diff,
        }
        (run_dir / "schema_diff.json").write_text(
            json.dumps(schema_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        summary = {
            "run_id": run_id,
            "status": "schema_drift",
            "failure_reason": "schema_drift",
            "config_version": config_version,
            "git_sha": git_sha,
            "input": {
                "path": str(loans_path),
                "sha256": source_hash,
                "archive_path": str(archive_result.path),
            },
            "schema_diff": schema_diff,
            "started_at": started_at.isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }
        (run_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (artifacts_dir / "latest.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, sort_keys=True))
        return 2

    try:
        from src.pipeline.data_ingestion import UnifiedIngestion

        ingestion = UnifiedIngestion(cfg)
        result = ingestion.ingest_looker(
            loans_path, financials_path=financials_path, archive_dir=None
        )
    except Exception as exc:
        summary = {
            "run_id": run_id,
            "status": "failed",
            "failure_reason": "ingestion_failed",
            "error": str(exc),
            "config_version": config_version,
            "git_sha": git_sha,
            "input": {
                "path": str(loans_path),
                "sha256": source_hash,
                "archive_path": str(archive_result.path),
            },
            "started_at": started_at.isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }
        (run_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (artifacts_dir / "latest.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, sort_keys=True))
        return 1

    df = result.df
    validation_cfg = ingestion_cfg.get("validation", {}) or {}
    required_columns = validation_cfg.get("required_columns") or []
    completeness_threshold = float(validation_cfg.get("completeness_threshold", 0.98))
    integrity_columns = validation_cfg.get("referential_integrity_columns") or ["loan_id"]

    completeness = compute_completeness(df, required_columns)
    freshness_hours = 0.0
    if "measurement_date" in df.columns:
        try:
            import pandas as pd

            as_of = pd.to_datetime(df["measurement_date"], errors="coerce").max()
            if pd.notna(as_of):
                freshness_hours = compute_freshness_hours(as_of.to_pydatetime())
        except Exception:
            freshness_hours = 0.0

    referential_integrity_pass = check_referential_integrity(df, integrity_columns)
    quality_pass = completeness >= completeness_threshold and referential_integrity_pass

    quality_payload = {
        "run_id": run_id,
        "completeness": round(completeness, 4),
        "freshness_hours": round(freshness_hours, 2),
        "referential_integrity_pass": referential_integrity_pass,
        "notes_json": {
            "source": ingest_source,
            "integrity_columns": integrity_columns,
            "completeness_threshold": completeness_threshold,
        },
    }
    (run_dir / "quality.json").write_text(
        json.dumps(quality_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    _, masked_columns = mask_pii_in_dataframe(
        df,
        keywords=(pipeline_cfg.get("transformation", {}) or {})
        .get("pii_masking", {})
        .get("keywords"),
    )
    access_log = [
        create_access_log_entry(
            stage="ingestion",
            user=args.user,
            action=args.action,
            status="success",
        )
    ]
    compliance_report = build_compliance_report(
        run_id=run_id,
        access_log=access_log,
        masked_columns=masked_columns,
        mask_stage="ingestion",
        metadata={
            "source": ingest_source,
            "source_path": str(loans_path),
            "archive_path": str(archive_result.path),
            "source_hash": source_hash,
        },
    )
    write_compliance_report(compliance_report, run_dir / "compliance.json")

    manifest = RunManifest(
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        inputs={"looker_loans": source_hash},
        outputs={},
    )
    write_manifest(run_dir / "manifest.json", manifest)

    status = "success"
    failure_reason = None
    exit_code = 0
    if args.validate and not quality_pass:
        status = "failed"
        failure_reason = "quality_gate_failed"
        exit_code = 3

    audit_payload = {
        "run": {
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
        },
        "raw_artifacts": [
            {
                "run_id": run_id,
                "endpoint": "looker.loans",
                "as_of": None,
                "sha256": source_hash,
                "storage_uri": str(archive_result.path),
            }
        ],
        "kpi_values": [],
        "data_quality": quality_payload,
    }

    enriched_audit = _enrich_audit_payload(
        audit_payload,
        config_version=config_version,
        git_sha=git_sha,
        kpi_def_version=_kpi_def_version(Path(args.kpis_config)),
    )

    if args.publish and status == "success":
        schema = (
            (pipeline_cfg.get("outputs", {}) or {}).get("supabase", {}).get("schema", "analytics")
        )
        _write_audit_payload(enriched_audit, schema=schema)
        state["raw_hashes"] = {**(state.get("raw_hashes") or {}), state_key: source_hash}
        state["last_run_id"] = run_id
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_state(state_file, state)

    summary = {
        "run_id": run_id,
        "status": status,
        "failure_reason": failure_reason,
        "config_version": config_version,
        "git_sha": git_sha,
        "input": {
            "path": str(loans_path),
            "sha256": source_hash,
            "archive_path": str(archive_result.path),
        },
        "quality": quality_payload,
        "compliance": {"masked_columns": masked_columns},
        "started_at": started_at.isoformat(),
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "endpoints": endpoints,
        "date_range": {"start": args.start_date, "end": args.end_date},
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (artifacts_dir / "latest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, sort_keys=True))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abaco-pipeline", description=__doc__)
    parser.add_argument(
        "--config",
        default="config/pipeline.yml",
        help="Path to pipeline config YAML (default: config/pipeline.yml)",
    )
    parser.add_argument(
        "--kpis-config",
        default="config/kpis.yml",
        help="Path to KPI config YAML (default: config/kpis.yml)",
    )
    parser.add_argument("--validate", action="store_true", help="Enable validation + quality gates")
    parser.add_argument("--publish", action="store_true", help="Publish audit payload to Supabase")
    parser.add_argument(
        "--force", action="store_true", help="Force publish even if input hash is unchanged"
    )
    parser.add_argument("--input", help="Override input path for ingestion")
    parser.add_argument("--state-file", help="Path to idempotency state file")
    parser.add_argument("--run-id", help="Override run_id")
    parser.add_argument("--endpoints", help="Comma-separated endpoint list")
    parser.add_argument("--start-date", help="Backfill start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Backfill end date (YYYY-MM-DD)")
    parser.add_argument("--user", default="pipeline", help="Actor for compliance audit log")
    parser.add_argument("--action", default="scheduled", help="Action for compliance audit log")

    sub = parser.add_subparsers(dest="command")

    p_cfg = sub.add_parser("print-config", help="Print parsed pipeline config")
    p_cfg.set_defaults(func=cmd_print_config)

    p_write = sub.add_parser("write-audit", help="Write audit payload to Supabase")
    p_write.add_argument(
        "--kpis-config",
        default="config/kpis.yml",
        help="Path to KPI config YAML (default: config/kpis.yml)",
    )
    p_write.add_argument("--payload", required=True, help="Path to audit payload JSON")
    p_write.add_argument(
        "--dry-run", action="store_true", help="Print enriched payload without writing"
    )
    p_write.add_argument(
        "--schema", default="analytics", help="Supabase schema (default: analytics)"
    )
    p_write.set_defaults(func=cmd_write_audit)

    p_run = sub.add_parser("run", help="Run pipeline ingestion/validation")
    p_run.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        return int(cmd_run(args))
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
