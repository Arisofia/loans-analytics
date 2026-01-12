import argparse
import sys
from pathlib import Path

from src.pipeline.orchestrator import UnifiedPipeline


def main():
    parser = argparse.ArgumentParser(description="Run the analytics pipeline.")
    parser.add_argument("--dataset", required=True, help="Path to input dataset.")
    parser.add_argument("--output", required=True, help="Path to output directory.")
    parser.add_argument("--config", help="Path to configuration file.")

    args = parser.parse_args()

    pipeline = UnifiedPipeline(config_path=Path(args.config) if args.config else None)
    result = pipeline.execute(Path(args.dataset))

    if result["status"] == "success":
        print("Pipeline completed: success")
        sys.exit(0)
    else:
        print(f"Pipeline failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    print("Pipeline start")
    main()
