import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.paths import Paths
from src.pipeline.orchestrator import UnifiedPipeline

try:
    from src.utils.tracing.azure import setup_azure_tracing

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
) -> bool:
    effective_user: str = str(user or os.getenv("PIPELINE_RUN_USER", "system"))
    effective_action: str = str(action or os.getenv("PIPELINE_RUN_ACTION", "manual"))

    logger.info(
        "--- ABACO UNIFIED PIPELINE START --- user=%s action=%s input=%s",
        effective_user,
        effective_action,
        Path(input_file).name,
    )

    try:
        pipeline = UnifiedPipeline(config_path=Path(config_path))
        result = pipeline.execute(Path(input_file), user=effective_user, action=effective_action)
        logger.info("Pipeline completed: %s", result.get("status"))
        if result.get("status") == "success":
            # Print run_id to stdout so fixtures can find it
            print(f"RUN_ID: {result.get('run_id')}")
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
