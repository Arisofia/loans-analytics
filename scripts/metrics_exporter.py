"""
Prometheus metrics exporter for Abaco Loans Analytics Pipeline.

Exposes /metrics endpoint for Prometheus scraping with:
- Pipeline execution metrics
- KPI calculation success/failure rates
- Connection pool health
- Idempotency cache hits/misses

Usage:
    python scripts/metrics_exporter.py

Access metrics:
    curl http://localhost:8000/metrics
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.config import settings
from python.supabase_pool import SupabaseConnectionPool


class MetricsRegistry:
    """Central registry for all pipeline metrics."""

    def __init__(self):
        self.metrics: Dict[str, float] = {}
        self._last_pipeline_run = None
        self._connection_pool = None

    def register_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Register a gauge metric with optional labels."""
        label_str = self._format_labels(labels) if labels else ""
        metric_key = f"{name}{label_str}"
        self.metrics[metric_key] = value

    def register_counter(self, name: str, value: float, labels: Dict[str, str] = None):
        """Register a counter metric with optional labels."""
        label_str = self._format_labels(labels) if labels else ""
        metric_key = f"{name}{label_str}"
        self.metrics[metric_key] = value

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus text format."""
        if not labels:
            return ""
        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_pairs) + "}"

    async def collect_metrics(self):
        """Collect all metrics from various sources."""
        self.metrics.clear()

        # Pipeline execution metrics
        await self._collect_pipeline_metrics()

        # Connection pool metrics
        await self._collect_connection_pool_metrics()

        # Idempotency cache metrics
        await self._collect_cache_metrics()

        # KPI calculation metrics
        await self._collect_kpi_metrics()

    async def _collect_pipeline_metrics(self):
        """Collect metrics from pipeline execution logs."""
        try:
            # Find most recent pipeline run
            runs_dir = Path("data/runs")
            if not runs_dir.exists():
                return

            run_dirs = sorted(runs_dir.glob("*"), reverse=True)
            if not run_dirs:
                return

            latest_run = run_dirs[0]
            result_file = latest_run / "result.json"

            if result_file.exists():
                with open(result_file) as f:
                    result = json.load(f)

                # Pipeline run status
                status = "success" if result.get("status") == "success" else "error"
                self.register_counter(
                    "pipeline_runs_total", 1, {"status": status, "run_id": latest_run.name}
                )

                # Pipeline duration
                if "duration_seconds" in result:
                    self.register_gauge(
                        "pipeline_duration_seconds",
                        result["duration_seconds"],
                        {"run_id": latest_run.name},
                    )

                # Phase-level metrics
                for phase_name, phase_data in result.get("phases", {}).items():
                    phase_status = "success" if phase_data.get("status") == "success" else "error"
                    self.register_counter(
                        "pipeline_phase_runs_total",
                        1,
                        {"phase": phase_name, "status": phase_status},
                    )

                    if "duration_seconds" in phase_data:
                        self.register_gauge(
                            "pipeline_phase_duration_seconds",
                            phase_data["duration_seconds"],
                            {"phase": phase_name},
                        )

                # Data volume
                if "ingestion" in result.get("phases", {}):
                    rows = result["phases"]["ingestion"].get("rows", 0)
                    self.register_gauge("fact_loans_row_count", rows)

        except Exception as e:
            print(f"Error collecting pipeline metrics: {e}")

    async def _collect_connection_pool_metrics(self):
        """Collect metrics from Supabase connection pool."""
        try:
            if not settings.supabase_pool.enabled:
                return

            # Initialize pool if needed
            if self._connection_pool is None:
                database_url = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")
                if not database_url:
                    return

                self._connection_pool = SupabaseConnectionPool(
                    database_url,
                    min_size=settings.supabase_pool.min_size,
                    max_size=settings.supabase_pool.max_size,
                )
                await self._connection_pool.initialize()

            # Get pool metrics
            metrics = self._connection_pool.get_metrics()

            self.register_gauge(
                "connection_pool_size", metrics.get("total_connections", 0), {"state": "total"}
            )
            self.register_gauge(
                "connection_pool_size", metrics.get("active_connections", 0), {"state": "active"}
            )
            self.register_gauge(
                "connection_pool_size",
                metrics.get("total_connections", 0) - metrics.get("active_connections", 0),
                {"state": "idle"},
            )

            self.register_counter(
                "connection_pool_queries_total", metrics.get("queries_executed", 0)
            )
            self.register_counter(
                "connection_pool_failures_total", metrics.get("failed_connections", 0)
            )

            # Health check
            health = await self._connection_pool.health_check()
            health_status = 1 if health.get("status") == "healthy" else 0
            self.register_gauge("connection_pool_health_check", health_status)

        except Exception as e:
            print(f"Error collecting connection pool metrics: {e}")
            self.register_gauge("connection_pool_health_check", 0)

    async def _collect_cache_metrics(self):
        """Collect idempotency cache metrics from orchestrator logs."""
        try:
            # Parse orchestrator logs for cache hits/misses
            # This is a placeholder - implement based on actual logging
            cache_file = Path("data/cache/idempotency_stats.json")
            if cache_file.exists():
                with open(cache_file) as f:
                    stats = json.load(f)

                self.register_counter("idempotency_cache_hits_total", stats.get("hits", 0))
                self.register_counter("idempotency_cache_misses_total", stats.get("misses", 0))
            else:
                # Default values
                self.register_counter("idempotency_cache_hits_total", 0)
                self.register_counter("idempotency_cache_misses_total", 0)

        except Exception as e:
            print(f"Error collecting cache metrics: {e}")

    async def _collect_kpi_metrics(self):
        """Collect KPI calculation metrics from calculation phase logs."""
        try:
            # Find latest calculation logs
            runs_dir = Path("data/runs")
            if not runs_dir.exists():
                return

            run_dirs = sorted(runs_dir.glob("*"), reverse=True)
            if not run_dirs:
                return

            latest_run = run_dirs[0]
            result_file = latest_run / "result.json"

            if result_file.exists():
                with open(result_file) as f:
                    result = json.load(f)

                # KPI-level metrics from calculation phase
                calc_phase = result.get("phases", {}).get("calculation", {})
                kpi_results = calc_phase.get("kpi_results", {})

                for kpi_name, kpi_data in kpi_results.items():
                    status = "success" if kpi_data.get("status") == "success" else "error"

                    self.register_counter(
                        "kpi_calculations_total", 1, {"kpi_name": kpi_name, "status": status}
                    )

                    if status == "error":
                        self.register_counter(
                            "kpi_calculation_failures_total", 1, {"kpi_name": kpi_name}
                        )

        except Exception as e:
            print(f"Error collecting KPI metrics: {e}")

    def render_prometheus_format(self) -> str:
        """Render metrics in Prometheus text format."""
        lines = []
        lines.append("# Abaco Loans Analytics Pipeline Metrics")
        lines.append(f"# Generated: {datetime.now().isoformat()}")
        lines.append("")

        # Group metrics by name
        metric_groups = {}
        for metric_key, value in self.metrics.items():
            # Extract metric name (before labels)
            if "{" in metric_key:
                metric_name = metric_key.split("{")[0]
            else:
                metric_name = metric_key

            if metric_name not in metric_groups:
                metric_groups[metric_name] = []
            metric_groups[metric_name].append((metric_key, value))

        # Render each metric group
        for metric_name, entries in sorted(metric_groups.items()):
            # Add HELP text
            lines.append(f"# HELP {metric_name} {self._get_help_text(metric_name)}")

            # Add TYPE
            metric_type = "counter" if "total" in metric_name else "gauge"
            lines.append(f"# TYPE {metric_name} {metric_type}")

            # Add metric values
            for metric_key, value in entries:
                lines.append(f"{metric_key} {value}")

            lines.append("")

        return "\n".join(lines)

    def _get_help_text(self, metric_name: str) -> str:
        """Get help text for metric."""
        help_texts = {
            "pipeline_runs_total": "Total number of pipeline runs by status",
            "pipeline_duration_seconds": "Pipeline execution duration in seconds",
            "pipeline_phase_runs_total": "Total runs per pipeline phase",
            "pipeline_phase_duration_seconds": "Duration of each pipeline phase",
            "fact_loans_row_count": "Number of rows in fact_loans table",
            "connection_pool_size": "Connection pool size by state (total, active, idle)",
            "connection_pool_queries_total": "Total queries executed through connection pool",
            "connection_pool_failures_total": "Total connection pool failures",
            "connection_pool_health_check": "Connection pool health status (1=healthy, 0=unhealthy)",
            "idempotency_cache_hits_total": "Total idempotency cache hits",
            "idempotency_cache_misses_total": "Total idempotency cache misses",
            "kpi_calculations_total": "Total KPI calculations by status",
            "kpi_calculation_failures_total": "Total KPI calculation failures",
        }
        return help_texts.get(metric_name, f"Metric: {metric_name}")


# Global registry
registry = MetricsRegistry()


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/metrics":
            # Collect latest metrics
            asyncio.run(registry.collect_metrics())

            # Render response
            response = registry.render_prometheus_format()

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(response.encode())

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


def main():
    """Run metrics exporter server."""
    port = int(os.getenv("METRICS_PORT", "8000"))

    print("=" * 80)
    print("ABACO LOANS ANALYTICS - METRICS EXPORTER")
    print("=" * 80)
    print(f"Starting metrics server on port {port}")
    print(f"Metrics endpoint: http://localhost:{port}/metrics")
    print(f"Health check: http://localhost:{port}/health")
    print("")
    print("Prometheus scrape config:")
    print("  - job_name: 'abaco-pipeline'")
    print("    static_configs:")
    print(f"      - targets: ['localhost:{port}']")
    print("=" * 80)

    server = HTTPServer(("0.0.0.0", port), MetricsHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down metrics exporter...")
        server.shutdown()


if __name__ == "__main__":
    main()
