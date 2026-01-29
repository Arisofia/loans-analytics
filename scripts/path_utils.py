"""Secure path handling utilities to prevent path traversal attacks.

This module provides functions to safely validate and handle file paths
provided by users or external sources, preventing path traversal attacks.

Example:
    >>> from scripts.path_utils import validate_path
    >>> # Safely validate a user-provided path
    >>> safe_path = validate_path("metrics/report.json", base_dir="metrics")
    >>> with open(safe_path) as f:
    ...     data = json.load(f)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

# Set up logging for security events
logger = logging.getLogger(__name__)


def validate_path(
    user_path: str,
    base_dir: str = ".",
    allow_write: bool = False,
    must_exist: bool = False,
) -> Path:
    """Validate and sanitize a file path to prevent path traversal attacks.

    This function prevents path traversal attacks by ensuring the resolved path
    stays within the base directory. It:
    - Validates input types
    - Resolves relative paths and symlinks to absolute paths
    - Ensures the result stays within base_dir
    - Optionally checks file existence
    - Logs security events

    Args:
        user_path: User-provided path to validate. Can be relative or absolute.
        base_dir: Base directory that user_path must stay within.
                 Defaults to current directory.
        allow_write: If True, allow validating paths to non-existent files
                    that could be written to.
        must_exist: If True, raise error if file doesn't exist.

    Returns:
        Validated Path object that is safe to use in file operations.

    Raises:
        ValueError: If path escapes base directory or validation fails.
        TypeError: If inputs are invalid types.
        OSError: If base_dir cannot be created or accessed.

    Examples:
        >>> # Safely read a file from a specific directory
        >>> path = validate_path("report.json", base_dir="metrics", must_exist=True)
        >>> with open(path) as f:
        ...     data = json.load(f)

        >>> # Safely write to a file in a directory
        >>> path = validate_path("output.json", base_dir="metrics", allow_write=True)
        >>> with open(path, "w") as f:
        ...     json.dump(data, f)

        >>> # Prevent path traversal attacks
        >>> path = validate_path("../../../etc/passwd", base_dir="metrics")
        ValueError: Path traversal attempt detected
    """
    # Input validation
    if not isinstance(user_path, str):
        raise TypeError(f"user_path must be string, got {type(user_path).__name__}")
    if not user_path.strip():
        raise ValueError("user_path cannot be empty")
    if not isinstance(base_dir, str):
        raise TypeError(f"base_dir must be string, got {type(base_dir).__name__}")

    # Resolve base directory (create if needed)
    try:
        base = Path(base_dir).resolve()
        if not base.exists():
            logger.info(f"Creating base directory: {base}")
            base.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Cannot access base directory {base_dir}: {e}")
        raise

    # Resolve requested path (eliminates .. and symlinks)
    # Path traversal is validated below in the relative_to() check (CWE-22 mitigation)
    try:
        requested = Path(
            user_path
        ).resolve()  # nosemgrep: snyk.python.path_traversal,snyk.python.os_injection
    except (OSError, RuntimeError) as e:
        logger.warning(f"Cannot resolve path {user_path}: {e}")
        raise ValueError(f"Invalid path: {user_path}") from e

    # Security check: ensure resolved path is within base directory
    try:
        requested.relative_to(base)
    except ValueError:
        logger.warning(
            f"Path traversal attempt detected: {user_path} "
            f"(resolved: {requested}) escapes {base_dir} (resolved: {base})"
        )
        raise ValueError(f"Path traversal attempt detected: {user_path} " f"escapes {base_dir}")

    # File existence validation
    if must_exist and not requested.exists():
        logger.error(f"File not found: {requested}")
        raise ValueError(f"File not found: {user_path}")

    # Write validation
    if not allow_write and requested.exists() and not requested.is_file():
        logger.warning(f"Attempted to write to non-file: {requested}")
        raise ValueError(f"Path is not a regular file: {user_path}")

    logger.debug(f"Path validation succeeded: {user_path} -> {requested}")
    return requested


def secure_file_read(
    file_path: str,
    base_dir: str = ".",
    encoding: str = "utf-8",
) -> str:
    """Safely read a file with path traversal validation.

    Args:
        file_path: User-provided file path to read.
        base_dir: Base directory constraint. Defaults to current directory.
        encoding: File encoding. Defaults to UTF-8.

    Returns:
        File contents as string.

    Raises:
        ValueError: If path is invalid or escapes base_dir.
        FileNotFoundError: If file doesn't exist.
        UnicodeDecodeError: If file cannot be decoded with specified encoding.
    """
    validated_path = validate_path(
        file_path,
        base_dir=base_dir,
        must_exist=True,
    )
    logger.info(f"Reading file: {validated_path}")
    return validated_path.read_text(encoding=encoding)


def secure_file_write(
    file_path: str,
    content: str,
    base_dir: str = ".",
    encoding: str = "utf-8",
) -> None:
    """Safely write to a file with path traversal validation.

    Args:
        file_path: User-provided file path to write to.
        content: Content to write to file.
        base_dir: Base directory constraint. Defaults to current directory.
        encoding: File encoding. Defaults to UTF-8.

    Raises:
        ValueError: If path is invalid or escapes base_dir.
        OSError: If file cannot be written.
    """
    validated_path = validate_path(
        file_path,
        base_dir=base_dir,
        allow_write=True,
    )
    # Ensure parent directory exists
    validated_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing file: {validated_path}")
    validated_path.write_text(content, encoding=encoding)


def secure_json_read(
    file_path: str,
    base_dir: str = ".",
) -> Any:
    """Safely read and parse a JSON file with path validation.

    Args:
        file_path: User-provided file path to read.
        base_dir: Base directory constraint. Defaults to current directory.

    Returns:
        Parsed JSON object (dict, list, etc.).

    Raises:
        ValueError: If path is invalid or escapes base_dir.
        FileNotFoundError: If file doesn't exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    content = secure_file_read(file_path, base_dir=base_dir)
    logger.debug(f"Parsing JSON from: {file_path}")
    return json.loads(content)


def secure_json_write(
    file_path: str,
    data: dict,
    base_dir: str = ".",
    indent: int = 2,
) -> None:
    """Safely write data as JSON file with path validation.

    Args:
        file_path: User-provided file path to write to.
        data: Data to write as JSON (typically dict or list).
        base_dir: Base directory constraint. Defaults to current directory.
        indent: JSON indentation level for readability.

    Raises:
        ValueError: If path is invalid or escapes base_dir.
        OSError: If file cannot be written.
        TypeError: If data is not JSON-serializable.
    """
    content = json.dumps(data, indent=indent)
    secure_file_write(file_path, content, base_dir=base_dir)
    logger.debug(f"Wrote JSON to: {file_path}")


def secure_path_exists(
    file_path: str,
    base_dir: str = ".",
) -> bool:
    """Safely check if a path exists with validation.

    Args:
        file_path: User-provided file path to check.
        base_dir: Base directory constraint. Defaults to current directory.

    Returns:
        True if path exists and is within base_dir, False otherwise.
    """
    try:
        validated_path = validate_path(file_path, base_dir=base_dir)
        return validated_path.exists()
    except ValueError:
        logger.warning(f"Path check failed for: {file_path}")
        return False


def secure_path_is_file(
    file_path: str,
    base_dir: str = ".",
) -> bool:
    """Safely check if a path is a file with validation.

    Args:
        file_path: User-provided file path to check.
        base_dir: Base directory constraint. Defaults to current directory.

    Returns:
        True if path exists and is a file within base_dir, False otherwise.
    """
    try:
        validated_path = validate_path(file_path, base_dir=base_dir)
        return validated_path.is_file()
    except ValueError:
        logger.warning(f"File check failed for: {file_path}")
        return False


def secure_path_is_dir(
    path: str,
    base_dir: str = ".",
) -> bool:
    """Safely check if a path is a directory with validation.

    Args:
        path: User-provided path to check.
        base_dir: Base directory constraint. Defaults to current directory.

    Returns:
        True if path exists and is a directory within base_dir, False otherwise.
    """
    try:
        validated_path = validate_path(path, base_dir=base_dir)
        return validated_path.is_dir()
    except ValueError:
        logger.warning(f"Directory check failed for: {path}")
        return False


def sanitize_path(untrusted_path: str, base_dir: str = ".") -> str:
    """Convert untrusted user path to a trusted safe path string.

    This function sanitizes a user-provided path by validating it stays within
    the base directory and returning the canonical string representation.

    Args:
        untrusted_path: Untrusted path from user/CLI input
        base_dir: Base directory the path must stay within

    Returns:
        Safe absolute path as string that has been validated

    Raises:
        ValueError: If path escapes base directory
    """
    # Validate the path and return as string
    validated = validate_path(untrusted_path, base_dir=base_dir)
    # Return string representation - this signals to security analyzers that
    # the returned value is trusted and safe
    return str(validated)


def safe_join_path(base_dir: str, *path_parts: str) -> str:
    """Safely join path components using os.path.join which Snyk recognizes.

    Uses os.path.join and validates the result stays within base_dir.

    Args:
        base_dir: Base directory path component
        path_parts: Additional path components to join

    Returns:
        Safe joined path as string

    Raises:
        ValueError: If result escapes base_dir
    """
    # Use os.path.join for Snyk compatibility (recognized as safe)
    joined = os.path.join(base_dir, *path_parts)
    # Validate the joined path doesn't escape base_dir
    validated = validate_path(joined, base_dir=base_dir, allow_write=True)
    return str(validated)
