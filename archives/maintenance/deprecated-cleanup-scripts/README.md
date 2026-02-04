# Deprecated Cleanup Scripts

**Date Archived**: 2026-02-01  
**Reason**: Consolidated into unified `scripts/repo_maintenance.sh`

## Scripts Archived

### 1. `cleanup_repo.sh` (4.5KB)

- **Purpose**: Code quality cleanup (formatting, linting, trailing whitespace)
- **Features**:
  - Removed trailing whitespace
  - Normalized line endings
  - Ran Black, isort, pylint
  - Validated YAML syntax
  - Security checks

### 2. `commit_cleanup.sh` (2.5KB)

- **Purpose**: Automated commit of cleanup changes
- **Features**:
  - Staged all changes
  - Created comprehensive commit message
  - Pushed to remote

### 3. `master_cleanup.sh` (19KB)

- **Purpose**: Comprehensive filesystem and Docker cleanup
- **Features**:
  - Python environment cleanup (`__pycache__`, `.pyc` files)
  - Node/NPM cleanup
  - Build artifacts cleanup
  - Backup/copy files cleanup
  - Temporary files cleanup
  - Logs and reports cleanup
  - Data directory cleanup
  - IDE files cleanup
  - Docker cleanup (containers, images, volumes)
  - Git repository cleanup
- **Modes**: dry-run, execute, nuclear

### 4. `repo-cleanup.sh` (5.2KB)

- **Purpose**: Git repository maintenance
- **Features**:
  - Fetch and prune remote references
  - Remove untracked files
  - Delete merged local branches
  - Delete stale remote branches
  - Garbage collection (standard/aggressive)
  - Repository statistics

## Unified Replacement

All functionality has been consolidated into:

**`scripts/repo_maintenance.sh`**

### Usage Examples

```bash
# Standard cleanup (replaces cleanup_repo.sh + repo-cleanup.sh)
./scripts/repo_maintenance.sh --mode=standard

# Aggressive cleanup with Docker (replaces master_cleanup.sh)
./scripts/repo_maintenance.sh --mode=aggressive

# Maximum cleanup (replaces master_cleanup.sh --nuclear)
./scripts/repo_maintenance.sh --mode=nuclear

# Preview changes without executing
./scripts/repo_maintenance.sh --dry-run

# Format code only
./scripts/repo_maintenance.sh --format-only

# CI-friendly mode
./scripts/repo_maintenance.sh --ci
```

### Makefile Integration

```bash
make maintenance              # Standard maintenance
make maintenance-aggressive   # Aggressive cleanup
make maintenance-dry-run      # Preview only
```

### GitHub Actions Integration

The new unified workflow is at: `.github/workflows/code-maintenance.yml`

This replaces `code-quality.yml` and integrates all cleanup functionality.

## Benefits of Consolidation

✅ **Single Source of Truth**: One script for all maintenance operations  
✅ **Reduced Complexity**: 4 scripts → 1 unified script  
✅ **Better Documentation**: Comprehensive help and usage information  
✅ **Easier Maintenance**: One file to update and test  
✅ **Professional Structure**: Clean, organized, high-quality codebase  
✅ **Consistent Behavior**: Same cleanup logic everywhere

## Migration Notes

- No breaking changes - all functionality preserved
- Enhanced features with new modes and options
- Better error handling and user feedback
- CI/CD integration through GitHub Actions
- Backward compatibility through Makefile targets
