import json
import logging
import os
from typing import Any, Dict


def _load_business_constants() -> Dict[str, Any]:
    """Load business constants from the shared config file."""
    # Try different relative paths depending on where it is called from
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "config", "business_constants.json"),
        os.path.join(os.getcwd(), "config", "business_constants.json"),
    ]

    for config_path in possible_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Could not load business constants from {config_path}: {e}")

    logging.warning("Could not find business_constants.json in any expected location.")
    # Fallback to defaults if config is missing
    return {
        "delinquency": {
            "statuses": ["30-59 days past due", "60-89 days past due", "90+ days past due"],
            "thresholds": {
                "par30_warning": 5.0,
                "par30_critical": 8.0,
                "par90_warning": 3.0,
                "par90_critical": 5.0,
                "yield_warning": 8.0,
                "yield_critical": 6.0,
            },
        },
        "growth_projection": {
            "default_yield": 1.2,
            "yield_step": 0.15,
            "default_loan_base": 100,
            "loan_volume_step": 15,
            "projection_months": 6,
        },
    }


_BUSINESS_CONSTANTS = _load_business_constants()
DELINQUENT_STATUSES = _BUSINESS_CONSTANTS["delinquency"]["statuses"]
DELINQUENCY_THRESHOLDS = _BUSINESS_CONSTANTS["delinquency"]["thresholds"]
GROWTH_PROJECTION_PARAMS = _BUSINESS_CONSTANTS["growth_projection"]
