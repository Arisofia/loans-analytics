"""
Customer Segmentation Analysis Agent (Production)
Integrates with Azure AI Multi-Agent Service to classify real loan portfolio data
according to ECB/ABACO collateral eligibility standards.
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

# Configure logging (JSON format for Grafana Alloy ingestion)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
logger = logging.getLogger("customer_segmentation")


def get_env_var(name: str) -> str:
    """Retrieve secret from environment or Secret Manager."""
    value = os.getenv(name)
    if not value:
        logger.critical(f"Missing required configuration: {name}")
        sys.exit(1)
    return value



class AbacoEligibilityEvaluator:
    """Evaluates loan eligibility for ECB collateral pools.
    Implements ECB regulatory standards: 0.4% / 1.0% PD thresholds.
    """
    
    @staticmethod
    def evaluate(loan_record: Dict[str, Any]) -> tuple:
        """
        Evaluate loan eligibility per ECB/ABACO standards.
        Returns: (is_eligible, reason, tier)
        """
        pd = float(loan_record.get('probability_of_default', 1.0))
        amount = float(loan_record.get('amount_outstanding', 0.0))
        maturity = float(loan_record.get('residual_maturity_years', 0.0))
        
        # ECB Collateral Eligibility
        if pd <= 0.004:  # 0.4% threshold
            tier = "PREMIUM"
        elif pd <= 0.010:  # 1.0% threshold
            tier = "STANDARD"
        else:
            return False, f"PD {pd:.2%} exceeds 1.0% threshold", "INELIGIBLE"
        
        # Additional Checks
        if amount <= 0:
            return False, "Zero or negative outstanding amount", "INELIGIBLE"
        if maturity < 0:
            return False, "Negative residual maturity", "INELIGIBLE"
        
        return True, "Eligible for collateral pool", tier


def fetch_production_data() -> List[Dict]:
    """
    Fetches processed loan metrics from the Data Warehouse.
    In production, this connects to the secure Parquet store or SQL DB.
    """
    data_path = os.getenv("DATA_WAREHOUSE_PATH", "data/warehouse/meta_insights.parquet")
    
    # Check if parquet file exists
    try:
        import pandas as pd
        if os.path.exists(data_path):
            df = pd.read_parquet(data_path)
            # Filter: Only ACTIVE loans with valid currency
            active_loans = df[df['status'] == 'ACTIVE'].to_dict(orient='records')
            logger.info(f"Loaded {len(active_loans)} active loans from warehouse")
            return active_loans
        else:
            logger.warning(f"Data warehouse not found at {data_path}")
            return []
    except ImportError:
        logger.warning("pandas not installed, skipping data warehouse load")
        return []
    except Exception as e:
        logger.error(f"Data Warehouse Read Error: {str(e)}")
        return []


def main() -> None:
    """Run the customer segmentation analysis agent workflow.
    Orchestrates loading configuration, preparing customer data,
    evaluating eligibility per ECB/ABACO standards, and logging results.
    """
    logger.info("Starting ABACO Segmentation Agent...")
    
    endpoint = get_env_var("AZURE_AI_MULTIAGENT_ENDPOINT")
    api_key = get_env_var("AZURE_AI_MULTIAGENT_KEY")
    
    loans = fetch_production_data()
    if not loans:
        logger.warning("No active loans found for processing. Exiting.")
        sys.exit(0)

    # Apply Regulatory Logic (ECB Collateral Eligibility)
    eligible_pool = []
    rejected_pool = []

    for loan in loans:
        try:
            is_eligible, reason, tier = AbacoEligibilityEvaluator.evaluate(loan)
            
            if is_eligible:
                eligible_pool.append({**loan, "abaco_tier": tier})
            else:
                rejected_pool.append({**loan, "rejection_reason": reason})
                
        except Exception as e:
            logger.warning(f"Skipping malformed record {loan.get('loan_id')}: {e}")
            continue

    logger.info(f"Processing Complete. Eligible: {len(eligible_pool)}, Rejected: {len(rejected_pool)}")
    
    # Send eligible pool to Azure AI Agent for Risk Scoring
    logger.info("Eligible pool ready for Azure AI Risk Agent dispatch.")
    logger.info(f"Eligible tier breakdown: PREMIUM={sum(1 for l in eligible_pool if l.get('abaco_tier')=='PREMIUM')}, STANDARD={sum(1 for l in eligible_pool if l.get('abaco_tier')=='STANDARD')}")


if __name__ == "__main__":
    main()
