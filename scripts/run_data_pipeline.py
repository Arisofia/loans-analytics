
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd

# Add project root to path for python/ modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from python.ingestion import CascadeIngestion
from python.transformation import DataTransformation
from python.kpi_engine import KPIEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_INPUT = os.getenv("PIPELINE_INPUT_FILE", "data/abaco_portfolio_calculations.csv")
METRICS_DIR = Path("data/metrics")
LOGS_DIR = Path("logs/runs")
METRICS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def ensure_required_columns(df: pd.DataFrame, required: Tuple[str, ...]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def write_outputs(run_id: str, kpi_df: pd.DataFrame, audit: Dict[str, Any]) -> None:
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

    logger.info("Wrote metrics to %s and %s; audit to %s; manifest to %s", metrics_path, csv_path, audit_path, manifest_path)

def run_pipeline(input_file: str = DEFAULT_INPUT) -> bool:
    run_started = datetime.now(timezone.utc).isoformat()
    ingestion = CascadeIngestion(data_dir=str(Path(input_file).parent or "."))
    transformer = DataTransformation()
    audit: Dict[str, Any] = {
        "run_id": ingestion.run_id,
        "started_at": run_started,
        "input_file": input_file,
        "errors": [],
        "kpis": {},
    }

    try:
        logger.info("Ingesting %s", input_file)
        df = ingestion.ingest_csv(Path(input_file).name)
        if df.empty:
            raise RuntimeError("Ingestion returned empty DataFrame")

        logger.info("Validating ingested data")
        df = ingestion.validate_loans(df)
        if not df["_validation_passed"].all():
            raise RuntimeError("Validation failed; see ingestion.errors")

        ensure_required_columns(df, ("total_receivable_usd",))

        logger.info("Transforming to KPI dataset")
        try:
            kpi_df = transformer.transform_to_kpi_dataset(df)
        except Exception as exc:
            error_msg = f"Transformation error: {type(exc).__name__}: {exc}"
            logger.error(error_msg, exc_info=True)
            audit["errors"].extend(ingestion.errors)
            audit["errors"].append({
                "stage": "transformation",
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            write_outputs(ingestion.run_id, pd.DataFrame(), audit)
            return False

        logger.info("Calculating KPIs")
        try:
            kpi_engine = KPIEngine(kpi_df)
            par_30, par_ctx = kpi_engine.calculate_par_30()
            collection_rate, coll_ctx = kpi_engine.calculate_collection_rate()
            health_score = kpi_engine.calculate_portfolio_health(par_30, collection_rate)
            audit["kpis"] = {
                "par_30": {"value": par_30, **par_ctx},
                "collection_rate": {"value": collection_rate, **coll_ctx},
                "health_score": {"value": health_score},
            }
            audit["kpi_audit_trail"] = kpi_engine.get_audit_trail().to_dict(orient="records")
        except Exception as exc:
            error_msg = f"KPI calculation error: {type(exc).__name__}: {exc}"
            logger.error(error_msg, exc_info=True)
            audit["errors"].extend(ingestion.errors)
            audit["errors"].append({
                "stage": "kpi_calculation",
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if 'kpi_engine' in locals():
                audit["kpi_audit_trail"] = kpi_engine.get_audit_trail().to_dict(orient="records")
            write_outputs(ingestion.run_id, pd.DataFrame(), audit)
            return False

        audit["ingest"] = ingestion.get_ingest_summary()
        audit["transform_run_id"] = transformer.run_id

        logger.info("Writing outputs and audit")
        write_outputs(ingestion.run_id, kpi_df, audit)
        logger.info("Pipeline completed successfully (run_id=%s)", ingestion.run_id)
        return True

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("Pipeline failed: %s", error_msg, exc_info=True)
        ingestion._record_error("pipeline", error_msg)  # noqa: SLF001
        audit["errors"].extend(ingestion.errors)
        audit["errors"].append({
            "stage": "pipeline",
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            write_outputs(ingestion.run_id, pd.DataFrame(), audit)
        except Exception:
            pass
        return False

if __name__ == "__main__":
    run_pipeline(DEFAULT_INPUT)
