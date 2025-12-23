import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

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

DEFAULT_AZURE_CONTAINER = os.getenv("PIPELINE_AZURE_CONTAINER")
DEFAULT_AZURE_CONNECTION_STRING = os.getenv("PIPELINE_AZURE_CONNECTION_STRING") or os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)
DEFAULT_AZURE_ACCOUNT_URL = os.getenv("PIPELINE_AZURE_ACCOUNT_URL") or os.getenv(
    "AZURE_STORAGE_ACCOUNT_URL"
)
DEFAULT_AZURE_BLOB_PREFIX = os.getenv("PIPELINE_AZURE_BLOB_PREFIX", "pipeline-runs")


def log_stage(stage: str, message: str, **details: Any) -> None:
    detail_str = ", ".join(
        f"{key}={value!r}" for key, value in details.items() if value is not None
    )
    payload = f"{stage}: {message}"
    if detail_str:
        payload = f"{payload} | {detail_str}"
    logger.info(payload)


def _is_dataframe_empty(df: Any) -> bool:
    if df is None:
        return True
    empty_attr = getattr(df, "empty", None)
    if isinstance(empty_attr, bool):
        return empty_attr
    return False


def _guess_content_type(path: Path) -> str:
    mapping = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".parquet": "application/octet-stream",
        ".html": "text/html",
        ".md": "text/markdown",
    }
    return mapping.get(path.suffix.lower(), "application/octet-stream")


def upload_outputs_to_azure(
    processed_outputs: Dict[str, Any],
    run_id: str,
    container_name: str,
    connection_string: str | None = None,
    account_url: str | None = None,
    blob_prefix: str | None = None,
) -> Dict[str, str]:
    if not container_name or not str(container_name).strip():
        raise ValueError("Azure container_name is required for export.")
    if not connection_string and not account_url:
        raise ValueError("Azure export requires a connection_string or account_url.")
    blob_service_client = (
        BlobServiceClient.from_connection_string(connection_string)
        if connection_string
        else BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
    )
    container_client = blob_service_client.get_container_client(str(container_name).strip())
    try:
        container_client.create_container()
    except ResourceExistsError:
        logger.info("Azure container '%s' already exists.", container_client.container_name)
    prefix_parts = [blob_prefix.rstrip("/") if blob_prefix else None, run_id]
    prefix = "/".join([part for part in prefix_parts if part])
    uploaded: Dict[str, str] = {}

    # Upload all files in processed_outputs that point to existing files
    for key, file_path in processed_outputs.items():
        if key == "generated_at":
            continue

        if not file_path:
            continue

        path_obj = Path(file_path)
        if not path_obj.exists():
            logger.warning("Azure export skipped missing file %s", path_obj)
            continue

        blob_name = f"{prefix}/{path_obj.name}" if prefix else path_obj.name
        with path_obj.open("rb") as handle:
            container_client.upload_blob(
                name=blob_name,
                data=handle,
                overwrite=True,
                content_settings=ContentSettings(content_type=_guess_content_type(path_obj)),
            )
        uploaded[key] = f"{container_client.container_name}/{blob_name}"

    return uploaded


def rewrite_manifest(
    manifest_path: Path,
    run_id: str,
    processed_outputs: Dict[str, Any],
    metadata: Dict[str, Any],
    compliance_path: Path,
) -> None:
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
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, default=str)


def generate_presentation_assets(run_id: str) -> Dict[str, str]:
    """
    Run presentation export scripts and return paths to generated assets.
    """
    import subprocess

    assets = {}
    try:
        # Run export_presentation.py
        subprocess.run(
            [sys.executable, "scripts/export_presentation.py"],
            check=True,
            capture_output=True,
            text=True,
        )

        # Run export_copilot_slide_payload.py
        subprocess.run(
            [sys.executable, "scripts/export_copilot_slide_payload.py"],
            check=True,
            capture_output=True,
            text=True,
        )

        # Collect generated files
        presentation_dir = Path("exports/presentation")
        if presentation_dir.exists():
            for item in presentation_dir.glob("*"):
                if item.is_file():
                    assets[f"presentation_{item.stem}"] = str(item)

        log_stage("pipeline:presentation", "Generated presentation assets", count=len(assets))

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate presentation assets: {e.stderr}")
        log_stage("pipeline:presentation", "Failed to generate assets", error=str(e))

    return assets


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

    # Generate presentation assets
    presentation_assets = generate_presentation_assets(run_id)

    processed_outputs = {
        "metrics_file": str(metrics_path),
        "csv_file": str(csv_path),
        "manifest_file": str(manifest_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "compliance_report_file": str(compliance_path),
        **presentation_assets,
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


def run_pipeline(
    input_file: str = DEFAULT_INPUT,
    user: str | None = None,
    action: str | None = None,
    azure_container: str | None = None,
    azure_connection_string: str | None = None,
    azure_account_url: str | None = None,
    azure_blob_prefix: str | None = None,
) -> bool:
    user = user or os.getenv("PIPELINE_RUN_USER", "system")
    action = action or os.getenv("PIPELINE_RUN_ACTION", "manual")
    azure_container = azure_container or DEFAULT_AZURE_CONTAINER
    azure_connection_string = azure_connection_string or DEFAULT_AZURE_CONNECTION_STRING
    azure_account_url = azure_account_url or DEFAULT_AZURE_ACCOUNT_URL
    azure_blob_prefix = azure_blob_prefix or DEFAULT_AZURE_BLOB_PREFIX

    input_path = Path(input_file)
    data_dir = str(input_path.parent or ".")
    ingestion = CascadeIngestion(data_dir=data_dir)
    ingestion.set_context(user=user, action=action, input_file=str(input_path))
    transformer = DataTransformation()
    transformer.set_context(
        user=user, action=action, ingest_run_id=ingestion.run_id, source_file=str(input_path)
    )

    compliance_log: List[Dict[str, Any]] = []

    def record_access(stage: str, status: str, message: Optional[str] = None) -> None:
        compliance_log.append(create_access_log_entry(stage, user, action, status, message))

    audit: Dict[str, Any] = {
        "run_id": ingestion.run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "errors": [],
        "kpis": {},
    }

    pipeline_success = True
    validation_passed = False

    log_stage(
        "pipeline:start",
        "Starting data pipeline",
        run_id=ingestion.run_id,
        user=user,
        action=action,
        input_file=str(input_path),
    )
    record_access("pipeline:start", "started", f"input_file={input_path}")

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
        if not _is_dataframe_empty(df):
            df = ingestion.validate_loans(df)
            validation_series = df.get("_validation_passed") if hasattr(df, "get") else None
            if validation_series is None:
                try:
                    validation_series = df["_validation_passed"]
                except Exception:
                    validation_series = None
            validation_passed = bool(getattr(validation_series, "all", lambda: False)())
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
                pipeline_success = False
        else:
            log_stage(
                "pipeline:validation",
                "Validation skipped (no rows)",
                run_id=ingestion.run_id,
            )
            record_access("validation", "skipped", "no rows to validate")
            pipeline_success = False
    except Exception as exc:
        error_msg = f"Validation error: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("validation", "error", error_msg)
        pipeline_success = False

    kpi_df = pd.DataFrame()
    masked_columns: List[str] = []
    mask_stage = "not_run"
    try:
        if not _is_dataframe_empty(df) and validation_passed:
            log_stage(
                "pipeline:transformation", "Transforming to KPI dataset", run_id=ingestion.run_id
            )
            kpi_df = transformer.transform_to_kpi_dataset(df)
            kpi_df, masked_columns = mask_pii_in_dataframe(kpi_df)
            mask_stage = "post_transformation"
            record_access("compliance", "pii_masked", f"columns={masked_columns}")
            log_stage(
                "pipeline:transformation",
                "Transformation completed",
                rows=len(kpi_df),
                run_id=ingestion.run_id,
            )
            record_access("transformation", "completed", f"rows={len(kpi_df)}")
        else:
            mask_stage = "transformation_skipped"
            log_stage(
                "pipeline:transformation",
                "Skipping transformation (validation failed or no data)",
                run_id=ingestion.run_id,
            )
            record_access("transformation", "skipped", "validation failed or no data")
            pipeline_success = False
    except Exception as exc:
        error_msg = f"Transformation error: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("transformation", "error", error_msg)
        pipeline_success = False

    transformation_summary = transformer.get_processing_summary()
    lineage_records = transformer.get_lineage()

    try:
        if not _is_dataframe_empty(kpi_df):
            log_stage("pipeline:kpi", "Calculating KPIs", run_id=ingestion.run_id)
            kpi_engine = KPIEngine(kpi_df)
            par_30, par_ctx = kpi_engine.calculate_par_30()
            par_90, par90_ctx = kpi_engine.calculate_par_90()
            collection_rate, coll_ctx = kpi_engine.calculate_collection_rate()
            health_score, health_ctx = kpi_engine.calculate_portfolio_health(
                par_30, collection_rate
            )
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
            pipeline_success = False
    except Exception as exc:
        error_msg = f"KPI calculation error: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("kpi", "error", error_msg)
        pipeline_success = False
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
        if _is_dataframe_empty(kpi_df):
            raise ValueError("No KPI dataset generated; cannot persist outputs.")
        log_stage("pipeline:output", "Writing outputs", run_id=ingestion.run_id)
        record_access("output", "started", "persisting metrics/csv/manifest")
        processed_outputs = write_outputs(
            ingestion.run_id, kpi_df, audit, metadata_payload, compliance_path
        )
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

        if azure_container:
            log_stage(
                "pipeline:azure_export",
                "Exporting processed outputs to Azure Blob",
                run_id=ingestion.run_id,
                container=azure_container,
            )
            record_access("azure_export", "started", f"container={azure_container}")
            try:
                azure_uploads = upload_outputs_to_azure(
                    processed_outputs,
                    ingestion.run_id,
                    container_name=azure_container,
                    connection_string=azure_connection_string,
                    account_url=azure_account_url,
                    blob_prefix=azure_blob_prefix,
                )
            except Exception as azure_exc:
                error_msg = f"Azure export failed: {type(azure_exc).__name__}: {azure_exc}"
                logger.exception(error_msg)
                audit["errors"].append(error_msg)
                pipeline_success = False
                record_access("azure_export", "error", error_msg)
            else:
                if azure_uploads:
                    processed_outputs["azure_blobs"] = azure_uploads
                    audit["processed_outputs"] = processed_outputs
                    metadata_payload["audit"] = audit
                    rewrite_manifest(
                        Path(processed_outputs["manifest_file"]),
                        ingestion.run_id,
                        processed_outputs,
                        metadata_payload,
                        compliance_path,
                    )
                    record_access(
                        "azure_export", "completed", f"uploaded={list(azure_uploads.keys())}"
                    )
                else:
                    record_access("azure_export", "skipped", "no files uploaded")
    except Exception as exc:
        error_msg = f"Failed to write outputs: {type(exc).__name__}: {exc}"
        logger.exception(error_msg)
        audit["errors"].append(error_msg)
        record_access("output", "error", error_msg)
        pipeline_success = False

    log_stage(
        "pipeline:complete",
        "Pipeline completed",
        run_id=ingestion.run_id,
        user=user,
        action=action,
        errors=len(audit.get("errors", [])),
        azure_export=bool(azure_container),
    )

    return pipeline_success and not audit.get("errors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ABACO data pipeline")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the CSV input file")
    parser.add_argument("--user", help="Identifier for the user or system triggering the pipeline")
    parser.add_argument("--action", help="Action context (e.g., github-action, manual-run)")
    parser.add_argument("--azure-container", help="Azure Blob container to upload cleaned outputs")
    parser.add_argument("--azure-connection-string", help="Azure Blob Storage connection string")
    parser.add_argument(
        "--azure-account-url",
        help="Azure Blob Storage account URL (used with DefaultAzureCredential)",
    )
    parser.add_argument(
        "--azure-blob-prefix", help="Prefix for blob paths (default: pipeline-runs/<run_id>)"
    )
    args = parser.parse_args()
    run_pipeline(
        input_file=args.input,
        user=args.user,
        action=args.action,
        azure_container=args.azure_container,
        azure_connection_string=args.azure_connection_string,
        azure_account_url=args.azure_account_url,
        azure_blob_prefix=args.azure_blob_prefix,
    )
