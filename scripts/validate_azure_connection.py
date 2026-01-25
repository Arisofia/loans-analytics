"""Validate Azure and Supabase connection and configuration.

This module provides utilities to test Azure Cosmos DB, Storage, and
Key Vault connectivity, plus Supabase API access, with proper error
handling and logging.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.secrets import get_secrets_manager

try:
    from src.azure_tracing import setup_azure_tracing

    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for validate_azure_connection")
except (ImportError, Exception) as tracing_err:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.warning("Azure tracing not initialized: %s", tracing_err)


def validate_all() -> bool:
    """Validate all critical configurations using SecretsManager."""
    manager = get_secrets_manager(use_vault=True)

    print("\n" + "=" * 60)
    print("VALIDATING SYSTEM CONNECTIVITY")
    print("=" * 60 + "\n")

    try:
        validation = manager.validate(fail_on_missing_required=True, fail_on_missing_optional=False)
        manager.log_status(include_optional=True)

        # Additional Azure specific checks if needed
        # ...

        return validation["status"] == "ok"
    except Exception as e:
        logger.error("Validation failed: %s", str(e))
        manager.log_status(include_optional=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    exit_code = 0 if validate_all() else 1
    sys.exit(exit_code)
