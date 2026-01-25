#!/usr/bin/env python3
"""
Generate observability dashboard script.

This script generates an HTML observability dashboard from collected metrics.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _calculate_success_rate(metrics):
    """Calculate success rate from metrics."""
    pipeline = metrics.get('pipeline', {})
    total = pipeline.get('total_runs', 0)
    failed = pipeline.get('failed_runs', 0)
    
    if total == 0:
        return 0
    
    success_rate = ((total - failed) / total) * 100
    return round(success_rate, 1)


def generate_dashboard(pipeline_status=None, agent_status=None, quality_trend=None):
    """Generate observability dashboard HTML."""
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Load all metric files
    metrics_file = output_dir / "opik_metrics.json"
    if metrics_file.exists():
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
    else:
        metrics = {}
    
    # Calculate success rate before using it in HTML
    success_rate = _calculate_success_rate(metrics)
    
    # Generate HTML dashboard
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abaco Analytics - Observability Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .metric-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #0066cc;
        }}
        .metric-card.success {{
            border-left-color: #28a745;
        }}
        .metric-card.warning {{
            border-left-color: #ffc107;
        }}
        .metric-card.danger {{
            border-left-color: #dc3545;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-badge.healthy {{
            background: #d4edda;
            color: #155724;
        }}
        .status-badge.warning {{
            background: #fff3cd;
            color: #856404;
        }}
        .status-badge.critical {{
            background: #f8d7da;
            color: #721c24;
        }}
        .timestamp {{
            color: #999;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Abaco Analytics - Observability Dashboard</h1>
        <p class="timestamp">Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        
        <h2>System Status</h2>
        <div class="metrics-grid">
            <div class="metric-card success">
                <div class="metric-label">Pipeline Health</div>
                <div class="metric-value">{pipeline_status or 'healthy'}</div>
                <span class="status-badge healthy">{pipeline_status or 'healthy'}</span>
            </div>
            
            <div class="metric-card success">
                <div class="metric-label">Agent Performance</div>
                <div class="metric-value">{agent_status or 'optimal'}</div>
                <span class="status-badge healthy">{agent_status or 'optimal'}</span>
            </div>
            
            <div class="metric-card success">
                <div class="metric-label">Data Quality</div>
                <div class="metric-value">{quality_trend or 'stable'}</div>
                <span class="status-badge healthy">{quality_trend or 'stable'}</span>
            </div>
        </div>
        
        <h2>Pipeline Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Runs</div>
                <div class="metric-value">{metrics.get('pipeline', {}).get('total_runs', 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{success_rate}%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Avg Duration</div>
                <div class="metric-value">{metrics.get('pipeline', {}).get('average_duration_seconds', 0):.1f}s</div>
            </div>
        </div>
        
        <h2>Agent Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Executions</div>
                <div class="metric-value">{metrics.get('agents', {}).get('total_executions', 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Avg Response Time</div>
                <div class="metric-value">{metrics.get('agents', {}).get('average_response_time_ms', 0):.0f}ms</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Error Rate</div>
                <div class="metric-value">{metrics.get('agents', {}).get('error_rate', 0) * 100:.1f}%</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # Write dashboard
    dashboard_file = output_dir / "dashboard.html"
    with open(dashboard_file, "w") as f:
        f.write(html)
    
    logger.info(f"Dashboard generated: {dashboard_file}")
    return dashboard_file


if __name__ == "__main__":
    import sys
    
    try:
        # Parse command line arguments
        pipeline_status = None
        agent_status = None
        quality_trend = None
        
        for arg in sys.argv[1:]:
            if arg.startswith("--pipeline-status") and "=" in arg:
                value = arg.split("=", 1)[1]
                pipeline_status = value if value else None
            elif arg.startswith("--agent-status") and "=" in arg:
                value = arg.split("=", 1)[1]
                agent_status = value if value else None
            elif arg.startswith("--quality-trend") and "=" in arg:
                value = arg.split("=", 1)[1]
                quality_trend = value if value else None
        
        dashboard_file = generate_dashboard(pipeline_status, agent_status, quality_trend)
        print(f"✓ Dashboard generated: {dashboard_file}")
    except Exception as e:
        logger.error(f"Failed to generate dashboard: {e}")
        raise
