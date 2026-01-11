import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd

# Ensure we can import from the root and python directories
root_dir = str(Path(__file__).parent.parent.parent)
python_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, root_dir)
sys.path.insert(0, python_dir)

from pipeline.ingestion import UnifiedIngestion
from src.kpi_engine_v2 import KPIEngineV2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("abaco.v2_pipeline")

def run_v2_pipeline(input_file: str):
    logger.info("🚀 Starting Abaco V2 Operational Pipeline")
    
    # 1. Ingestion with Automated Data Quality Audit
    config = {
        "pipeline": {
            "phases": {
                "ingestion": {
                    "validation": {
                        "required_columns": ["loan_id", "total_receivable_usd", "measurement_date"],
                        "numeric_columns": ["total_receivable_usd"],
                        "date_columns": ["measurement_date"],
                        "strict": False
                    }
                }
            }
        }
    }
    
    ingestor = UnifiedIngestion(config)
    result = ingestor.ingest_file(Path(input_file))
    
    logger.info(f"✅ Ingestion complete. Row count: {len(result.df)}")
    
    # 2. Print Data Quality Report
    if result.quality_report:
        print("\n" + "="*40)
        print(result.quality_report.to_markdown())
        print("="*40 + "\n")
    
    # 3. KPI Engine V2 Calculation
    logger.info("📊 Calculating KPIs via Engine V2")
    engine = KPIEngineV2(result.df, actor="v2_pipeline_runner")
    metrics = engine.calculate_all()
    
    for name, data in metrics.items():
        val = data.get("value")
        status = "✅" if val is not None else "❌"
        print(f"{status} {name}: {val}")
        
    # 4. Export Audit Trail
    audit_df = engine.get_audit_trail()
    audit_path = Path("exports/kpi_audit_trail.csv")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(audit_path, index=False)
    logger.info(f"🔒 Audit trail exported to {audit_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Abaco V2 Operational Pipeline")
    parser.add_argument("--input", required=True, help="Path to input data file")
    args = parser.parse_args()
    
    try:
        run_v2_pipeline(args.input)
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        sys.exit(1)
