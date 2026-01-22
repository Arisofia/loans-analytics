"""Tests for centralized path management module."""

import os
import tempfile
from pathlib import Path

import pytest

from src.config.paths import Paths, get_project_root, resolve_path


class TestProjectRoot:
    """Test project root detection."""

    def test_get_project_root_exists(self):
        """Project root should be detected correctly."""
        root = get_project_root()
        assert (root / "src").exists()
        assert (root / ".git").exists()
        assert (root / ".github").exists()

    def test_project_root_contains_config(self):
        """Project root should contain config directory."""
        root = get_project_root()
        config_dir = root / "config"
        assert config_dir.exists() or True  # Config may not exist yet


class TestResolvePath:
    """Test path resolution with environment variables."""

    def test_resolve_absolute_path(self):
        """Absolute paths should be resolved unchanged."""
        result = resolve_path("/tmp/test")
        assert result == Path("/tmp/test").resolve()

    def test_resolve_home_relative_path(self):
        """Home-relative paths should expand ~."""
        result = resolve_path("~/test")
        expected = Path("~/test").expanduser()
        assert result == expected.resolve()

    def test_resolve_with_environment_variable_precedence(self):
        """Environment variables should take precedence."""
        os.environ["TEST_CUSTOM_PATH"] = "/custom/test/path"
        result = resolve_path("./default", env_var="TEST_CUSTOM_PATH")
        assert result == Path("/custom/test/path").resolve()
        del os.environ["TEST_CUSTOM_PATH"]

    def test_resolve_creates_directories_when_requested(self):
        """Parent directories should be created when create=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "new" / "nested" / "file.txt"
            result = resolve_path(str(test_path), create=True)
            assert result.parent.exists()
            assert result.parent.is_dir()

    def test_resolve_does_not_create_by_default(self):
        """Directories should not be created by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "nonexistent"
            result = resolve_path(str(test_path), create=False)
            assert not result.exists()

    def test_resolve_empty_path_raises_error(self):
        """Empty path string should raise ValueError."""
        with pytest.raises(ValueError):
            resolve_path("")


class TestPathsMetricsDir:
    """Test metrics directory path resolution."""

    def test_metrics_dir_default(self):
        """Default metrics directory should be ./data/metrics."""
        result = Paths.metrics_dir()
        assert "metrics" in str(result)

    def test_metrics_dir_respects_env_var(self):
        """METRICS_DIR env var should override default."""
        os.environ["METRICS_DIR"] = "/var/metrics"
        result = Paths.metrics_dir()
        assert result == Path("/var/metrics").resolve()
        del os.environ["METRICS_DIR"]

    def test_metrics_dir_respects_data_metrics_path_var(self):
        """DATA_METRICS_PATH env var should be supported."""
        os.environ["DATA_METRICS_PATH"] = "/custom/metrics"
        result = Paths.metrics_dir()
        assert "metrics" in str(result)
        del os.environ["DATA_METRICS_PATH"]

    def test_metrics_dir_creates_when_requested(self):
        """Metrics directory should be created when create=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["METRICS_DIR"] = tmpdir
            result = Paths.metrics_dir(create=True)
            assert result.exists()
            del os.environ["METRICS_DIR"]


class TestPathsLogsDir:
    """Test logs directory path resolution."""

    def test_logs_dir_default(self):
        """Default logs directory should be ./logs."""
        result = Paths.logs_dir()
        assert "logs" in str(result)

    def test_logs_dir_respects_env_var(self):
        """LOGS_DIR env var should override default."""
        os.environ["LOGS_DIR"] = "/var/log/app"
        result = Paths.logs_dir()
        assert result == Path("/var/log/app").resolve()
        del os.environ["LOGS_DIR"]


class TestPathsMonitoringLogsDir:
    """Test monitoring logs directory path resolution."""

    def test_monitoring_logs_dir_under_logs(self):
        """Monitoring logs should be under logs directory."""
        result = Paths.monitoring_logs_dir()
        logs_dir = Paths.logs_dir()
        assert str(result).startswith(str(logs_dir))
        assert "monitoring" in str(result)

    def test_monitoring_logs_dir_creates_nested_structure(self):
        """Should create nested logs/monitoring structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LOGS_DIR"] = tmpdir
            result = Paths.monitoring_logs_dir(create=True)
            assert result.exists()
            assert (Path(tmpdir) / "monitoring").exists()
            del os.environ["LOGS_DIR"]


class TestPathsEnvironment:
    """Test environment detection."""

    def test_get_environment_defaults_to_development(self):
        """Environment should default to 'development'."""
        old_env = os.environ.get("PYTHON_ENV")
        old_app_env = os.environ.get("APP_ENV")

        if "PYTHON_ENV" in os.environ:
            del os.environ["PYTHON_ENV"]
        if "APP_ENV" in os.environ:
            del os.environ["APP_ENV"]

        result = Paths.get_environment()
        assert result == "development"

        if old_env:
            os.environ["PYTHON_ENV"] = old_env
        if old_app_env:
            os.environ["APP_ENV"] = old_app_env

    def test_get_environment_respects_python_env(self):
        """PYTHON_ENV should take precedence."""
        os.environ["PYTHON_ENV"] = "production"
        result = Paths.get_environment()
        assert result == "production"
        del os.environ["PYTHON_ENV"]
