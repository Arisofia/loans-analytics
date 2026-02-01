# Repository Maintenance Guide

## Overview

The Abaco Loans Analytics repository uses a unified maintenance system for code quality, cleanup, formatting, and repository hygiene. This guide explains how to use the consolidated tools effectively.

## Quick Start

### Command Line

```bash
# Standard maintenance (recommended for regular use)
./scripts/repo_maintenance.sh --mode=standard

# Or using Makefile
make maintenance
```

### Preview Changes First

```bash
# Dry-run to see what would be cleaned
./scripts/repo_maintenance.sh --dry-run
make maintenance-dry-run
```

## The Unified Maintenance Script

**Location**: `scripts/repo_maintenance.sh`

This script consolidates all repository maintenance operations into a single, professional tool.

### Features

✨ **Code Formatting & Linting**
- Black formatter for Python
- isort for import sorting
- Ruff for fast linting with auto-fix
- Flake8 for style checking

🐍 **Python Environment Cleanup**
- Removes __pycache__ directories
- Cleans .pyc, .pyo bytecode files
- Clears pytest, mypy, ruff caches
- Removes coverage artifacts

🏗️ **Build Artifacts & Temp Files**
- Clears build/, dist/ directories
- Removes node_modules (if present)
- Deletes backup files (*.bak, *.old, *.backup)
- Cleans temporary files (*.tmp, *.temp)
- Removes editor swap files (.swp, .swo)
- Eliminates numbered copies and duplicates

🔧 **Git Repository Maintenance**
- Fetches and prunes remote references
- Deletes merged local branches
- Runs garbage collection
- Optimizes repository size
- (Aggressive mode) Deep GC with reflog cleanup

🐳 **Docker Cleanup** (Aggressive/Nuclear modes only)
- Removes stopped containers
- Deletes dangling images
- Prunes unused volumes
- System-wide cleanup

### Usage Modes

#### Standard Mode (Recommended)
```bash
./scripts/repo_maintenance.sh --mode=standard
# OR
make maintenance
```

**What it does**:
- Formats code (Black, isort, Ruff)
- Cleans Python caches
- Removes build artifacts and temp files
- Git fetch, prune, and standard GC

**When to use**: Regular maintenance, before commits, after merges

---

#### Aggressive Mode
```bash
./scripts/repo_maintenance.sh --mode=aggressive
# OR
make maintenance-aggressive
```

**What it does**:
- Everything in Standard mode
- **Aggressive Git GC** (more thorough, takes longer)
- **Docker cleanup** (stopped containers, dangling images)

**When to use**: Weekly/monthly deep cleaning, after large refactors

---

#### Nuclear Mode ⚠️
```bash
./scripts/repo_maintenance.sh --mode=nuclear
```

**What it does**:
- Everything in Aggressive mode
- **Git reflog expiration** (removes reflog history)
- **Docker system prune with volumes** (deletes ALL unused Docker resources)

**When to use**: 
- Extreme repo bloat situations
- Recovering from extensive experimentation
- ⚠️ **CAUTION**: Cannot recover deleted reflog entries or Docker volumes

---

#### Format-Only Mode
```bash
./scripts/repo_maintenance.sh --format-only
# OR
make format
```

**What it does**: Only runs code formatters (Black, isort, Ruff)

**When to use**: Quick formatting before commit, CI checks

---

#### Dry-Run Mode
```bash
./scripts/repo_maintenance.sh --dry-run
# OR
make maintenance-dry-run
```

**What it does**: Shows what would be cleaned WITHOUT making changes

**When to use**: Before running aggressive/nuclear modes, checking repo state

---

#### CI Mode
```bash
./scripts/repo_maintenance.sh --ci
```

**What it does**: Non-interactive mode suitable for CI/CD pipelines

**When to use**: GitHub Actions workflows, automated systems

## GitHub Actions Workflow

**Location**: `.github/workflows/code-maintenance.yml`

### Automatic Triggers

- **Push to main/develop**: Runs formatting and auto-commits fixes
- **Pull Requests**: Validates code quality (no auto-commits)
- **Weekly Schedule**: Monday 2 AM UTC - full repository maintenance
- **Manual Dispatch**: On-demand with selectable cleanup level

### Jobs

1. **format-and-lint**: Code formatting with auto-fix
2. **repository-cleanup**: Filesystem and cache cleanup
3. **type-check**: MyPy static type analysis
4. **sonarcloud**: Code quality analysis (if configured)
5. **git-maintenance**: Git repository optimization
6. **maintenance-summary**: Consolidated job results

### Manual Workflow Dispatch

Run from GitHub UI:

1. Go to Actions → Code Maintenance
2. Click "Run workflow"
3. Select cleanup level:
   - **standard**: Regular cleanup
   - **aggressive**: Deep cleanup with GC
   - **nuclear**: Maximum cleanup (use with caution)

## Makefile Targets

All maintenance operations are available through Make:

```bash
make maintenance              # Standard cleanup
make maintenance-aggressive   # Aggressive cleanup
make maintenance-dry-run      # Preview changes

# Individual operations
make format                   # Format code only
make lint                     # Run linters
make type-check               # Run MyPy
make clean                    # Remove build artifacts only
```

## Best Practices

### Daily Development

```bash
# Before committing
make format
git add -A
git commit -m "your message"
```

### Weekly Maintenance

```bash
# Preview first
make maintenance-dry-run

# Then execute
make maintenance
```

### Monthly Deep Clean

```bash
# For a thorough cleanup
make maintenance-aggressive
```

### After Major Refactoring

```bash
# Check what needs cleaning
./scripts/repo_maintenance.sh --dry-run

# Then decide between standard or aggressive
make maintenance-aggressive
```

## What Was Consolidated

This unified system replaces the following deprecated scripts (now in `archives/maintenance/deprecated-cleanup-scripts/`):

1. **cleanup_repo.sh** - Code quality and formatting
2. **commit_cleanup.sh** - Automated commit creation
3. **master_cleanup.sh** - Comprehensive filesystem cleanup
4. **repo-cleanup.sh** - Git repository maintenance
5. **code-quality.yml** - GitHub Actions workflow

The new system consolidates the most commonly used maintenance tasks. Some specialized checks from the deprecated scripts (such as YAML validation, merge-conflict marker and secret scanning, and additional cleanup targets) remain available via CI workflows and the archived scripts directory.

## Troubleshooting

### "Black not installed"
```bash
source .venv/bin/activate
pip install black isort ruff
```

### "Not in a git repository"
Ensure you're in the repository root:
```bash
cd /path/to/abaco-loans-analytics
```

### Git GC takes too long
Use standard mode instead of aggressive:
```bash
./scripts/repo_maintenance.sh --mode=standard
```

### Want to keep reflog history
Avoid nuclear mode. Use standard or aggressive instead.

## Integration with CI/CD

The maintenance workflow integrates seamlessly with:
- **Pre-commit hooks**: Auto-format on commit
- **GitHub Actions**: Auto-format on push, validate on PR
- **Azure Pipelines**: Can be triggered via webhook
- **Local development**: Make targets for quick access

## Support

For issues or questions about repository maintenance:
1. Check this documentation
2. Review `scripts/repo_maintenance.sh --help`
3. See GitHub Actions runs for automated maintenance logs
4. Check `archives/maintenance/deprecated-cleanup-scripts/README.md` for migration notes

---

**Last Updated**: 2026-02-01  
**Version**: 1.0.0 (Unified System)
