"""Shared pipeline utilities."""

import traceback
from typing import Any, Dict


def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    Format exception into standardized error response.

    Args:
        error: Exception that occurred

    Returns:
        Dictionary with status, error message, and traceback
    """
    return {
        "status": "failed",
        "error": str(error),
        "traceback": traceback.format_exc(),
    }
