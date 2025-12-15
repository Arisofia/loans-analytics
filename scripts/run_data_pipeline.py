import argparse
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Add project root to path for python/ modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from python.compliance import (
    build_compliance_report,
    create_access_log_entry,
    mask_pii_in_dataframe,
    write_compliance_report,
)
from python.ingestion import CascadeIngestion
from python.kpi_engine import KPIEngine
from python.transformation import DataTransformation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_INPUT = os.getenv("PIPELINE_INPUT_FILE", "data/abaco_portfolio_calculations.csv")
METRICS_DIR = Path("data/metrics")
LOGS_DIR = Path("logs/runs")
METRICS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log_stage(stage: str, message: str, **details: Any) -> None:
    detail_str = ", ".join(f"{key}={value!r}" for key, value in details.items() if value is not None)
    payload = f"{stage}: {message}"
    if detail_str:
        payload = f"{payload} | {detail_str}"
    logger.info(payload)


def write_outputs(
    run_id: str,
    kpi_df: pd.DataFrame,
    audit: Dict[str, Any],
    metadata: Dict[str, Any],
    compliance_path: Path,
) -> Dict[str, Any]:
    metrics_path = METRICS_DIR / f"{run_id}.parquet"
    csv_path = METRICS_DIR / f"{run_id}.csv"
    audit_path = LOGS_DIR / f"{run_id}.json"
    manifest_path = LOGS_DIR / f"{run_id}_manifest.json"

    kpi_df.to_parquet(metrics_path, index=False)
    kpi_df.to_csv(csv_path, index=False)

    processed_outputs = {
        "metrics_file": str(metrics_path),
        "csv_file": str(csv_path),
        "manifest_file": str(manifest_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "compliance_report_file": str(compliance_path),
    }

    manifest = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_files": metadata.get("raw_files", []),
        "processed_outputs": processed_outputs,
        "processed_data": metadata.get("processed_data"),
        "lineage": metadata.get("lineage", []),
        "user": metadata.get("user"),
        "action": metadata.get("action"),
        "audit": metadata.get("audit", {}),
        "compliance_report_file": str(compliance_path),
    }

    with audit_path.open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, default=str)

    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, default=str)

    return processed_outputs


def run_pipeline(input_file: str = DEFAULT_INPUT, user: str | None = None, action: str | None = None) -> bool:
    user = user or os.getenv("PIPELINE_RUN_USER", "system")
    action = action or os.getenv("PIPELINE_RUN_ACTION", "manual")
    input_path = Path(input_file)
    data_dir = str(input_path.parent or ".")
    ingestion = CascadeIngestion(data_dir=data_dir)
    ingestion.set_context(user=user, action=action, input_file=str(input_path))
    transformer = DataTransformation()
    transformer.set_context(user=user, action=action, ingest_run_id=ingestion.run_id, source_file=str(input_path))

    log_stage(
        "pipeline:start",
        "Starting data pipeline",
        run_id=ingestion.run_id,
        user=user,
        action=action,
        input_file=str(input_path),
    )
    record_access("pipeline:start", "started", f"input_file={input_path}")

    audit: Dict[str, Any] = {
        "run_id": ingestion.run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "errors": [],
        "kpis": {},
    }

    compliance_log: List[Dict[str, Any]] = []

    def record_access(stage: str, status: str, message: Optional[str] = None) -> None:
        compliance_log.append(create_access_log_entry(stage, user, action, status, message))

    df = pd.DataFrame()
    try:
        df = ingestion.ingest_csv(input_path.name)
    finally:
        raw_files = ingestion.raw_files or [
            {
                "file": str(input_path),
                "status": "unknown",
                "rows": len(df),
                "timestamp": ingestion.timestamp,
            }
        ]
        log_stage(
            "pipeline:ingestion",
            "Ingestion summary",
            run_id=ingestion.run_id,
            files=[entry["file"] for entry in raw_files],
            rows=len(df),
            errors=len(ingestion.errors),
        )
        record_access(
            "ingestion",
            "completed" if not ingestion.errors else "warning",
            f"rows={len(df)}, errors={len(ingestion.errors)}",
        )

    try:
        if not df.empty:
            df = ingestion.validate_loans(df)
            validation_passed = bool(df.get("_validation_passed", pd.Series([True] * len(df))).all())
            log_stage(
                "pipeline:validation",
                "Validation completed",
                run_id=ingestion.run_id,
                passed=validation_passed,
                rows=len(df),
            )
            record_access(
                "validation",
                "passed" if validation_passed else "failed",
                f"rows={len(df)}",
            )
            if not validation_passed:
                audit["errors"].extend(ingestion.errors)
        else:
            log_stage(
                "pipeline:validation",
                "Validation skipped (no rows)",
                run_id=ingestion.run_id,
            )
            record_access("validation", "skipped", "no rows to validate")
    except Exception as exc:
        error_msg = f"Validation error: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("validation", "error", error_msg)

    kpi_df = pd.DataFrame()
    masked_columns: List[str] = []
    mask_stage = "not_run"
    try:
        if not df.empty and df.get("_validation_passed", pd.Series([False] * len(df))).all():
            log_stage("pipeline:transformation", "Transforming to KPI dataset", run_id=ingestion.run_id)
            kpi_df = transformer.transform_to_kpi_dataset(df)
            kpi_df, masked_columns = mask_pii_in_dataframe(kpi_df)
            mask_stage = "post_transformation"
            record_access("compliance", "pii_masked", f"columns={masked_columns}")
            log_stage("pipeline:transformation", "Transformation completed", rows=len(kpi_df), run_id=ingestion.run_id)
            record_access("transformation", "completed", f"rows={len(kpi_df)}")
        else:
            mask_stage = "transformation_skipped"
            log_stage(
                "pipeline:transformation",
                "Skipping transformation (validation failed or no data)",
                run_id=ingestion.run_id,
            )
            record_access("transformation", "skipped", "validation failed or no data")
    except Exception as exc:
        error_msg = f"Transformation error: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("transformation", "error", error_msg)

    transformation_summary = transformer.get_processing_summary()
    lineage_records = transformer.get_lineage()

    try:
        if not kpi_df.empty:
            log_stage("pipeline:kpi", "Calculating KPIs", run_id=ingestion.run_id)
            kpi_engine = KPIEngine(kpi_df)
            par_30, par_ctx = kpi_engine.calculate_par_30()
            par_90, par90_ctx = kpi_engine.calculate_par_90()
            collection_rate, coll_ctx = kpi_engine.calculate_collection_rate()
            health_score, health_ctx = kpi_engine.calculate_portfolio_health(par_30, collection_rate)
            audit["kpis"] = {
                "par_30": {"value": par_30, **par_ctx},
                "par_90": {"value": par_90, **par90_ctx},
                "collection_rate": {"value": collection_rate, **coll_ctx},
                "health_score": {"value": health_score, **health_ctx},
            }
            audit["kpi_audit_trail"] = kpi_engine.get_audit_trail().to_dict(orient="records")
            log_stage(
                "pipeline:kpi",
                "KPIs calculated",
                par_30=par_30,
                par_90=par_90,
                collection_rate=collection_rate,
                health_score=health_score,
                run_id=ingestion.run_id,
            )
            record_access(
                "kpi",
                "completed",
                f"par_30={par_30}, par_90={par_90}",
            )
        else:
            log_stage(
                "pipeline:kpi",
                "Skipping KPI calculation (no KPI dataset)",
                run_id=ingestion.run_id,
            )
            audit["kpis"] = {}
            audit["kpi_audit_trail"] = []
            record_access("kpi", "skipped", "no KPI dataset to calculate")
    except Exception as exc:
        error_msg = f"KPI calculation error: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("kpi", "error", error_msg)
        if "kpi_engine" in locals():
            audit["kpi_audit_trail"] = kpi_engine.get_audit_trail().to_dict(orient="records")

    audit["ingest"] = ingestion.get_ingest_summary()
    audit["transformation"] = transformation_summary
    audit["lineage"] = lineage_records
    audit["metadata"] = {
        "user": user,
        "action": action,
        "initiated_at": datetime.now(timezone.utc).isoformat(),
    }
    audit["compliance"] = {
        "pii_masked_columns": masked_columns,
        "mask_stage": mask_stage,
        "access_log": compliance_log,
    }

    metadata_payload = {
        "raw_files": raw_files,
        "user": user,
        "action": action,
        "audit": audit,
        "processed_data": transformation_summary,
        "lineage": lineage_records,
        "compliance": audit["compliance"],
    }

    compliance_path = LOGS_DIR / f"{ingestion.run_id}_compliance_report.json"
    try:
        log_stage("pipeline:output", "Writing outputs", run_id=ingestion.run_id)
        record_access("output", "started", "persisting metrics/csv/manifest")
        processed_outputs = write_outputs(ingestion.run_id, kpi_df, audit, metadata_payload, compliance_path)
        record_access("output", "completed", "metrics/csv/manifest persisted")
        record_access("compliance_report", "started", f"path={compliance_path}")
        compliance_report = build_compliance_report(
            ingestion.run_id,
            compliance_log,
            masked_columns,
            mask_stage,
            audit["metadata"],
        )
        write_compliance_report(compliance_report, compliance_path)
        audit["processed_outputs"] = processed_outputs
    except Exception as exc:
        error_msg = f"Failed to write outputs: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("output", "error", error_msg)

    log_stage(
        "pipeline:complete",
        "Pipeline completed",
        run_id=ingestion.run_id,
        user=user,
        action=action,
        errors=len(audit.get("errors", [])),
    )

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ABACO data pipeline")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the CSV input file")
    parser.add_argument("--user", help="Identifier for the user or system triggering the pipeline")
    parser.add_argument("--action", help="Action context (e.g., github-action, manual-run)")
    args = parser.parse_args()
    run_pipeline(input_file=args.input, user=args.user, action=args.action)
