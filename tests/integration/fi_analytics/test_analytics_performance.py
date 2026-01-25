"""
FI-ANALYTICS-002: Sprint 2 Performance, Robustness & E2E

Test Cases:
  - B-03: Performance SLA validation (<30s for 10k records)
  - E-01: Retry logic for transient failures
  - G-01: Idempotency (multiple runs produce same results)
  - I-01: Full End-to-End Acceptance
"""

import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Dict  # noqa: E402

import pandas as pd  # noqa: E402



class TestAnalyticsPerformanceRobustness:
    """Performance and robustness tests."""

    def test_b03_performance_sla(self, analytics_test_env: Dict[str, Any]) -> None:
        """
        B-03: Performance SLA validation.
        Verify that pipeline handles 10k records in < 30 seconds.
        """
        # Generate 10k records
        large_dataset_path = analytics_test_env["output_dir"] / "large_sample.csv"
        df_base = pd.read_csv(analytics_test_env["dataset_path"])
        df_large = pd.concat([df_base] * (10000 // len(df_base) + 1)).head(10000)
        # Add required columns (unconditionally)
        df_large["loan_id"] = [f"loan_{i}" for i in range(len(df_large))]
        if "total_receivable_usd" not in df_large.columns:
            df_large["total_receivable_usd"] = 1000.0
        if "measurement_date" not in df_large.columns:
            df_large["measurement_date"] = "2025-01-01"
        df_large.to_csv(large_dataset_path, index=False)

        output_dir = analytics_test_env["output_dir"] / "perf_out"
        output_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        env = os.environ.copy()
        env["OTEL_SDK_DISABLED"] = "true"
        env["PYTHONPATH"] = os.path.join(os.getcwd(), "python")
        result = subprocess.run([
            sys.executable,
            "python/scripts/run_v2_pipeline.py",
            "--input",
            str(large_dataset_path)
        ], capture_output=True, text=True, timeout=60, env=env)
        duration = time.time() - start_time

        assert result.returncode == 0
        assert duration < 30.0, f"Pipeline took too long: {duration:.2f}s"
        assert "Pipeline completed: success" in (result.stdout + result.stderr)

    def test_g01_idempotency(self, analytics_test_env: Dict[str, Any]) -> None:
        """
        G-01: Idempotency.
        Verify that multiple runs with same data produce same KPI results.
        """
        dataset = analytics_test_env["dataset_path"]

        import re  # noqa: E402

        results = []
        for i in range(2):
            result = subprocess.run([
                sys.executable,
                "python/scripts/run_v2_pipeline.py",
                "--input",
                str(dataset)
            ], capture_output=True, text=True, env={**os.environ, "OTEL_SDK_DISABLED": "true", "PYTHONPATH": os.path.join(os.getcwd(), "python")}, check=True)

            match = re.search(r"RUN_ID: ([\w_]+)", result.stdout)
            assert match, f"RUN_ID not found in output: {result.stdout}"
            run_id = match.group(1)

            metrics_file = Path("data/metrics") / f"{run_id}_metrics.json"
            with open(metrics_file) as f:
                data = json.load(f)

                # Recursively remove run-specific fields
                def clean_data(obj):
                    if isinstance(obj, dict):
                        obj.pop("run_id", None)
                        obj.pop("timestamp", None)
                        obj.pop("pipeline_status", None)
                        for v in obj.values():
                            clean_data(v)
                    elif isinstance(obj, list):
                        for item in obj:

                clean_data(data)
                results.append(data)

        test_overrides = {
            "pipeline": {
                "phases": {
                    "ingestion": {
                        "validation": {
                            "strict": False,
                            "required_columns": ["total_receivable_usd"],
                        }
                    },
                    "outputs": {
                        "dashboard_triggers": {
                            "enabled": True,
                            "outputs": ["azure", "supabase"],
                            "clients": {
                                "azure": {"enabled": True, "subscription_id": "test_id"},
                                "supabase": {"enabled": True, "url": "test_url"},
                            },
                        }
                    },
                }
            }
        }
        deep_update(config, test_overrides)

        config_path = analytics_test_env["output_dir"] / "test_pipeline_config_full.yml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)


        # FIX: Point to the existing pipeline script
        pipeline_script = "python/scripts/run_v2_pipeline.py"
        if not Path(pipeline_script).exists():
            assert False, f"Pipeline script not found at {pipeline_script}"

        # Ensure the input dataset has the required columns
        df = pd.read_csv(analytics_test_env["dataset_path"])
        if "loan_id" not in df.columns:
            df["loan_id"] = [f"loan_{i}" for i in range(len(df))]
        if "total_receivable_usd" not in df.columns:
            df["total_receivable_usd"] = 1000.0
        if "measurement_date" not in df.columns:
            df["measurement_date"] = "2025-01-01"
        df.to_csv(analytics_test_env["dataset_path"], index=False)
        result = subprocess.run(
            results = []
            for i in range(2):
                result = subprocess.run([
                    sys.executable,
                    "python/scripts/run_v2_pipeline.py",
                    "--input",
                    str(dataset)
                ], capture_output=True, text=True, env={**os.environ, "OTEL_SDK_DISABLED": "true", "PYTHONPATH": os.path.join(os.getcwd(), "python")}, check=True)

                match = re.search(r"RUN_ID: ([\w_]+)", result.stdout)
                assert match, f"RUN_ID not found in output: {result.stdout}"
                run_id = match.group(1)

                metrics_file = Path("data/metrics") / f"{run_id}_metrics.json"
                with open(metrics_file) as f:
                    data = json.load(f)

                # Recursively remove run-specific fields
                def clean_data(obj):
                    if isinstance(obj, dict):
                        obj.pop("run_id", None)
                        obj.pop("timestamp", None)
                        obj.pop("pipeline_status", None)
                        for v in obj.values():
                            clean_data(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            clean_data(item)

                clean_data(data)
                results.append(data)

            assert results[0] == results[1], "Idempotency failure: results differ between runs"
