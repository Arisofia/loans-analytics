"""Logging configuration for the v2 pipeline scaffold.

Uses structlog when available; falls back to stdlib logging.
"""

from __future__ import annotations

import logging


def configure_logging(level: str | None = None) -> None:
    log_level = (level or "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))

    try:
        import structlog

        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level, logging.INFO)
            ),
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
    except Exception:
        # structlog is optional in this scaffold
        pass
