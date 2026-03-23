from __future__ import annotations
import argparse
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
from backend.python.kpis.strategic_reporting import build_strategic_summary, load_dashboard_metrics, write_strategic_report

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default='reports/strategic', help='Directory where report files will be written.')
    parser.add_argument('--streamlit-local', default='http://localhost:8501', help='Local Streamlit dashboard URL.')
    parser.add_argument('--grafana-local', default='http://localhost:3001/dashboards', help='Local Grafana dashboards URL.')
    parser.add_argument('--streamlit-prod', default='', help='Deployed Streamlit dashboard URL (set explicitly for production reports).')
    parser.add_argument('--dashboard-docs', default='docs/analytics/dashboards.md', help='Path or URL to dashboard documentation.')
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    metrics = load_dashboard_metrics(REPO_ROOT)
    summary = build_strategic_summary(metrics)
    links = {'streamlit_local': args.streamlit_local, 'grafana_local': args.grafana_local, 'streamlit_prod': args.streamlit_prod, 'dashboard_docs': args.dashboard_docs}
    output_dir = REPO_ROOT / args.output_dir
    json_path, md_path = write_strategic_report(summary, links, output_dir)
    print(f'Strategic report JSON: {json_path}')
    print(f'Strategic report MD:   {md_path}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
