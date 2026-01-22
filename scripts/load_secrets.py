import logging
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("abaco.scripts.load_secrets")


def redact_dict(
    d: Dict[str, Any],
    redact_keys: tuple = ("secret", "token", "password", "key"),
) -> Dict[str, Any]:
    redacted = {}

    for k, v in d.items():
        if any(sub in k.lower() for sub in redact_keys):
            redacted[k] = "<redacted>"
        else:
            # keep non-sensitive values
            redacted[k] = v
    return redacted


def load_secrets(use_vault_fallback: bool = True) -> dict:
    """Load and validate secrets from environment or Azure Key Vault.

    Args:
        use_vault_fallback: If True, use Azure Key Vault as fallback for missing secrets

    Returns:
        Dict with validation results
    """
    manager = get_secrets_manager(use_vault=use_vault_fallback)

    print("\n" + "=" * 60)
    print("LOADING SECRETS")
    print("=" * 60 + "\n")

    # Validate all secrets
    try:
        validation = manager.validate(fail_on_missing_required=True, fail_on_missing_optional=False)
        manager.log_status(include_optional=True)
        return validation
    except ValueError as e:
        print(f"⚠️  Validation failed: {e}")
        print("\nAttempting to load available secrets...")
        manager.log_status(include_optional=True)
        return {"status": "partial", "error": str(e)}


if __name__ == "__main__":
    results = load_secrets(use_vault_fallback=True)
    print(f"\nResult: {results.get('status', 'unknown')}")
    if results.get("error"):
        print(f"Error: {results['error']}")
    exit(0 if results.get("status") == "ok" else 1)
