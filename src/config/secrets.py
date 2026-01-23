"""Unified secrets management with validation and optional Azure Key Vault fallback."""

import os
from typing import Any, Dict, Optional


class SecretsManager:
    """Unified secrets access with validation.

    Supports:
    - Environment variables (primary)
    - Optional Azure Key Vault fallback (legacy)
    - Required/optional validation
    - Safe logging (masks values)
    """

    REQUIRED_KEYS = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ]

    OPTIONAL_KEYS = [
        "GEMINI_API_KEY",
        "PERPLEXITY_API_KEY",
        "XAI_API_KEY",
        "HUBSPOT_API_KEY",
        "HUBSPOT_PORTAL_ID",
        "CASCADE_TOKEN",
        "SLACK_WEBHOOK_OPS",
        "SLACK_WEBHOOK_LEADERSHIP",
        "SLACK_BOT_TOKEN",
        "OPIK_TOKEN",
        "PHOENIX_TOKEN",
        "FIGMA_TOKEN",
        "FIGMA_FILE_KEY",
        "CASCADE_TOKEN",
    ]

    AZURE_KEYS = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_KEY_VAULT_NAME",
    ]

    def __init__(self, use_vault_fallback: bool = False):
        """Initialize secrets manager.

        Args:
            use_vault_fallback: If True, attempt Azure Key Vault fallback for missing secrets
        """
        self.use_vault_fallback = use_vault_fallback
        self._vault_client = None
        self._cache: Dict[str, str] = {}
        self._status: Dict[str, str] = {}

        if use_vault_fallback:
            self._init_vault_client()

    def _init_vault_client(self):
        """Initialize Azure Key Vault client (lazy load)."""
        try:
            from azure.identity import ClientSecretCredential
            from azure.keyvault.secrets import SecretClient

            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            vault_name = os.getenv("AZURE_KEY_VAULT_NAME")

            if all([tenant_id, client_id, client_secret, vault_name]):
                vault_url = f"https://{vault_name}.vault.azure.net"
                credential = ClientSecretCredential(
                    tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
                )
                self._vault_client = SecretClient(vault_url=vault_url, credential=credential)
        except Exception as e:
            print(f"⚠️  Azure Key Vault initialization failed: {e}")
            self._vault_client = None

    def get(self, key: str, required: bool = False, default: Optional[str] = None) -> Optional[str]:
        """Get a secret with optional validation.

        Args:
            key: Secret name
            required: If True, raise error if not found
            default: Default value if not found and not required

        Returns:
            Secret value or default

        Raises:
            ValueError: If required and not found
        """
        if key in self._cache:
            return self._cache[key]

        value = os.getenv(key)

        if value:
            self._cache[key] = value
            self._status[key] = "✅"
            return value

        if self.use_vault_fallback and self._vault_client:
            try:
                secret = self._vault_client.get_secret(key)
                if secret and secret.value:
                    self._cache[key] = secret.value
                    self._status[key] = "✅ (vault)"
                    return secret.value
            except Exception:
                pass

        self._status[key] = "❌"

        if required:
            raise ValueError(f"Required secret '{key}' not found in environment or Key Vault")

        return default

    def get_all(self, required_only: bool = False) -> Dict[str, Optional[str]]:
        """Get all secrets (returns dict, values masked for logging).

        Args:
            required_only: If True, return only required keys

        Returns:
            Dict of key: value pairs
        """
        keys = self.REQUIRED_KEYS if required_only else (self.REQUIRED_KEYS + self.OPTIONAL_KEYS)
        return {key: self.get(key, required=required_only) for key in keys}

    def validate(
        self, fail_on_missing_optional: bool = False, fail_on_missing_required: bool = True
    ) -> Dict[str, Any]:
        """Validate all secrets are available.

        Args:
            fail_on_missing_optional: If True, raise on missing optional keys
            fail_on_missing_required: If True, raise on missing required keys

        Returns:
            Dict with validation status (ok if all required found, error if any missing)

        Raises:
            ValueError: If validation fails per fail_on_* parameters
        """
        missing_required = []
        missing_optional = []

        for key in self.REQUIRED_KEYS:
            if not self.get(key):
                missing_required.append(key)

        for key in self.OPTIONAL_KEYS:
            if not self.get(key):
                missing_optional.append(key)

        if fail_on_missing_required and missing_required:
            raise ValueError(f"Missing required secrets: {', '.join(missing_required)}")

        if fail_on_missing_optional and missing_optional:
            raise ValueError(f"Missing optional secrets: {', '.join(missing_optional)}")

        status = "error" if missing_required else "ok"
        return {
            "status": status,
            "required_missing": missing_required,
            "optional_missing": missing_optional,
            "required_found": len(self.REQUIRED_KEYS) - len(missing_required),
            "optional_found": len(self.OPTIONAL_KEYS) - len(missing_optional),
        }

    def log_status(self, include_optional: bool = False):
        """Log secrets validation status (values masked).

        Args:
            include_optional: If True, include optional keys in output
        """
        keys = self.REQUIRED_KEYS
        if include_optional:
            keys = keys + self.OPTIONAL_KEYS

        print("\n" + "=" * 60)
        print("SECRETS VALIDATION STATUS")
        print("=" * 60)

        for key in keys:
            status = self._status.get(key, "?")
            print(f"  {key:.<40} {status}")

        print("=" * 60 + "\n")


def get_secrets_manager(use_vault: bool = False) -> SecretsManager:
    """Factory function to get SecretsManager instance.

    Args:
        use_vault: Enable Azure Key Vault fallback

    Returns:
        SecretsManager instance
    """
    return SecretsManager(use_vault_fallback=use_vault)


__all__ = ["SecretsManager", "get_secrets_manager"]
