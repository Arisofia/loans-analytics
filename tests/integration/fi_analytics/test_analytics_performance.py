"""
FI-ANALYTICS-002: Sprint 2 Performance, Robustness & E2E

Test Cases:
  - B-03: Performance SLA validation (<30s for 10k records)
  - E-01: Retry logic for transient failures
  - G-01: Idempotency (multiple runs produce same results)
  - I-01: Full End-to-End Acceptance
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import pandas as pd


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
        df_large.to_csv(large_dataset_path, index=False)

        output_dir = analytics_test_env["output_dir"] / "perf_out"
        output_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_data_pipeline.py",
                "--input",
                str(large_dataset_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "OTEL_SDK_DISABLED": "true"},
        )
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

        import re

        results = []
        for i in range(2):
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_data_pipeline.py",
                    "--input",
                    str(dataset),
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "OTEL_SDK_DISABLED": "true"},
                check=True,
            )

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

        assert (
            results[0] == results[1]
        ), "Idempotency failure: results differ between runs"

    def test_i01_e2e_acceptance(self, analytics_test_env: Dict[str, Any]) -> None:
        """
        I-01: Full End-to-End Acceptance.
        Smoke test for a full run with all features enabled (mocked).
        """
        import re

        import yaml

        dataset = analytics_test_env["dataset_path"]

        # Load base config
        base_config_path = Path("config/pipeline.yml")
        with open(base_config_path) as f:
            config = yaml.safe_load(f)

        # Update with test-specific overrides
        def deep_update(source, overrides):
            for key, value in overrides.items():
                if (
                    isinstance(value, dict)
                    and key in source
                    and isinstance(source[key], dict)
                ):
                    deep_update(source[key], value)
                else:
                    source[key] = value
            return source

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
                            "outputs": ["figma", "notion"],
                            "clients": {
                                "figma": {"enabled": True, "token": "test_token"},
                                "notion": {"enabled": True, "api_token": "test_token"},
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

        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_data_pipeline.py",
                "--input",
                str(dataset),
                "--config",
                str(config_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "OTEL_SDK_DISABLED": "true"},
        )

        assert result.returncode == 0, f"Pipeline failed with stderr: {result.stderr}"

        match = re.search(r"RUN_ID: ([\w_]+)", result.stdout)
        assert match, f"RUN_ID not found in output: {result.stdout}"
        run_id = match.group(1)

        # Check manifest for trigger results instead of logs which can be finicky
        manifest_path = Path("logs/runs") / run_id / f"{run_id}_manifest.json"
        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = json.load(f)
            if "triggers" not in manifest:
                print(f"DEBUG: Manifest keys: {list(manifest.keys())}")
                print(f"DEBUG: result.stdout: {result.stdout}")
                print(f"DEBUG: result.stderr: {result.stderr}")
            assert "triggers" in manifest
            assert "dashboard_trigger" in manifest["triggers"]
            trigger_res = manifest["triggers"]["dashboard_trigger"]
            assert "outputs" in trigger_res
            assert "figma" in trigger_res["outputs"]
            assert "notion" in trigger_res["outputs"]

        assert (Path("data/metrics") / f"{run_id}_metrics.json").exists()
        assert (Path("data/metrics") / f"{run_id}.csv").exists()
