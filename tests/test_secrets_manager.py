"""Tests for unified secrets management module."""

import os

import pytest

from src.config.secrets import SecretsManager, get_secrets_manager


class TestSecretsManagerGet:
    """Test getting individual secrets."""

    def test_get_existing_secret(self):
        """Should return value for existing env var."""
        os.environ["TEST_SECRET"] = "test_value"
        manager = SecretsManager()
        result = manager.get("TEST_SECRET")
        assert result == "test_value"
        del os.environ["TEST_SECRET"]

    def test_get_nonexistent_secret_returns_none(self):
        """Should return None for missing optional secret."""
        manager = SecretsManager()
        result = manager.get("NONEXISTENT_SECRET")
        assert result is None

    def test_get_required_missing_secret_raises_error(self):
        """Should raise error for missing required secret."""
        manager = SecretsManager()
        with pytest.raises(ValueError, match="Required secret"):
            manager.get("NONEXISTENT_SECRET", required=True)

    def test_get_with_default_value(self):
        """Should return default value for missing secret."""
        manager = SecretsManager()
        result = manager.get("NONEXISTENT_SECRET", default="default_value")
        assert result == "default_value"


class TestSecretsManagerValidate:
    """Test secrets validation."""

    def test_validate_required_only_missing(self):
        """Should report missing required secrets."""
        # Temporarily unset known secrets from .env
        old_openai = os.environ.pop("OPENAI_API_KEY", None)
        old_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)

        try:
            manager = SecretsManager()
            result = manager.validate(fail_on_missing_required=False)

            assert result["status"] == "error"
            assert len(result["required_missing"]) > 0
            assert "OPENAI_API_KEY" in result["required_missing"]
        finally:
            if old_openai:
                os.environ["OPENAI_API_KEY"] = old_openai
            if old_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = old_anthropic

    def test_validate_with_all_required_set(self):
        """Should pass validation when all required secrets set."""
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        manager = SecretsManager()
        result = manager.validate(fail_on_missing_required=False)

        assert result["status"] == "ok"
        assert result["required_missing"] == []

        del os.environ["OPENAI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]

    def test_validate_raises_on_missing_required(self):
        """Should raise error when required secret missing."""
        manager = SecretsManager()
        with pytest.raises(ValueError, match="Missing required secrets"):
            manager.validate(fail_on_missing_required=True)

    def test_validate_optional_keys(self):
        """Should track optional secrets separately."""
        manager = SecretsManager()
        result = manager.validate(fail_on_missing_required=False, fail_on_missing_optional=False)

        assert "optional_missing" in result
        assert len(result["optional_missing"]) >= 0


class TestSecretsManagerGetAll:
    """Test getting all secrets."""

    def test_get_all_required_only(self):
        """Should return dict of required secrets."""
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        manager = SecretsManager()
        result = manager.get_all(required_only=True)

        assert isinstance(result, dict)
        assert "OPENAI_API_KEY" in result
        assert "ANTHROPIC_API_KEY" in result
        assert result["OPENAI_API_KEY"] == "test-openai-key"

        del os.environ["OPENAI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]

    def test_get_all_includes_optional(self):
        """Should include optional keys when requested."""
        manager = SecretsManager()
        result = manager.get_all(required_only=False)

        assert isinstance(result, dict)
        assert len(result) > 0


class TestSecretsManagerFactory:
    """Test factory function."""

    def test_get_secrets_manager_default(self):
        """Should create manager without vault fallback by default."""
        manager = get_secrets_manager()
        assert isinstance(manager, SecretsManager)
        assert not manager.use_vault_fallback

    def test_get_secrets_manager_with_vault(self):
        """Should create manager with vault fallback when requested."""
        manager = get_secrets_manager(use_vault=True)
        assert isinstance(manager, SecretsManager)
        assert manager.use_vault_fallback


class TestSecretsManagerLogging:
    """Test logging functionality."""

    def test_log_status_does_not_expose_values(self, capsys):
        """Log output should not contain actual secret values."""
        os.environ["OPENAI_API_KEY"] = "test-secret-value-not-exposed"

        manager = SecretsManager()
        manager.get("OPENAI_API_KEY")
        manager.log_status()

        captured = capsys.readouterr()
        assert "test-secret" not in captured.out
        assert "OPENAI_API_KEY" in captured.out

        del os.environ["OPENAI_API_KEY"]
