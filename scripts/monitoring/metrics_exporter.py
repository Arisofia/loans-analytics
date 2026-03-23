import asyncio
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Optional
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.python.config import settings
from backend.python.supabase_pool import SupabaseConnectionPool

class MetricsRegistry:

    def __init__(self) -> None:
        self.metrics: Dict[str, float] = {}
        self._connection_pool: Optional[SupabaseConnectionPool] = None

    def register_counter(self, name: str, value: int, labels: Optional[Dict[str, str]]=None) -> None:
        label_str = self._format_labels(labels)
        metric_key = f'{name}{label_str}'
        self.metrics[metric_key] = self.metrics.get(metric_key, 0) + value

    def register_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]]=None) -> None:
        label_str = self._format_labels(labels)
        metric_key = f'{name}{label_str}'
        self.metrics[metric_key] = value

    def _format_labels(self, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return ''
        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return '{' + ','.join(label_pairs) + '}'

    async def collect_metrics(self) -> None:
        self.metrics.clear()
        await self._collect_pipeline_metrics()
        await self._collect_connection_pool_metrics()
        await self._collect_cache_metrics()
        await self._collect_kpi_metrics()

    async def _collect_pipeline_metrics(self) -> None:
        try:
            runs_dir = Path('logs/runs')
            if not runs_dir.exists():
                return
            run_dirs = sorted(runs_dir.glob('*'), reverse=True)
            if not run_dirs:
                return
            latest_run = run_dirs[0]
            result_file = latest_run / 'pipeline_results.json'
            if result_file.exists():
                with open(result_file) as f:
                    result = json.load(f)
                status = 'success' if result.get('status') == 'success' else 'error'
                status_val = 1 if status == 'success' else 0
                self.register_gauge('pipeline_last_run_status', status_val, {'status': status, 'run_id': latest_run.name})
                if 'duration_seconds' in result:
                    self.register_gauge('pipeline_duration_seconds', result['duration_seconds'], {'run_id': latest_run.name})
                for phase_name, phase_data in result.get('phases', {}).items():
                    phase_status = 'success' if phase_data.get('status') == 'success' else 'error'
                    self.register_counter('pipeline_phase_runs_total', 1, {'phase': phase_name, 'status': phase_status})
                    if 'duration_seconds' in phase_data:
                        self.register_gauge('pipeline_phase_duration_seconds', phase_data['duration_seconds'], {'phase': phase_name})
                if 'ingestion' in result.get('phases', {}):
                    rows = result['phases']['ingestion'].get('rows', 0)
                    self.register_gauge('fact_loans_row_count', rows)
        except Exception as e:
            print(f'Error collecting pipeline metrics: {e}')

    async def _collect_connection_pool_metrics(self) -> None:
        try:
            if not settings.supabase_pool.enabled:
                return
            if self._connection_pool is None:
                database_url = os.getenv('SUPABASE_DATABASE_URL') or os.getenv('DATABASE_URL')
                if not database_url:
                    return
                self._connection_pool = SupabaseConnectionPool(database_url, min_size=settings.supabase_pool.min_size, max_size=settings.supabase_pool.max_size)
                await self._connection_pool.initialize()
            metrics = self._connection_pool.get_metrics()
            total_conns = metrics.get('total_connections', 0)
            active_conns = metrics.get('active_connections', 0)
            self.register_gauge('connection_pool_size', total_conns, {'state': 'total'})
            self.register_gauge('connection_pool_size', active_conns, {'state': 'active'})
            self.register_gauge('connection_pool_size', total_conns - active_conns, {'state': 'idle'})
            self.register_counter('connection_pool_queries_total', metrics.get('queries_executed', 0))
            self.register_counter('connection_pool_failures_total', metrics.get('failed_connections', 0))
            health = await self._connection_pool.health_check()
            health_status = 1 if health.get('status') == 'healthy' else 0
            self.register_gauge('connection_pool_health_check', health_status)
        except Exception as e:
            print(f'Error collecting connection pool metrics: {e}')
            self.register_gauge('connection_pool_health_check', 0)

    async def _collect_cache_metrics(self) -> None:
        try:
            cache_file = Path('data/cache/idempotency_stats.json')
            if cache_file.exists():
                with open(cache_file) as f:
                    stats = json.load(f)
                self.register_counter('idempotency_cache_hits_total', stats.get('hits', 0))
                self.register_counter('idempotency_cache_misses_total', stats.get('misses', 0))
            else:
                self.register_counter('idempotency_cache_hits_total', 0)
                self.register_counter('idempotency_cache_misses_total', 0)
        except Exception as e:
            print(f'Error collecting cache metrics: {e}')

    async def _collect_kpi_metrics(self) -> None:
        try:
            runs_dir = Path('logs/runs')
            if not runs_dir.exists():
                return
            run_dirs = sorted(runs_dir.glob('*'), reverse=True)
            if not run_dirs:
                return
            latest_run = run_dirs[0]
            result_file = latest_run / 'pipeline_results.json'
            if result_file.exists():
                with open(result_file) as f:
                    result = json.load(f)
                calc_phase = result.get('phases', {}).get('calculation', {})
                kpi_results = calc_phase.get('kpi_results', {})
                for kpi_name, kpi_data in kpi_results.items():
                    status = 'success' if kpi_data.get('status') == 'success' else 'error'
                    self.register_counter('kpi_calculations_total', 1, {'kpi_name': kpi_name, 'status': status})
                    if status == 'error':
                        self.register_counter('kpi_calculation_failures_total', 1, {'kpi_name': kpi_name})
        except Exception as e:
            print(f'Error collecting KPI metrics: {e}')

    def render_prometheus_format(self) -> str:
        lines = ['# Abaco Loans Analytics Pipeline Metrics', f'# Generated: {datetime.now().isoformat()}', '']
        metric_groups: Dict[str, list] = {}
        for metric_key, value in self.metrics.items():
            metric_name = metric_key.split('{')[0] if '{' in metric_key else metric_key
            if metric_name not in metric_groups:
                metric_groups[metric_name] = []
            metric_groups[metric_name].append((metric_key, value))
        for metric_name, entries in sorted(metric_groups.items()):
            help_text = self._get_help_text(metric_name)
            lines.append(f'# HELP {metric_name} {help_text}')
            metric_type = 'counter' if 'total' in metric_name else 'gauge'
            lines.append(f'# TYPE {metric_name} {metric_type}')
            for metric_key, value in entries:
                lines.append(f'{metric_key} {value}')
            lines.append('')
        return '\n'.join(lines)

    def _get_help_text(self, metric_name: str) -> str:
        help_texts = {'pipeline_last_run_status': 'Status of the last pipeline run (1=success, 0=error)', 'pipeline_duration_seconds': 'Pipeline execution duration', 'pipeline_phase_runs_total': 'Total runs per pipeline phase', 'pipeline_phase_duration_seconds': 'Duration of each phase', 'fact_loans_row_count': 'Number of rows in fact_loans', 'connection_pool_size': 'Connection pool size by state', 'connection_pool_queries_total': 'Total pool queries', 'connection_pool_failures_total': 'Total pool failures', 'connection_pool_health_check': 'Pool health (1=ok, 0=bad)', 'idempotency_cache_hits_total': 'Total cache hits', 'idempotency_cache_misses_total': 'Total cache misses', 'kpi_calculations_total': 'Total KPI calculations by status', 'kpi_calculation_failures_total': 'Total KPI calc failures'}
        return help_texts.get(metric_name, f'Metric: {metric_name}')
registry = MetricsRegistry()

class MetricsHandler(BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        if self.path == '/metrics':
            asyncio.run(registry.collect_metrics())
            response = registry.render_prometheus_format()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(response.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, _format: str, *args: object) -> None:
        pass

def main() -> None:
    port = int(os.getenv('METRICS_PORT', '8000'))
    print('=' * 60)
    print('ABACO LOANS ANALYTICS - METRICS EXPORTER')
    print('=' * 60)
    print(f'Starting metrics server on port {port}')
    print(f'Metrics endpoint: http://localhost:{port}/metrics')
    print(f'Health check: http://localhost:{port}/health')
    print('')
    print('Prometheus scrape config:')
    print("  - job_name: 'abaco-pipeline'")
    print('    static_configs:')
    print(f"      - targets: ['localhost:{port}']")
    print('=' * 60)
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down metrics exporter...')
        server.shutdown()
if __name__ == '__main__':
    main()
