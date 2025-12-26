import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path for python/ modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.compliance import build_compliance_report, write_compliance_report
from python.ingestion import CascadeIngestion
from python.kpi_engine import KPIEngine
from python.pipeline.orchestrator import UnifiedPipeline
from python.transformation import DataTransformation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_INPUT = os.getenv("PIPELINE_INPUT_FILE", "data/abaco_portfolio_calculations.csv")


def write_outputs(
    df, metrics: Dict[str, Any], manifest: Dict[str, Any], output_dir: str = "data/metrics"
) -> Dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    run_id = manifest.get("run_id", "run")
    metrics_file = output_path / f"{run_id}.parquet"
    csv_file = output_path / f"{run_id}.csv"
    manifest_file = output_path / f"{run_id}_manifest.json"
    compliance_report_file = output_path / f"{run_id}_compliance.json"

    df.to_parquet(metrics_file, index=False)
    df.to_csv(csv_file, index=False)

    manifest.update({"metrics_file": str(metrics_file), "csv_file": str(csv_file)})
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "metrics_file": str(metrics_file),
        "csv_file": str(csv_file),
        "manifest_file": str(manifest_file),
        "compliance_report_file": str(compliance_report_file),
        "generated_at": manifest.get("generated_at"),
    }


def upload_outputs_to_azure(
    outputs: Dict[str, Any],
    azure_connection_string: str,
    azure_container: str,
    azure_blob_prefix: str,
) -> Dict[str, str]:
    # Placeholder for legacy pipeline tests; upload handled by UnifiedOutput.
    return {}


def rewrite_manifest(manifest_path: str, azure_blobs: Dict[str, str]) -> None:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    manifest["azure_blobs"] = azure_blobs
    Path(manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_pipeline(
    input_file: str,
    azure_container: Optional[str] = None,
    azure_connection_string: Optional[str] = None,
    azure_blob_prefix: Optional[str] = None,
) -> bool:
    ingestion = CascadeIngestion(data_dir=str(Path(input_file).parent))
    ingested = ingestion.ingest_csv(Path(input_file).name)
    validated = ingestion.validate_loans(ingested)

    if validated.empty or not bool(validated.get("_validation_passed", True).all()):
        return False

    transformer = DataTransformation()
    kpi_df = transformer.transform_to_kpi_dataset(validated)

    kpi_engine = KPIEngine(kpi_df)
    par_30, par_30_ctx = kpi_engine.calculate_par_30()
    par_90, par_90_ctx = kpi_engine.calculate_par_90()
    collection_rate, coll_ctx = kpi_engine.calculate_collection_rate()
    health_score, health_ctx = kpi_engine.calculate_portfolio_health(par_30, collection_rate)

    metrics = {
        "PAR30": {"value": par_30, **par_30_ctx},
        "PAR90": {"value": par_90, **par_90_ctx},
        "CollectionRate": {"value": collection_rate, **coll_ctx},
        "PortfolioHealth": {"value": health_score, **health_ctx},
    }

    manifest = {
        "run_id": ingestion.run_id,
        "generated_at": ingestion.timestamp,
        "metrics": metrics,
        "ingestion": ingestion.get_ingest_summary(),
        "transformation": transformer.get_processing_summary(),
        "lineage": transformer.get_lineage(),
    }

    outputs = write_outputs(kpi_df, metrics, manifest)

    compliance_report = build_compliance_report(
        run_id=ingestion.run_id,
        access_log=[],
        masked_columns=[],
        mask_stage="ingestion",
        metadata={"input": input_file},
    )
    write_compliance_report(compliance_report, Path(outputs["compliance_report_file"]))

    if azure_container and azure_connection_string:
        azure_blobs = upload_outputs_to_azure(
            outputs, azure_connection_string, azure_container, azure_blob_prefix or "runs"
        )
        if azure_blobs:
            rewrite_manifest(outputs["manifest_file"], azure_blobs)

    return True


def main(
    input_file: str = DEFAULT_INPUT,
    user: Optional[str] = None,
    action: Optional[str] = None,
    config_path: str = "config/pipeline.yml",
) -> bool:
    user = user or os.getenv("PIPELINE_RUN_USER", "system")
    action = action or os.getenv("PIPELINE_RUN_ACTION", "manual")

    context = {
        "user": user,
        "action": action,
        "triggered_at": Path(input_file).name,
    }

    logger.info("--- ABACO UNIFIED PIPELINE START ---")

    try:
        pipeline = UnifiedPipeline(config_path=Path(config_path))
        result = pipeline.execute(Path(input_file), user=user, action=action)
        logger.info("Pipeline completed: %s", result.get("status"))
        return result.get("status") == "success"
    except Exception as exc:
        logger.error("Pipeline execution failed: %s", exc)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ABACO Unified Data Pipeline")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the CSV input file")
    parser.add_argument("--user", help="Identifier for the user or system triggering the pipeline")
    parser.add_argument("--action", help="Action context (e.g., github-action, manual-run)")
    parser.add_argument("--config", default="config/pipeline.yml", help="Path to pipeline config")

    args = parser.parse_args()
    success = main(
        input_file=args.input,
        user=args.user,
        action=args.action,
        config_path=args.config,
    )

    sys.exit(0 if success else 1)
