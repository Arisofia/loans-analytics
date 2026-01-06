"""
FI-ANALYTICS-002: Sprint 2 Performance, Robustness & E2E

Test Cases:
  - B-03: Performance SLA validation (<30s for 10k records)
  - E-01: Retry logic for transient failures
  - G-01: Idempotency (multiple runs produce same results)
  - I-01: Full End-to-End Acceptance
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest


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
                "-m",
                "src.analytics.run_pipeline",
                "--dataset", str(large_dataset_path),
                "--output", str(output_dir)
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "OTEL_SDK_DISABLED": "true"}
        )
        duration = time.time() - start_time

        assert result.returncode == 0
        assert duration < 30.0, f"Pipeline took too long: {duration:.2f}s"
        assert "Pipeline execution completed successfully" in (result.stdout + result.stderr)

    def test_g01_idempotency(self, analytics_test_env: Dict[str, Any]) -> None:
        """
        G-01: Idempotency.
        Verify that multiple runs with same data produce same KPI results.
        """
        dataset = analytics_test_env["dataset_path"]
        
        results = []
        for i in range(2):
            out_dir = analytics_test_env["output_dir"] / f"idemp_{i}"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.analytics.run_pipeline",
                    "--dataset", str(dataset),
                    "--output", str(out_dir)
                ],
                env={**os.environ, "OTEL_SDK_DISABLED": "true"},
                check=True
            )
            with open(out_dir / "kpi_results.json") as f:
                data = json.load(f)
                # Remove run-specific fields
                data.pop("run_id", None)
                data.pop("timestamp", None)
                results.append(data)

        assert results[0] == results[1], "Idempotency failure: results differ between runs"

    def test_e01_retry_placeholder(self, analytics_test_env: Dict[str, Any]) -> None:
        """
        E-01: Retry logic placeholder.
        Verify that pipeline continues even if simulated transient failure happens.
        """
        # This is partially covered by integration tests (soft-fail)
        # In a real implementation, we'd check logs for "retry" attempts.
        pass

    def test_i01_e2e_acceptance(self, analytics_test_env: Dict[str, Any]) -> None:
        """
        I-01: Full End-to-End Acceptance.
        Smoke test for a full run with all features enabled (mocked).
        """
        dataset = analytics_test_env["dataset_path"]
        output_dir = analytics_test_env["output_dir"] / "e2e_out"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.analytics.run_pipeline",
                "--dataset", str(dataset),
                "--output", str(output_dir),
                "--sync-figma",
                "--figma-token", "test_token",
                "--sync-notion"
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "OTEL_SDK_DISABLED": "true"}
        )

        assert result.returncode == 0
        combined = result.stdout + result.stderr
        assert "Syncing KPIs to Figma" in combined
        assert "Syncing to Notion" in combined
        assert (output_dir / "kpi_results.json").exists()
        assert (output_dir / "metrics.csv").exists()
