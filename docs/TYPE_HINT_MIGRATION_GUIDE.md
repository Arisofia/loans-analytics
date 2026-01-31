# Python 3.10+ Type Hint Migration Guide

**Target Audience**: Abaco Development Team  
**Migration Date**: January 31, 2026  
**Python Version**: 3.10+ Required

---

## Overview

This guide helps developers understand and adopt the new Python 3.10+ type hint syntax used throughout the codebase.

---

## Quick Reference

### Before (Python 3.9-)

```python
from typing import Dict, List, Optional, Set, Tuple, Any

def process_loans(
    loans: List[Dict[str, Any]],
    config: Optional[Dict[str, str]] = None
) -> Tuple[List[str], Dict[str, int]]:
    loan_ids: List[str] = []
    stats: Dict[str, int] = {}
    return loan_ids, stats
```

### After (Python 3.10+)

```python
from typing import Any

def process_loans(
    loans: list[dict[str, Any]],
    config: dict[str, str] | None = None
) -> tuple[list[str], dict[str, int]]:
    loan_ids: list[str] = []
    stats: dict[str, int] = {}
    return loan_ids, stats
```

---

## Type Transformation Cheat Sheet

| Old Syntax | New Syntax | Example |
|------------|------------|---------|
| `Dict[K, V]` | `dict[K, V]` | `dict[str, int]` |
| `List[T]` | `list[T]` | `list[str]` |
| `Set[T]` | `set[T]` | `set[int]` |
| `Tuple[T, U]` | `tuple[T, U]` | `tuple[str, int]` |
| `Optional[T]` | `T \| None` | `str \| None` |
| `Union[T, U]` | `T \| U` | `str \| int` |

**Keep using from typing**:
- `Any` - unchanged
- `TYPE_CHECKING` - unchanged
- `Protocol` - unchanged
- `Callable` - unchanged (no built-in equivalent)
- `TypeVar` - unchanged

---

## Common Patterns

### 1. Function Return Types

#### Old Style
```python
from typing import Dict, List

def get_kpis() -> Dict[str, List[float]]:
    return {"par30": [0.02, 0.03], "par90": [0.01, 0.015]}
```

#### New Style
```python
def get_kpis() -> dict[str, list[float]]:
    return {"par30": [0.02, 0.03], "par90": [0.01, 0.015]}
```

---

### 2. Optional Parameters

#### Old Style
```python
from typing import Optional, Dict

def load_config(path: Optional[str] = None) -> Dict[str, str]:
    if path is None:
        path = "config.yml"
    return {}
```

#### New Style
```python
def load_config(path: str | None = None) -> dict[str, str]:
    if path is None:
        path = "config.yml"
    return {}
```

**Note**: `X | None` is more explicit than `Optional[X]` and aligns with Python's walrus operator style.

---

### 3. Complex Nested Types

#### Old Style
```python
from typing import Dict, List, Optional

def process_data() -> Dict[str, List[Optional[Dict[str, int]]]]:
    return {"results": [{"count": 1}, None, {"count": 2}]}
```

#### New Style
```python
def process_data() -> dict[str, list[dict[str, int] | None]]:
    return {"results": [{"count": 1}, None, {"count": 2}]}
```

---

### 4. Class Attributes

#### Old Style
```python
from typing import Dict, List

class KPIEngine:
    config: Dict[str, str]
    results: List[float]
    
    def __init__(self):
        self.config: Dict[str, str] = {}
        self.results: List[float] = []
```

#### New Style
```python
class KPIEngine:
    config: dict[str, str]
    results: list[float]
    
    def __init__(self):
        self.config: dict[str, str] = {}
        self.results: list[float] = []
```

---

### 5. Union Types

#### Old Style
```python
from typing import Union

def process(value: Union[str, int, None]) -> str:
    return str(value)
```

#### New Style
```python
def process(value: str | int | None) -> str:
    return str(value)
```

---

## Migration Workflow

### For New Code

1. **Use native types by default**:
   ```python
   def my_function(items: list[str]) -> dict[str, int]:
       pass
   ```

2. **Use `| None` instead of Optional**:
   ```python
   def my_function(config: dict[str, str] | None = None) -> str | None:
       pass
   ```

3. **Only import from typing what you need**:
   ```python
   from typing import Any  # Only if you need Any
   ```

### For Existing Code

1. **Run Black formatter** (already configured for Python 3.10+):
   ```bash
   black src/pipeline/your_file.py
   ```

2. **Update imports**:
   ```python
   # Remove these
   from typing import Dict, List, Optional, Set, Tuple
   
   # Keep these if needed
   from typing import Any, TYPE_CHECKING, Protocol, Callable
   ```

3. **Find and replace**:
   - `Dict[` → `dict[`
   - `List[` → `list[`
   - `Set[` → `set[`
   - `Tuple[` → `tuple[`
   - `Optional[X]` → `X | None`

4. **Run tests**:
   ```bash
   pytest tests/
   ```

---

## IDE Configuration

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.extraPaths": ["src", "python"],
  "python.languageServer": "Pylance"
}
```

### PyCharm

1. Go to **Settings** → **Project** → **Python Interpreter**
2. Ensure Python 3.10+ is selected
3. Enable **Type Hints** in inspections

---

## Type Checking

### With mypy

```bash
# Check specific files
mypy src/pipeline/calculation.py

# Check entire directory
mypy src/pipeline/

# Strict mode
mypy --strict src/pipeline/
```

### Configuration (`mypy.ini`)

```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
```

---

## Common Pitfalls

### 1. Forgetting to Remove Old Imports

❌ **Wrong**:
```python
from typing import Dict, List  # Still importing old types

def process() -> dict[str, list[str]]:  # Using new syntax
    pass
```

✅ **Correct**:
```python
def process() -> dict[str, list[str]]:
    pass
```

---

### 2. Mixing Old and New Syntax

❌ **Wrong**:
```python
from typing import Optional

def process(config: dict[str, str] = None) -> Optional[dict]:
    pass
```

✅ **Correct**:
```python
def process(config: dict[str, str] | None = None) -> dict | None:
    pass
```

---

### 3. Using `| None` in Python 3.9

❌ **Breaks on Python 3.9**:
```python
def process(value: str | None) -> int:
    pass
```

✅ **Use old syntax if supporting Python 3.9**:
```python
from typing import Optional

def process(value: Optional[str]) -> int:
    pass
```

**Note**: This codebase requires Python 3.10+, so use new syntax.

---

## Testing Your Changes

### 1. Run Type Checker
```bash
mypy src/ python/
```

### 2. Run Tests
```bash
pytest tests/
```

### 3. Check Formatting
```bash
black --check src/ python/
```

### 4. Run Linters
```bash
ruff src/ python/
pylint src/ python/
```

---

## Examples from Our Codebase

### Pipeline Example

**File**: `src/pipeline/calculation.py`

```python
from typing import Any

class CalculationPhase:
    def __init__(self, config: dict[str, Any], kpi_definitions: dict[str, Any]):
        self.config = config
        self.kpi_definitions = kpi_definitions
    
    def execute(
        self,
        clean_data_path: Path | None = None,
        df: pd.DataFrame | None = None,
        run_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Execute KPI calculation phase."""
        pass
```

### Multi-Agent Example

**File**: `python/multi_agent/base_agent.py`

```python
from typing import Any

class BaseAgent:
    def process_request(
        self,
        request: dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Process agent request."""
        pass
```

---

## FAQ

### Q: Why migrate to new syntax?

**A**: 
1. More concise and readable
2. Standard Python 3.10+ practice
3. Better IDE support
4. Future-proof for Python 3.11+

### Q: Can I still use `Optional[T]`?

**A**: Yes, but we recommend `T | None` for consistency. The old syntax still works but is verbose.

### Q: What about Python 3.9 compatibility?

**A**: This codebase requires Python 3.10+. If you need 3.9 support, use old syntax.

### Q: Do I need to update all my code at once?

**A**: No, but new code should use new syntax. Update old code opportunistically.

### Q: How do I handle `Callable`?

**A**: Keep using `from typing import Callable` - there's no built-in replacement yet.

---

## Resources

- [PEP 585 – Type Hinting Generics In Standard Collections](https://peps.python.org/pep-0585/)
- [PEP 604 – Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [Python 3.10 Release Notes](https://docs.python.org/3/whatsnew/3.10.html)
- [mypy Documentation](https://mypy.readthedocs.io/)

---

## Support

If you have questions about the migration:

1. Check this guide first
2. Review examples in `src/pipeline/` and `python/multi_agent/`
3. Run `mypy` to catch type errors
4. Ask in team Slack channel #dev-python

---

**Last Updated**: January 31, 2026  
**Maintainer**: Development Team
