# Engineering Standards & Code Quality

This document outlines the engineering standards, code quality requirements, and best practices for the Abaco Loans Analytics project.

## 1. Code Style and Formatting

- **Auto-formatting**: Use `black` for code formatting and `isort` for import sorting.
- **Line Length**: Maximum line length is **100 characters** (consistent with project-level `pyproject.toml` or `Makefile` goals, although standard `black` is 88, we aim for < 100).
- **Indentation**: Use 4 spaces for Python.

### Commands

```bash
make format  # Runs black and isort
```

## 2. Static Analysis & Linting

We use a combination of tools to ensure code quality:

- **Pylint**: For deep static analysis and logical errors.
- **Flake8**: For PEP8 style enforcement.
- **Ruff**: For fast, comprehensive linting and quick fixes.

### Key Rules

- **No Unused Variables**: Always remove or underscore unused variables.
- **Lazy Logging**: Use `%s` formatting in logging calls (e.g., `logger.info("msg: %s", var)`) instead of f-strings to avoid unnecessary string interpolation if the log level is disabled.
- **Complexity**: Keep functions focused and avoid too many return statements or positional arguments.

### Commands

```bash
make lint  # Runs all linters
```

## 3. Type Checking

Type safety is enforced via **Mypy**. All new production code in `src/pipeline/` must be fully type-hinted.

### Rules

- **Explicit Annotations**: Annotate complex dictionaries and collections (e.g., `Dict[str, Any]`).
- **Optional Types**: Use `Optional[T]` for variables that can be `None`.
- **Strictness**: Aim for no `Any` where possible, though `Any` is permitted for complex dataframes or legacy integrations.

### Commands

```bash
make type-check
```

## 4. Documentation

- **Docstrings**: Use Google-style or standard Sphinx docstrings for all public classes and methods.
- **Clarity over Comments**: Prefer clean, self-documenting code. Only use comments to explain "why", not "what".

## 5. Testing

- **Framework**: `pytest`
- **Coverage**: Aim for > 80% coverage on core pipeline modules.
- **Parity**: KPI calculations must maintain parity between Python logic and SQL views (Supabase/PostgreSQL).

### Commands

```bash
make test
make test-cov
```

## 6. Continuous Improvement

- Run `make quality` before every commit to ensure all standards are met.
- Technical debt should be documented in `COMPREHENSIVE_DEBT_AUDIT.md`.

## 7. Linting Exceptions

| File | Warning | Rationale |
|------|---------|-----------|
| `src/pipeline/data_ingestion.py` | `W0101` (Unreachable code) | Pylint identifies `df_polars.to_pandas()` after `pl.read_excel()` as unreachable. This is likely due to the lack of optional dependencies for Excel in the linting environment, causing `read_excel` to be typed as always raising. |
| `src/analytics/kpi_catalog_processor.py` | Multiple | This is a legacy module scheduled for gradual replacement by the new pipeline. Style and complexity warnings are suppressed to focus on functional stability until it is fully deprecated in v2.0. |
| `src/agents/orchestrator.py` | `valid-type`, `misc` | SQLAlchemy's `declarative_base()` usage requires type ignores because Mypy has difficulty with the dynamically generated base class. |

---
*Last Updated: 2026-01-01*
