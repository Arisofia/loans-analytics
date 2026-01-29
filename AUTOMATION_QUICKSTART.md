# 🤖 Automation Quick Start

## One-Time Setup (Local)

```bash
chmod +x scripts/setup-automation.sh
./scripts/setup-automation.sh
```

This installs pre-commit hooks that run on every commit.

## Common Commands

```bash
# Format all Python code
git fmt

# Run all checks
git check

# Run tests
git test

# Manual check of specific file
pre-commit run --files path/to/file.py
```

## What Happens Automatically

### On Every Commit
- ✅ Remove trailing whitespace
- ✅ Format Python code (Black)
- ✅ Sort imports (isort)
- ✅ Lint Python code (Flake8, Ruff)
- ✅ Lint YAML files
- ✅ Check for merge conflicts
- ✅ Remove unused imports

### On Every PR
- ✅ Auto-format and auto-commit formatting changes
- ✅ Run pytest on Python 3.10, 3.11, 3.12
- ✅ Generate coverage reports
- ✅ Security scanning (Bandit, Safety)

### Weekly (Monday 2 AM)
- ✅ Update Python dependencies
- ✅ Update npm packages
- ✅ Fix security issues
- ✅ Generate changelog

## File Locations

| Purpose | File |
|---------|------|
| CI/CD Workflows | `.github/workflows/auto-*.yml` |
| Pre-commit config | `.pre-commit-config.yaml` |
| Setup script | `scripts/setup-automation.sh` |
| Full docs | `docs/AUTOMATION_SETUP.md` |

## Troubleshooting

**Hooks not running?**
```bash
pre-commit install  # Reinstall
git config core.hooksPath  # Verify
```

**Want to skip checks?**
```bash
git commit --no-verify  # (not recommended)
```

**See available hooks?**
```bash
pre-commit run --list  # Show all hooks
```

---

For details, see [AUTOMATION_SETUP.md](../AUTOMATION_SETUP.md)
