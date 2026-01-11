# Engineering Standards & Code Quality Guidelines

**Last Updated**: 2026-01-01  
**Version**: 1.0  
**Status**: Active

---

## Overview

This document establishes engineering standards for the ABACO Analytics platform,
ensuring code quality, maintainability, and consistency across the Python and
TypeScript codebase. All contributors must adhere to these standards to maintain
excellence in code integrity and operational reliability.

---

## Code Quality Metrics

### Current Status (Phase 4 Audit)

| Tool              | Score      | Status                     | Files Checked      |
| ----------------- | ---------- | -------------------------- | ------------------ |
| **pylint**        | 9.56/10    | ✅ Excellent                | 37 Python modules  |
| **ruff**          | 184 issues | ⚠️ Minor (58 auto-fixable)  | python/ + tests/   |
| **mypy**          | 5 errors   | ✅ Good (external libs)     | 37 Python modules  |
| **test coverage** | 162/169    | ✅ 95.9%                   | test suite         |

---

## Python Standards

### 1. Code Style & Formatting

**Tool**: Black + isort
**Config**: `pyproject.toml`

#### Line Length

- **Max**: 88 characters (Black default)
- **Exception**: SQL queries, long URLs, or domain-specific strings
  (document in comment)

```python
# Good: Proper line length
def validate_portfolio_metrics(
    total_receivable: float,
    eligible_amount: float,
    delinquent_bucket: Dict[str, float]
) -> Dict[str, float]:
    pass

# Avoid: Line too long
def validate_portfolio_metrics(total_receivable: float, eligible_amount: float, delinquent_bucket: Dict[str, float]) -> Dict[str, float]:
    pass
```

#### Imports

- **Order**: Standard library → Third-party → Local (enforced by isort)
- **Placement**: All imports at top of file (no import-outside-toplevel)
- **Exception**: Conditional imports for optional dependencies

```python
# Good: Standard library first, then third-party, then local
import os
import json
import logging

import pandas as pd
import numpy as np
from pydantic import BaseModel

from python.validation import validate_dataframe
from python.pipeline.utils import hash_file

# Avoid: Third-party before standard library
import pandas as pd
import os
import json
```

#### Formatting

- **Run before commit**: `black python tests`
- **Trailing whitespace**: Remove all (automatic with Black)
- **Blank lines**: 2 between top-level definitions, 1 within classes

### 2. Naming Conventions

| Element         | Convention          | Example                |
| --------------- | ------------------- | ---------------------- |
| Modules         | snake_case          | `kpi_engine_v2.py`     |
| Classes         | PascalCase          | `UnifiedIngestion`     |
| Functions       | snake_case          | `calculate_par_30()`   |
| Constants       | UPPER_SNAKE_CASE    | `MAX_RETRIES = 3`      |
| Private methods | _leading_underscore | `_validate_schema()`   |
| Type hints      | descriptive         | `config: Dict[str, Any]` |

### 3. Type Hints

**Requirement**: All public functions must have type hints
**Tool**: mypy (strict mode)

```python
# Good: Complete type hints
def ingest_file(
    self,
    file_path: Path,
    archive_dir: Optional[Path] = None
) -> IngestionResult:
    """Ingest and validate a CSV/Parquet/JSON file."""
    pass

# Avoid: Missing return type
def ingest_file(self, file_path: Path, archive_dir=None):
    pass
```

### 4. Docstrings

**Format**: Google-style docstrings
**Requirement**: All public classes and functions

```python
def calculate_par_90(
    df: pd.DataFrame,
    dpd_col: str = "dpd_90_plus_usd"
) -> Tuple[float, Dict[str, Any]]:
    """Calculate Portfolio-at-Risk (90+ days past due).
    
    Args:
        df: DataFrame with loan portfolio data
        dpd_col: Column name for 90+ DPD balances
        
    Returns:
        Tuple of (par_90_value, context_metadata)
        
    Raises:
        ValueError: If required columns are missing
        
    Example:
        >>> df = pd.read_csv("loans.csv")
        >>> par_90, ctx = calculate_par_90(df)
        >>> print(f"PAR90: {par_90:.2f}%")
    """
    pass
```

### 5. Error Handling

**Pattern**: Specific exceptions, informative messages

```python
# Good: Specific exception with context
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    raise FileNotFoundError(f"Input file not found: {file_path}")
except pd.errors.ParserError as e:
    raise ValueError(f"Failed to parse CSV at {file_path}: {e}")

# Avoid: Bare except or generic Exception
try:
    df = pd.read_csv(file_path)
except:
    print("Failed to read file")
```

### 6. Logging

**Requirements**:

- Use `logging` module, not print()
- Use lazy formatting (%s) not f-strings in log calls
- Log at appropriate level (DEBUG, INFO, WARNING, ERROR)

```python
# Good: Lazy formatting
logger.info("Ingestion complete: %d rows, %s checksum", row_count, checksum)
logger.warning("Validation failed for %d records", error_count)

# Avoid: f-string formatting in logger calls
logger.info(f"Ingestion complete: {row_count} rows")  # Evaluated even if not logged
```

### 7. Magic Numbers & Configuration

**Rule**: No magic numbers in code; use configuration or named constants

```python
# Good: Named constant with context
MAX_RETRIES = 3
BACKOFF_SECONDS = 1.0
RATE_LIMIT_RPS = 60

def configure_retry_policy(config: Dict[str, Any]) -> RetryPolicy:
    return RetryPolicy(
        max_retries=config.get("cascade", {}).get("http", {}).get("retry", {}).get("max_retries", MAX_RETRIES),
        backoff_seconds=config.get("cascade", {}).get("http", {}).get("retry", {}).get("backoff_seconds", BACKOFF_SECONDS),
    )

# Avoid: Magic numbers embedded in code
if attempt > 3:
    raise TimeoutError()
```

---

## Testing Standards

### 1. Test Organization

**Structure**:

```text
tests/
├── test_ingestion.py       # UnifiedIngestion tests
├── test_transformation.py   # UnifiedTransformation tests
├── test_pipeline.py         # Pipeline integration
├── test_pipeline_integration.py
├── test_kpi_engine.py       # KPI calculations
├── data_tests/              # Data contract tests
│   ├── test_kpi_contracts.py
│   └── test_kpi_stat_advanced.py
└── conftest.py              # Shared fixtures
```

### 2. Test Naming

- **Filename**: `test_<module>.py`
- **Function**: `test_<feature>()` - starts with "test_"
- **Clarity**: Name should describe what is being tested

```python
# Good: Clear test name
def test_ingest_csv_with_valid_data(tmp_path, minimal_config):
    """Test that valid CSV is ingested and validated."""
    pass

def test_ingest_csv_error_on_missing_file(minimal_config):
    """Test that FileNotFoundError is raised for missing input."""
    pass

# Avoid: Unclear or too broad
def test_ingest():
    pass

def test_it_works():
    pass
```

### 3. Fixtures & Configuration

**Location**: `tests/conftest.py`  
**Scope**: Function (default), Session (for expensive setup), or Module

```python
# Good: Reusable fixture with clear scope
@pytest.fixture
def minimal_config() -> Dict[str, Any]:
    """Minimal pipeline config for testing."""
    return {
        "pipeline": {
            "phases": {
                "ingestion": {...},
                "transformation": {...},
            }
        },
        "cascade": {...}
    }

# Usage in tests
def test_ingest_data(tmp_path, minimal_config):
    ingestion = UnifiedIngestion(minimal_config)
    pass
```

### 4. Assertions & Expectations

```python
# Good: Clear, specific assertions
assert result.df is not None
assert len(result.df) == expected_rows
assert result.df["total_receivable_usd"].sum() == pytest.approx(3000.0)
assert "run_id" in result.metadata
assert result.run_id.startswith("ingest_")

# Avoid: Vague or overly broad assertions
assert result  # What is being tested?
assert len(result.df) > 0  # Use specific values
```

### 5. Mock Usage

```python
# Good: Mock external dependencies, not core logic
@patch("scripts.run_data_pipeline.UnifiedPipeline")
def test_main_success(mock_pipeline_cls):
    mock_pipeline = mock_pipeline_cls.return_value
    mock_pipeline.execute.return_value = {"status": "success"}
    
    result = main(input_file="data/test.csv")
    assert result is True

# Avoid: Over-mocking or mocking behavior we want to test
@patch("python.pipeline.ingestion.UnifiedIngestion.ingest_file")
def test_ingest_data(mock_ingest):
    # This defeats the purpose of testing the actual ingestion logic
    pass
```

---

## Git & Version Control

### 1. Commit Messages

**Format**: `<type>: <subject>`

```text
PHASE 4: Fix test suite for config-aware UnifiedIngestion

- Updated 28 tests to use new config parameter
- Added minimal_config fixture to conftest.py
- All tests passing (162 passed, 15 unrelated failures)
```

**Types**:

- `PHASE X`: Major phase completion
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `test`: Test additions/updates
- `docs`: Documentation
- `style`: Formatting, linting

### 2. Branch Naming

- `refactor/pipeline-complexity` - Major refactoring
- `feat/config-consolidation` - Feature development
- `fix/test-suite-alignment` - Bug fixes

### 3. PR Standards

- **Title**: Clear, descriptive
- **Body**: Explain what, why, how
- **Tests**: All tests passing
- **Coverage**: Code changes should include tests

---

## Configuration Management

### 1. Environment-Aware Configuration

**Pattern**: Config loaded at startup, injected into classes

```python
# Good: Configuration passed via constructor
class UnifiedIngestion:
    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None):
        self.config = config.get("pipeline", {}).get("phases", {}).get("ingestion", {})

# Usage
config = load_config("config/pipeline.yml")
ingestion = UnifiedIngestion(config)

# Avoid: Global configuration or environment variables
class UnifiedIngestion:
    def __init__(self):
        self.config = os.getenv("PIPELINE_CONFIG")  # Not testable
```

### 2. Config Files

**Location**: `config/pipeline.yml` (main) + `config/environments/{env}.yml` (overrides)  
**Format**: YAML

---

## Documentation Standards

### 1. Module Docstrings

```python
"""Phase 2: Data transformation, normalization, and compliance masking.

This module provides the UnifiedTransformation class for standardizing,
validating, and masking sensitive data in loan portfolios before KPI
calculation.

Classes:
    TransformationResult: Container for transformation outputs and lineage
    UnifiedTransformation: Main transformation orchestrator

Example:
    >>> from python.pipeline.transformation import UnifiedTransformation
    >>> transformer = UnifiedTransformation(config)
    >>> result = transformer.transform(df)
"""
```

### 2. README Structure

```text
README.md
├── Title & Description
├── Quick Start (installation, usage)
├── Architecture
├── Configuration
├── Running Tests
├── Contributing
└── License
```

---

## Linting Exceptions & Rationale

### Documented Exceptions

| Code | Reason | Files | Action |
|------|--------|-------|--------|
| C0415 | Import outside toplevel (requests in ingest_http) | ingestion.py:228 | Intentional - conditional HTTP import |
| C0415 | Import outside toplevel (azure in output) | output.py:53-56 | Intentional - conditional Azure import |
| R0917 | Too many positional arguments | output.py:91, base.py:29 | Refactor in Phase 5 |
| W1203 | f-string in logging | prefect_orchestrator, data_validation_gx | Fix: use lazy formatting |
| E501 | Line too long | Multiple files | Auto-fix with ruff --fix |

### Auto-Fix Commands

```bash
# Format code with Black
black python tests

# Sort imports with isort
isort python tests

# Auto-fix ruff issues
python -m ruff check python tests --fix

# Remove trailing whitespace
python -m ruff check python --select=W291 --fix
```

---

## Development Workflow

### 1. Before Committing

```bash
# Format code
make format

# Lint check
make lint

# Type check
make type-check

# Run tests
make test

# Full quality audit
make audit-code
```

### 2. Code Review Checklist

- [ ] Code style consistent (Black, isort)
- [ ] Type hints complete (public APIs)
- [ ] Tests written and passing
- [ ] Docstrings present and accurate
- [ ] No hardcoded secrets or credentials
- [ ] Error handling is specific
- [ ] Logging is appropriate
- [ ] Configuration is injected, not hardcoded

---

## Performance & Scalability

### 1. Data Processing

**Best Practice**: Process in batches, not entire datasets in memory

```python
# Good: Chunk processing
chunk_size = 10000
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    process(chunk)

# Avoid: Load entire file
df = pd.read_csv(file_path)  # May fail on large files
```

### 2. Database Queries

**Best Practice**: Use pagination and filters

```python
# Good: Filtered query with pagination
query = "SELECT * FROM loans WHERE segment = 'Consumer' LIMIT 1000 OFFSET 0"

# Avoid: Full table scan
query = "SELECT * FROM loans"
```

---

## Security & Compliance

### 1. PII Protection

- All PII fields automatically masked in transformation
- Access logs record all data reads
- Compliance reports generated for each run

### 2. Secret Management

- Use environment variables or Azure Key Vault
- Never commit secrets to repository
- Rotate credentials regularly

### 3. Audit Trail

```python
# Every data operation logged with:
# - run_id (unique execution identifier)
# - timestamp (ISO 8601)
# - operation (ingest, transform, mask, etc.)
# - status (success/failure)
# - metadata (row counts, error details)
```

---

## Continuous Improvement

### Metrics Tracked

- Code quality score (pylint)
- Test coverage (pytest-cov)
- Build time (CI/CD)
- Deployment frequency (GitHub Actions)

### Phase 5 Roadmap

- [ ] Resolve remaining mypy errors (external lib stubs)
- [ ] Auto-fix all ruff line-length issues
- [ ] Reduce to 0 trailing whitespace issues
- [ ] Document all linting exceptions
- [ ] Create OPERATIONS.md (operational runbook)
- [ ] Create MIGRATION.md (migration guide)

---

## References

- [PEP 8 Style Guide](https://pep8.org/)
- [PEP 257 Docstring Conventions](https://peps.python.org/pep-0257/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [pytest Best Practices](https://docs.pytest.org/)
- [mypy Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet.html)

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-01 | Initial standards document based on Phase 4 audit |

**Maintainer**: Engineering Team  
**Last Reviewed**: 2026-01-01  
**Next Review**: 2026-02-01
