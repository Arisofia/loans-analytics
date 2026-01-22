import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default required secrets (can be modified by tests)
REQUIRED_SECRETS = {
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
}

OPTIONAL_SECRETS = {
    "AZURE_STORAGE_CONNECTION_STRING",
    "FIGMA_ACCESS_TOKEN",
    "NOTION_API_KEY",
}


class SecretsManager:
    def __init__(self, use_vault_fallback: bool = False):
        self.use_vault_fallback = use_vault_fallback
        self._secrets: Dict[str, str] = {}
        # Pre-load from env
        self._load_from_env()

    def _load_from_env(self):
        for key in REQUIRED_SECRETS | OPTIONAL_SECRETS:
            val = os.getenv(key)
            if val:
                self._secrets[key] = val

    def get(
        self, key: str, default: Optional[str] = None, required: bool = False
    ) -> Optional[str]:
        val = self._secrets.get(key) or os.getenv(key)
        if val is None and default is not None:
            return default

        if required and val is None:
            if self.use_vault_fallback:
                # TODO: Implement vault fallback
                pass
            raise ValueError(f"Required secret '{key}' is missing.")

        return val

    def get_all(self, required_only: bool = False) -> Dict[str, str]:
        keys = (
            REQUIRED_SECRETS if required_only else (REQUIRED_SECRETS | OPTIONAL_SECRETS)
        )
        result = {}
        for k in keys:
            val = self.get(k)
            if val:
                result[k] = val
        return result

    def validate(
        self,
        fail_on_missing_required: bool = False,
        fail_on_missing_optional: bool = False,
    ) -> Dict[str, Any]:
        missing_required = []
        missing_optional_dict = {}

        for k in REQUIRED_SECRETS:
            if self.get(k) is None:
                missing_required.append(k)

        for k in OPTIONAL_SECRETS:
            present = self.get(k) is not None
            missing_optional_dict[k] = not present

        if fail_on_missing_required and missing_required:
            raise ValueError(f"Missing required secrets: {', '.join(missing_required)}")

        # logic for 'status'
        if missing_required:
            status = "error"
        else:
            status = "ok"

        return {
            "status": status,
            "required_missing": missing_required,  # Renamed from 'missing' to match test
            "optional_missing": missing_optional_dict,
        }

    def log_status(self) -> None:
        validation = self.validate()

        # Log required
        for k in REQUIRED_SECRETS:
            present = k not in validation["required_missing"]
            logger.info(f"Secret '{k}': {'PRESENT' if present else 'MISSING'}")

        # Log optional
        for k, missing in validation["optional_missing"].items():
            logger.info(f"Secret '{k}': {'MISSING' if missing else 'PRESENT'}")


def get_secrets_manager(use_vault: bool = False) -> SecretsManager:
    return SecretsManager(use_vault_fallback=use_vault)
