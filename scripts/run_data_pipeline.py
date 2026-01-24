import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compliance import build_compliance_report, write_compliance_report
from src.config.paths import Paths
from src.kpi_engine_v2 import KPIEngineV2 as KPIEngine
from src.pipeline.data_ingestion import UnifiedIngestion
from src.pipeline.data_transformation import UnifiedTransformation
from src.pipeline.orchestrator import UnifiedPipeline

# Legacy aliases for backward compatibility with tests/patching
CascadeIngestion = UnifiedIngestion
DataTransformation = UnifiedTransformation

try:
    from src.azure_tracing import setup_azure_tracing

    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for run_data_pipeline")
except (ImportError, Exception) as tracing_err:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.warning("Azure tracing not initialized: %s", tracing_err)

DEFAULT_INPUT = os.getenv(
    "PIPELINE_INPUT_FILE", str(Paths.raw_data_dir() / "abaco_portfolio_calculations.csv")
)


def main(
    input_file: str = DEFAULT_INPUT,
    user: Optional[str] = None,
    action: Optional[str] = None,
    config_path: str = "config/pipeline.yml",
    with_db: bool = False,
    train_model: bool = False,
    ask_kpi: Optional[str] = None,
) -> bool:
    effective_user: str = user or os.getenv("PIPELINE_RUN_USER", "system")
    effective_action: str = action or os.getenv("PIPELINE_RUN_ACTION", "manual")

    logger.info(
        "--- ABACO UNIFIED PIPELINE START --- user=%s action=%s input=%s",
        effective_user,
        effective_action,
        Path(input_file).name,
    )

    config_overrides = {}
    if with_db:
        logger.info("Enabling Supabase upload via config override.")
        config_overrides = {"pipeline": {"phases": {"outputs": {"supabase": {"enabled": True}}}}}

    try:
        pipeline = UnifiedPipeline(config_path=Path(config_path), config_overrides=config_overrides)
        result = pipeline.execute(Path(input_file), user=effective_user, action=effective_action)

        status = result.get("status")
        logger.info("Pipeline completed: %s", status)

        if status == "success":
            # Post-pipeline actions
            run_id = result.get("run_id", "unknown")
            output_path = Paths.metrics_dir(create=True)
            metrics_json_path = output_path / f"{run_id}_metrics.json"
            csv_path = output_path / f"{run_id}.csv"

            # Re-generate outputs for post-pipeline actions
            # This is a simplification; in a real scenario, pipeline.execute would return these directly
            kpi_df = pd.read_parquet(output_path / f"{run_id}.parquet") # Assuming parquet was written
            metrics_data = json.loads(metrics_json_path.read_text())

            if train_model:
                try:
                    logger.info("Starting ML Model Training...")
                    # Adjust sys.path for local imports if necessary, or ensure proper package structure
                    from apps.analytics.risk_model import LoanRiskModel

                    model = LoanRiskModel()
                    metrics = model.train(kpi_df) # Pass the processed dataframe
                    logger.info("ML Training Finished. Metrics: %s", metrics)
                except Exception as e:
                    logger.error("ML Training failed: %s", e)

            if ask_kpi and metrics_json_path:
                try:
                    logger.info("Processing Gen AI Query: %s", ask_kpi)
                    from agents.gen_ai_kpi import KPIQuestionAnsweringAgent

                    # metrics_data is already loaded above
                    flat_metrics = {}
                    for k, v in metrics_data.items():
                        if isinstance(v, dict) and "value" in v:
                            flat_metrics[k] = v["value"]
                        else:
                            flat_metrics[k] = v

                    agent = KPIQuestionAnsweringAgent()
                    answer = agent.answer_query(ask_kpi, flat_metrics)
                    print(f"\n--- KPI AGENT ANSWER ---\n{answer}\n------------------------\n")
                    logger.info("Gen AI Answer generated.")
                except Exception as e:
                    logger.error("Gen AI Query failed: %s", e)

        return status == "success"
    except Exception as exc:
        logger.error("Pipeline execution failed: %s", exc)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the ABACO Unified Data Pipeline")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to the CSV input file")
    parser.add_argument("--user", help="Identifier for the user or system triggering the pipeline")
    parser.add_argument("--action", help="Action context (e.g., github-action, manual-run)")
    parser.add_argument("--config", default="config/pipeline.yml", help="Path to pipeline config")
    parser.add_argument("--with-db", action="store_true", help="Enable Supabase upload")
    parser.add_argument(
        "--train-model", action="store_true", help="Train ML risk model after pipeline"
    )
    parser.add_argument(
        "--ask-kpi", help="Ask a natural language question about the calculated KPIs"
    )

    args = parser.parse_args()
    success = main(
        input_file=args.input,
        user=args.user,
        action=args.action,
        config_path=args.config,
        with_db=args.with_db,
        train_model=args.train_model,
        ask_kpi=args.ask_kpi,
    )

    sys.exit(0 if success else 1)