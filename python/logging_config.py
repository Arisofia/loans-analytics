"""Centralized logging configuration for consistent logging across the application."""

import logging
from typing import Optional


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
