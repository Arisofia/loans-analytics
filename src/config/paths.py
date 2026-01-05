"""Centralized path management with environment-specific overrides."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """Get project root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "src").exists() and (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Project root not found")


def resolve_path(path_str: str, env_var: Optional[str] = None, create: bool = False) -> Path:
    """Resolve path with environment variable support."""
    if not path_str:
        raise ValueError("path_str cannot be empty")

    if env_var and env_var in os.environ:
        resolved = Path(os.environ[env_var]).expanduser()
    else:
        path_str = os.path.expandvars(path_str)
        if path_str.startswith("~"):
            resolved = Path(path_str).expanduser()
        elif path_str.startswith("./"):
            resolved = get_project_root() / path_str[2:]
        elif Path(path_str).is_absolute():
            resolved = Path(path_str)
        else:
            resolved = get_project_root() / path_str

    resolved = resolved.resolve()
    if create and not resolved.exists():
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


class Paths:
    """Centralized path configuration with environment overrides."""

    @staticmethod
    def raw_data_dir(create: bool = False) -> Path:
        return resolve_path(
            os.getenv("DATA_RAW_PATH", "./data/raw"), env_var="DATA_RAW_DIR", create=create
        )

    @staticmethod
    def data_dir(create: bool = False) -> Path:
        return resolve_path(os.getenv("DATA_PATH", "./data"), env_var="DATA_DIR", create=create)

    @staticmethod
    def scripts_dir() -> Path:
        return get_project_root() / "scripts"

    @staticmethod
    def metrics_dir(create: bool = False) -> Path:
        return resolve_path(
            os.getenv("DATA_METRICS_PATH", "./data/metrics"), env_var="METRICS_DIR", create=create
        )

    @staticmethod
    def config_file() -> Path:
        config_dir = os.getenv("CONFIG_PATH", "./config")
        return resolve_path(config_dir + "/pipeline.yml", env_var="CONFIG_FILE")

    @staticmethod
    def logs_dir(create: bool = False) -> Path:
        return resolve_path(os.getenv("LOGS_PATH", "./logs"), env_var="LOGS_DIR", create=create)

    @staticmethod
    def docs_dir() -> Path:
        return get_project_root() / "docs"

    @staticmethod
    def exports_dir(create: bool = False) -> Path:
        return resolve_path(
            os.getenv("EXPORTS_PATH", "./exports"), env_var="EXPORTS_DIR", create=create
        )

    @staticmethod
    def reports_dir(create: bool = False) -> Path:
        return resolve_path(
            os.getenv("REPORTS_PATH", "./reports"), env_var="REPORTS_DIR", create=create
        )

    @staticmethod
    def monitoring_logs_dir(create: bool = False) -> Path:
        logs_dir = Paths.logs_dir(create=create)
        monitoring_dir = logs_dir / "monitoring"
        if create:
            monitoring_dir.mkdir(parents=True, exist_ok=True)
        return monitoring_dir

    @staticmethod
    def runs_artifacts_dir(create: bool = False) -> Path:
        logs_dir = Paths.logs_dir(create=create)
        runs_dir = logs_dir / "runs"
        if create:
            runs_dir.mkdir(parents=True, exist_ok=True)
        return runs_dir

    @staticmethod
    def get_environment() -> str:
        return os.getenv("PYTHON_ENV", os.getenv("APP_ENV", "development"))
