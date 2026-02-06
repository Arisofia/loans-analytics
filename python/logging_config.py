"""Centralized logging configuration for consistent logging across the application."""

import logging
import os
from typing import Optional

import sentry_sdk


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    This provides a single point for logger creation across the application,
    making it easier to maintain consistent logging configuration.

    Args:
        name: Logger name, typically __name__ from the calling module.
              If None, returns the root logger.

    Returns:
        Configured logger instance

    Example:
        from python.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    return logging.getLogger(name)


def configure_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    Configure logging format and level for the entire application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string. If None, uses default format.

    Raises:
        ValueError: If level is not a valid logging level

    Example:
        configure_logging(level="DEBUG")
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Validate logging level
    level_upper = level.upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level_upper not in valid_levels:
        raise ValueError(f"Invalid logging level: {level}. Must be one of {valid_levels}")

    logging.basicConfig(
        level=getattr(logging, level_upper), format=format_string, datefmt="%Y-%m-%d %H:%M:%S"
    )


def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def init_sentry(service_name: str) -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    send_default_pii = os.getenv("SENTRY_SEND_DEFAULT_PII", "false").lower() == "true"

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("ENVIRONMENT", "local"),
        release=os.getenv("SENTRY_RELEASE", f"{service_name}@dev"),
        send_default_pii=send_default_pii,
        traces_sample_rate=_get_float_env("SENTRY_TRACES_SAMPLE_RATE", 0.1),
        profiles_sample_rate=_get_float_env("SENTRY_PROFILES_SAMPLE_RATE", 0.0),
    )


def set_sentry_correlation(correlation_id: str) -> None:
    """Tag the current Sentry scope with a correlation_id.

    This links Sentry errors/transactions to operational events stored in
    monitoring.operational_events, enabling end-to-end traceability.
    """
    sentry_sdk.set_tag("correlation_id", correlation_id)
    sentry_sdk.set_context("monitoring", {"correlation_id": correlation_id})
