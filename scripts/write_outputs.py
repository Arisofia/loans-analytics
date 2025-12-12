import json
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

def write_outputs(run_id: str, kpi_df: pd.DataFrame, audit: dict):
    """
    Write metrics, audit, and manifest files for full traceability and dashboard integration.
    """
    METRICS_DIR = Path("data/metrics")
    LOGS_DIR = Path("logs/runs")
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    metrics_path = METRICS_DIR / f"{run_id}.parquet"
    csv_path = METRICS_DIR / f"{run_id}.csv"
    audit_path = LOGS_DIR / f"{run_id}.json"
    manifest_path = LOGS_DIR / f"{run_id}_manifest.json"

    kpi_df.to_parquet(metrics_path, index=False)
    kpi_df.to_csv(csv_path, index=False)
    with audit_path.open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, default=str)

    manifest = {
        "run_id": run_id,
        "metrics_file": str(metrics_path),
        "csv_file": str(csv_path),
        "audit_file": str(audit_path),
        "timestamp": audit.get("started_at"),
        "kpis": audit.get("kpis", {}),
        "errors": audit.get("errors", []),
        "kpi_audit_trail": audit.get("kpi_audit_trail", []),
        "ingest": audit.get("ingest", {}),
        "transform_run_id": audit.get("transform_run_id", None),
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    logging.info("Wrote metrics to %s and %s; audit to %s; manifest to %s", metrics_path, csv_path, audit_path, manifest_path)
