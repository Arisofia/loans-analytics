# Path Traversal Vulnerabilities - Fix Guide

## Overview

Snyk Code identified **12 Path Traversal vulnerabilities** in your Python scripts. These occur when unsanitized user input (command-line arguments) flows directly into file operations.

### What is Path Traversal?

An attacker could use relative path sequences like `../../../etc/passwd` to escape intended directories and access arbitrary files on the system.

**Example Vulnerable Code:**

```python
# DANGEROUS - allows path traversal
file_path = sys.argv[1]  # User provides: "../../../etc/passwd"
with open(file_path) as f:
    data = f.read()
```

**Secure Code:**

```python
# SAFE - validates path is within allowed directory
base_dir = Path("metrics")  # Only allow access here
requested_file = Path(sys.argv[1])
file_path = (base_dir / requested_file).resolve()

# Ensure resolved path is still within base_dir
if not str(file_path).startswith(str(base_dir.resolve())):
    raise ValueError("Path traversal attempt detected")
```

## Affected Files

| File                                        | Lines          | Issue Count |
| ------------------------------------------- | -------------- | ----------- |
| `scripts/store_metrics.py`                  | 22, 26, 39, 46 | 4           |
| `scripts/generate_performance_dashboard.py` | 57, 182, 183   | 3           |
| `scripts/compare_costs.py`                  | 48             | 1           |
| `scripts/compare_performance.py`            | 48             | 1           |
| `scripts/post_cost_comment.py`              | 23             | 1           |
| `scripts/post_performance_comment.py`       | 22             | 1           |
| `scripts/validate_agent_checklist.py`       | 25             | 1           |

## Solution: Secure Path Handling Utility

Create a reusable utility function in `scripts/path_utils.py`:

```python
"""Secure path handling utilities to prevent path traversal attacks."""

from pathlib import Path
from typing import Optional


def validate_path(
    user_path: str,
    base_dir: str = ".",
    allow_write: bool = False,
    must_exist: bool = False,
) -> Path:
    """Validate and sanitize a file path.

    Prevents path traversal attacks by ensuring the resolved path
    stays within the base directory.

    Args:
        user_path: User-provided path to validate
        base_dir: Base directory that user_path must stay within
        allow_write: If True, allow writing to non-existent files
        must_exist: If True, raise error if file doesn't exist

    Returns:
        Validated Path object

    Raises:
        ValueError: If path escapes base directory or file doesn't exist
        TypeError: If inputs are invalid
    """
    if not isinstance(user_path, str):
        raise TypeError(f"user_path must be string, got {type(user_path)}")
    if not user_path.strip():
        raise ValueError("user_path cannot be empty")

    # Resolve base directory
    base = Path(base_dir).resolve()
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)

    # Resolve requested path (eliminates .. and symlinks)
    requested = Path(user_path).resolve()

    # Security check: ensure resolved path is within base
    try:
        requested.relative_to(base)
    except ValueError:
        raise ValueError(
            f"Path traversal attempt detected: {user_path} escapes {base_dir}"
        )

    # Existence checks
    if must_exist and not requested.exists():
        raise ValueError(f"File not found: {requested}")

    if not allow_write and requested.exists() and requested.is_dir():
        raise ValueError(f"Cannot write to directory: {requested}")

    return requested


def secure_file_read(
    file_path: str,
    base_dir: str = ".",
    encoding: str = "utf-8",
) -> str:
    """Safely read a file with path validation.

    Args:
        file_path: User-provided file path
        base_dir: Base directory constraint
        encoding: File encoding (default UTF-8)

    Returns:
        File contents as string
    """
    validated_path = validate_path(
        file_path, base_dir=base_dir, must_exist=True
    )
    return validated_path.read_text(encoding=encoding)


def secure_file_write(
    file_path: str,
    content: str,
    base_dir: str = ".",
    encoding: str = "utf-8",
) -> None:
    """Safely write to a file with path validation.

    Args:
        file_path: User-provided file path
        content: Content to write
        base_dir: Base directory constraint
        encoding: File encoding (default UTF-8)
    """
    validated_path = validate_path(
        file_path, base_dir=base_dir, allow_write=True
    )
    validated_path.parent.mkdir(parents=True, exist_ok=True)
    validated_path.write_text(content, encoding=encoding)


def secure_json_read(
    file_path: str,
    base_dir: str = ".",
):
    """Safely read JSON file with path validation.

    Args:
        file_path: User-provided file path
        base_dir: Base directory constraint

    Returns:
        Parsed JSON object
    """
    import json

    content = secure_file_read(file_path, base_dir=base_dir)
    return json.loads(content)


def secure_json_write(
    file_path: str,
    data: dict,
    base_dir: str = ".",
) -> None:
    """Safely write JSON file with path validation.

    Args:
        file_path: User-provided file path
        data: Data to write as JSON
        base_dir: Base directory constraint
    """
    import json

    content = json.dumps(data, indent=2)
    secure_file_write(file_path, content, base_dir=base_dir)
```

## Fix Instructions by Script

### 1. `scripts/store_metrics.py`

**Lines to Fix**: 22, 26, 39, 46

```python
from scripts.path_utils import validate_path
import json
from pathlib import Path

# Instead of:
# with open(metrics_file) as f:  # UNSAFE
# with open(output_file, "w") as f:  # UNSAFE

# Use:
def store_metrics(metrics_file: str, storage_dir: str = "metrics/history") -> None:
    """Store metrics with timestamp for historical tracking."""

    # Validate input file
    validated_metrics = validate_path(
        metrics_file,
        base_dir="metrics",  # Only allow files from metrics/
        must_exist=True
    )

    with open(validated_metrics) as f:
        metrics = json.load(f)

    # Validate storage directory
    storage_path = validate_path(
        storage_dir,
        base_dir="metrics",
        allow_write=True
    )
    storage_path.mkdir(parents=True, exist_ok=True)

    # Rest of function with validated paths
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = storage_path / f"metrics_{timestamp}.json"

    metrics["stored_at"] = datetime.utcnow().isoformat()
    metrics["source_file"] = str(validated_metrics)

    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2)

    # ... rest of function
```

### 2. `scripts/generate_performance_dashboard.py`

**Lines to Fix**: 57, 182, 183

Similar pattern - validate report file path before using:

```python
from scripts.path_utils import validate_path

# For reading reports:
validated_report = validate_path(
    report_file,
    base_dir=".",  # or appropriate base directory
    must_exist=True
)

# For writing output:
validated_output = validate_path(
    output_file,
    base_dir=".",
    allow_write=True
)
```

### 3. `scripts/compare_costs.py` & `scripts/compare_performance.py`

**Lines**: 48 each

```python
from scripts.path_utils import validate_path

# Instead of: with open(report_file) as f:
validated_report = validate_path(
    report_file,
    base_dir=".",
    must_exist=True
)
with open(validated_report) as f:
    report = json.load(f)
```

### 4. `scripts/post_cost_comment.py` & `scripts/post_performance_comment.py`

**Lines**: 23, 22

```python
from scripts.path_utils import validate_path

validated_file = validate_path(
    file_path,
    base_dir=".",
    must_exist=True
)
```

### 5. `scripts/validate_agent_checklist.py`

**Line**: 25

```python
from scripts.path_utils import validate_path

validated_config = validate_path(
    config_file,
    base_dir=".",
    must_exist=True
)
```

## Testing the Fix

After implementing, verify with:

```bash
# Test vulnerable paths are blocked
python scripts/store_metrics.py ../../../etc/passwd  # Should fail

# Test legitimate paths work
python scripts/store_metrics.py metrics/current.json  # Should work

# Verify Snyk Code passes
snyk code test
```

## Best Practices

1. **Always validate user paths** before file operations
2. **Use absolute paths** after validation (`.resolve()`)
3. **Whitelist base directories** - don't trust arbitrary paths
4. **Test with malicious input** (`../`, `../../`, symlinks)
5. **Log security violations** for monitoring
6. **Document constraints** in function docstrings

## Severity Assessment

| Risk                   | Impact | Likelihood |
| ---------------------- | ------ | ---------- |
| Arbitrary file read    | High   | Medium     |
| Arbitrary file write   | High   | Medium     |
| Information disclosure | High   | High       |
| System compromise      | Low    | Low        |

**Current Risk**: MEDIUM (12 vulnerabilities)  
**After Fix**: LOW (properly validated paths)

## References

- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- CWE-22: https://cwe.mitre.org/data/definitions/22.html
- Python pathlib security: https://docs.python.org/3/library/pathlib.html

---

**Status**: Ready to implement  
**Effort**: Low (reusable utility handles all cases)  
**Risk**: None (improves security)
