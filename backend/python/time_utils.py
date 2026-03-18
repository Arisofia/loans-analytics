"""Centralized time utilities for consistent timestamp handling across the application."""

from datetime import datetime, timezone
from typing import Optional


def get_utc_now() -> datetime:
    """
    Get current UTC time with timezone awareness.

    This replaces the deprecated datetime.utcnow() and ensures consistent
    timezone-aware timestamps across the application.

    Returns:
        Current UTC time as timezone-aware datetime

    Example:
        from backend.python.time_utils import get_utc_now
        current_time = get_utc_now()
    """
    return datetime.now(timezone.utc)


def get_iso_timestamp() -> str:
    """
    Get current UTC time as ISO 8601 formatted string.

    Returns:
        ISO 8601 formatted timestamp string (e.g., '2024-01-28T10:30:00+00:00')

    Example:
        from backend.python.time_utils import get_iso_timestamp
        timestamp = get_iso_timestamp()
    """
    return get_utc_now().isoformat()


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """
    Parse an ISO 8601 formatted timestamp string to datetime.

    Supports common ISO 8601 formats including timestamps with 'Z' suffix
    for UTC timezone (e.g., '2024-01-28T10:30:00Z').

    Args:
        timestamp_str: ISO 8601 formatted timestamp string

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If timestamp string is not valid ISO 8601 format

    Example:
        from backend.python.time_utils import parse_iso_timestamp
        dt = parse_iso_timestamp('2024-01-28T10:30:00+00:00')
        dt_utc = parse_iso_timestamp('2024-01-28T10:30:00Z')
    """
    # Handle 'Z' suffix for UTC timezone (common ISO 8601 format)
    # datetime.fromisoformat() doesn't support 'Z', so normalize to '+00:00'
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"
    return datetime.fromisoformat(timestamp_str)


def format_timestamp(dt: datetime, fmt: Optional[str] = None) -> str:
    """
    Format a datetime object to string.

    Args:
        dt: Datetime object to format
        fmt: Format string. If None, uses ISO 8601 format.

    Returns:
        Formatted timestamp string

    Example:
        from backend.python.time_utils import format_timestamp, get_utc_now
        formatted = format_timestamp(get_utc_now(), "%Y-%m-%d")
    """
    if fmt is None:
        return dt.isoformat()
    return dt.strftime(fmt)
