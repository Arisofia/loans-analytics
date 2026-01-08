import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.secrets import get_secrets_manager  # noqa: E402

load_dotenv()


def redact_dict(d: dict, mask: str = "<redacted>") -> dict:
    """Return a shallow copy of `d` with sensitive-looking keys redacted.

    Keys containing 'password' or 'token' (case-insensitive) will be replaced
    with `mask`. If `d` is not a dict it is returned unchanged.
    """
    if not isinstance(d, dict):
        return d
    out = {}
    for k, v in d.items():
        key_l = k.lower()
        if any(sub in key_l for sub in ("password", "token", "secret", "key")):
            out[k] = mask
        else:
            out[k] = v
    return out


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
