#!/usr/bin/env python
"""
24-Hour Monitoring Checkpoint Tracker
Executes validation and records metrics for each checkpoint
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.paths import Paths, get_project_root


class MonitoringCheckpoint:
    """Track and record checkpoint metrics"""

    def __init__(self, checkpoint_hour: Optional[int] = None):
        self.checkpoint_hour = checkpoint_hour or self._current_hour()
        self.start_time = datetime.now()
        self.metrics: Dict[str, Any] = {
            "checkpoint_hour": self.checkpoint_hour,
            "timestamp": self.start_time.isoformat(),
            "validation": None,
            "system_metrics": None,
            "status": "PENDING",
        }

    def _current_hour(self) -> int:
        """Calculate hours since cutover (01:58:46 UTC)"""
        cutover_time = datetime(2025, 12, 26, 1, 58, 46)
        now = datetime.utcnow()
        hours = int((now - cutover_time).total_seconds() / 3600)
        return max(0, hours)

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Gather system resource metrics"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "memory_rss_mb": memory_info.rss / (1024 * 1024),
                "memory_vms_mb": memory_info.vms / (1024 * 1024),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "num_threads": process.num_threads(),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def run_validation(self) -> Dict[str, Any]:
        """Execute production validation script"""
        try:
            # Use argument list, never shell=True, and do not interpolate
            # untrusted input.
            script_path = Paths.scripts_dir() / "production_validation.py"
            if not script_path.exists():
                return {
                    "status": "FAIL",
                    "error": f"Missing validation script at {script_path}",
                }
            completed = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
                check=False,
            )
            validation_report_path = get_project_root() / "production_validation_report.json"

            if completed.returncode == 0 and validation_report_path.exists():
                with open(validation_report_path, encoding="utf-8") as handle:
                    report = json.load(handle)
                if completed.stdout:
                    report["stdout"] = completed.stdout.strip()
                if completed.stderr:
                    report["stderr"] = completed.stderr.strip()
                report["returncode"] = completed.returncode
                return report
            else:
                # Optionally: Delete any stale report if process failed
                if validation_report_path.exists():
                    try:
                        validation_report_path.unlink()
                    except Exception:
                        pass

                return {
                    "status": "FAIL",
                    "error": f"Validation script failed (returncode={completed.returncode})",
                    "returncode": completed.returncode,
                    "stdout": completed.stdout.strip() if completed.stdout else "",
                    "stderr": completed.stderr.strip() if completed.stderr else "",
                }

        except subprocess.TimeoutExpired:
            return {"status": "FAIL", "error": "Validation script timeout"}
        except Exception as exc:
            return {"status": "FAIL", "error": str(exc)}

    def execute(self) -> dict:
        """Execute checkpoint validation and collect metrics"""
        print(f"\n{'=' * 80}")
        print(f"CHECKPOINT: Hour {self.checkpoint_hour}")
        print(f"Timestamp: {self.start_time.isoformat()}")
        print(f"{'=' * 80}\n")

        print("Running validation suite...")
        self.metrics["validation"] = self.run_validation()
        validation_status = self.metrics["validation"].get("status", "UNKNOWN")
        print(f"Validation Status: {validation_status}")

        print("\nCollecting system metrics...")
        system_metrics = self._get_system_metrics()
        self.metrics["system_metrics"] = system_metrics
        if "error" not in system_metrics:
            print(f"  Memory: {system_metrics['memory_rss_mb']:.1f} MB")
            print(f"  CPU: {system_metrics['cpu_percent']:.1f}%")

        self.metrics["status"] = validation_status
        self.metrics["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()

        return self.metrics

    def save_checkpoint(self, output_dir: Optional[str] = None) -> str:
        """Save checkpoint results to file

        Args:
            output_dir: Directory to save checkpoint. Defaults to logs/monitoring from config.
        """
        if output_dir is None:
            output_path = Paths.monitoring_logs_dir(create=True)
        else:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        checkpoint_file = output_path / f"checkpoint_hour_{self.checkpoint_hour:02d}.json"
        with open(checkpoint_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

        return str(checkpoint_file)

    def print_summary(self):
        """Print checkpoint summary"""
        print(f"\n{'─' * 80}")
        print(f"CHECKPOINT SUMMARY - Hour {self.checkpoint_hour}")
        print(f"{'─' * 80}")

        validation = self.metrics.get("validation") or {}
        if not isinstance(validation, dict):
            validation = {}
        print(f"\nValidation Status: {validation.get('status', 'UNKNOWN')}")

        if validation.get("checks"):
            print("\nValidation Checks:")
            for check_name, check_result in validation["checks"].items():
                if check_result:
                    status = check_result.get("status", "UNKNOWN")
                else:
                    status = "UNKNOWN"
                print(f"  ✓ {check_name}: {status}")

        system_metrics = self.metrics.get("system_metrics") or {}
        if isinstance(system_metrics, dict) and "error" not in system_metrics:
            print("\nSystem Metrics:")
            print(f"  Memory: {system_metrics['memory_rss_mb']:.1f} MB " "(threshold: 200 MB)")
            print(f"  CPU: {system_metrics['cpu_percent']:.1f}% " "(threshold: 80%)")
            print(f"  Threads: {system_metrics['num_threads']}")

        performance_checks = validation.get("checks", {}).get("performance")
        if isinstance(performance_checks, dict):
            perf = performance_checks.get("metrics", {})
            print("\nPerformance:")
            print(f"  Latency: {perf.get('latency_ms', 'N/A')} ms " "(threshold: 100 ms)")
            print(f"  Throughput: {perf.get('throughput_rows_per_sec', 'N/A')} " "rows/sec")

        duration = self.metrics.get("duration_seconds")
        if isinstance(duration, (int, float)):
            print(f"\nDuration: {duration:.2f} seconds")
        else:
            print("\nDuration: N/A")
        print(f"{'─' * 80}\n")


def main():
    checkpoint = MonitoringCheckpoint()
    results = checkpoint.execute()
    checkpoint_file = checkpoint.save_checkpoint()
    checkpoint.print_summary()

    print(f"Checkpoint saved: {checkpoint_file}")

    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
