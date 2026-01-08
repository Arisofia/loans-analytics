
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.figma_client import FigmaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_facts_to_figma")

def main():
    dashboard_path = project_root / "exports" / "complete_kpi_dashboard.json"
    if not dashboard_path.exists():
        logger.error(f"Dashboard file not found: {dashboard_path}")
        sys.exit(1)
    
    with open(dashboard_path, "r") as f:
        dashboard = json.load(f)
    
    run_id = dashboard.get("run_id", "manual-sync")
    
    # Prepare data for FigmaClient.sync_batch_export
    # FigmaClient expects kpi_metrics for update_kpi_cards
    # and summary for create_dashboard_snapshot
    
    export_data = {
        "kpi_metrics": {
            "collection_rate": {"current_value": dashboard.get("collection_rate", 0) * 100, "status": "active"},
            "par_30": {"current_value": dashboard.get("delinquency_rate_30_pct", 0), "status": "active"},
            "par_90": {"current_value": dashboard.get("par_90_ratio_pct", 0), "status": "active"},
            "ltv": {"current_value": dashboard.get("ltv_cac_ratio", 0), "status": "active"},
        },
        "summary": {
            "active_clients": dashboard.get("active_clients"),
            "total_aum_usd": dashboard.get("total_aum_usd"),
            "monthly_revenue_usd": dashboard.get("monthly_revenue_usd"),
            "mom_growth_pct": dashboard.get("mom_growth_pct"),
            "timestamp": dashboard.get("timestamp")
        }
    }
    
    client = FigmaClient()
    if not client.api_token or not client.file_key:
        logger.error("FIGMA_TOKEN or FIGMA_FILE_KEY not set")
        sys.exit(1)
        
    logger.info(f"Starting Figma sync for run {run_id}...")
    results = client.sync_batch_export(export_data, run_id)
    
    if results.get("success"):
        logger.info("✅ Figma sync completed successfully")
        print(json.dumps(results, indent=2))
    else:
        logger.error(f"❌ Figma sync failed: {results.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
