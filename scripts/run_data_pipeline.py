import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for python/ modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from python.pipeline import UnifiedPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_INPUT = os.getenv("PIPELINE_INPUT_FILE", "data/abaco_portfolio_calculations.csv")

def main(
    input_file: str = DEFAULT_INPUT,
    user: Optional[str] = None,
    action: Optional[str] = None,
    config_path: str = "config/pipeline.yml"
) -> bool:
    """
    Main entry point for the ABACO Unified Data Pipeline.
    """
    user = user or os.getenv("PIPELINE_RUN_USER", "system")
    action = action or os.getenv("PIPELINE_RUN_ACTION", "manual")
    
    context = {
        "user": user,
        "action": action,
        "triggered_at": Path(input_file).name
    }

    logger.info("--- ABACO UNIFIED PIPELINE START ---")
    
    try:
        pipeline = UnifiedPipeline(config_path=config_path)
        manifest = pipeline.run(input_file, context=context)
        
        logger.info(f"Pipeline completed successfully. Manifest: {manifest.get('run_id')}")
        return True
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
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
        config_path=args.config
    )
    
    sys.exit(0 if success else 1)
