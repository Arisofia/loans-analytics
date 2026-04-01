"""Pipeline Health Check — verifies the pipeline can initialize and validate config.

Usage:
    python scripts/monitoring/pipeline_health_check.py [--input PATH]

Exit codes:
    0  — pipeline is healthy (imports load, config parses, optional dry-run passes)
    1  — pipeline is unhealthy (import error, config error, or validation failure)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def _check_imports() -> bool:
    try:
        from backend.src.pipeline.orchestrator import UnifiedPipeline  # noqa: F401
        from backend.src.pipeline.ingestion import IngestionPhase  # noqa: F401
        from backend.src.pipeline.transformation import TransformationPhase  # noqa: F401
        from backend.src.pipeline.calculation import CalculationPhase  # noqa: F401
        from backend.src.pipeline.output import OutputPhase  # noqa: F401
        return True
    except ImportError as exc:
        print(f"[FAIL] Import error: {exc}", file=sys.stderr)
        return False


def _check_config(config_path: Path) -> bool:
    try:
        from backend.src.pipeline.orchestrator import UnifiedPipeline
        pipeline = UnifiedPipeline(config_path=config_path if config_path.exists() else None)
        _ = pipeline  # instantiation succeeded
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Config/init error: {exc}", file=sys.stderr)
        return False


def _check_validate_mode(config_path: Path, input_path: Path | None) -> bool:
    try:
        from backend.src.pipeline.orchestrator import UnifiedPipeline
        pipeline = UnifiedPipeline(config_path=config_path if config_path.exists() else None)
        result = pipeline.execute(input_path=input_path, mode="validate")
        return result.get("status") in ("success", "warning", "completed")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] validate-mode execution error: {exc}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline health check")
    parser.add_argument("--config", type=Path, default=Path("config/pipeline.yml"))
    parser.add_argument("--input", type=Path, default=None,
                        help="Optional data file for validate-mode dry run")
    parser.add_argument("--skip-validate", action="store_true",
                        help="Skip the pipeline validation execution check")
    args = parser.parse_args()

    checks_passed = 0
    checks_total = 2  # 1. import check + 2. config/init check (always run)

    # 1. Import check
    if _check_imports():
        print("[OK]  Pipeline imports")
        checks_passed += 1
    else:
        print("[FAIL] Pipeline imports")

    # 2. Config / init check
    if _check_config(args.config):
        print("[OK]  Pipeline config + init")
        checks_passed += 1
    else:
        print("[FAIL] Pipeline config + init")

    # 3. Optional validate-mode check
    if not args.skip_validate and args.input is not None:
        checks_total += 1
        if args.input.exists():
            if _check_validate_mode(args.config, args.input):
                print("[OK]  Pipeline validate-mode execution")
                checks_passed += 1
            else:
                print("[FAIL] Pipeline validate-mode execution")
        else:
            print(f"[SKIP] validate-mode — input not found: {args.input}")

    print(f"\nHealth check: {checks_passed}/{checks_total} passed")
    sys.exit(0 if checks_passed == checks_total else 1)


if __name__ == "__main__":
    main()
