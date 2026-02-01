# Master Cleanup Guide

## Overview

The **Master Cleanup Script** is a comprehensive, nuclear-grade cleanup tool designed to maintain your repository in its cleanest, most production-ready state. This script removes ALL backups, copies, caches, and temporary files from both local and cloud environments.

**Philosophy**: ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE. PRODUCTION ONLY.

## Quick Start

```bash
# Preview what will be deleted (safe, non-destructive)
./scripts/master_cleanup.sh --dry-run

# Execute the cleanup
./scripts/master_cleanup.sh --execute

# Nuclear option (includes Docker volumes, git reflog)
./scripts/master_cleanup.sh --nuclear
```

## What Gets Cleaned

### 1. Python Environment (🐍)

- `__pycache__/` directories (all Python bytecode cache)
- `.pytest_cache/` (pytest cache)
- `.mypy_cache/` (mypy type checker cache)
- `.ruff_cache/` (ruff linter cache)
- `htmlcov/` (coverage HTML reports)
- `.coverage` (coverage data files)
- `*.pyc`, `*.pyo`, `*.pyd` (bytecode and compiled files)
- `*.egg-info/` (Python package metadata)

### 2. Node/NPM Environment (📦)

- `node_modules/` (all npm packages)
- `.npm/`, `.yarn/` (package manager caches)
- `.next/` (Next.js build artifacts)
- `.turbo/` (Turborepo cache)
- `dist/`, `out/` (distribution builds)
- `*.tsbuildinfo` (TypeScript build info)
- `.pnpm-debug.log*` (pnpm debug logs)

### 3. Build Artifacts (🏗️)

- `.gradle/` (Gradle build cache)
- `build/` (general build directory)
- `coverage/` (coverage reports)

### 4. Backup & Copy Files (💾)

- `*.backup`, `*.bak` (backup files)
- `*.old`, `*.orig` (old/original versions)
- `*.copy`, `*.Copy` (copy files)
- `*~` (editor backup files)
- `*.cleanup-backup` (cleanup backup files)
- `* (1).*`, `* (2).*`, etc. (numbered copies from Finder/downloads)
- `* copy.*`, `* Copy.*` (copy suffix files)

### 5. Temporary Files (🗑️)

- `tmp/`, `.tmp/` (temporary directories)
- `*.tmp`, `*.temp` (temporary files)
- `*.swp`, `*.swo` (vim swap files)
- `.*.swp` (hidden vim swap files)

### 6. Logs & Reports (📋)

- `logs/` (all log directories)
- `*.log` (individual log files)
- `playwright-report/` (Playwright test reports)
- `test-results/` (test result directories)
- `pytest-report/` (pytest reports)
- `coverage.xml`, `junit.xml` (test/coverage XML)
- Temporary markdown reports:
  - `AUTOMATION_SUMMARY*.md`
  - `CLEANUP_COMPLETE.md`
  - `CONSOLIDATION_*.md`
  - `OPTIMIZATION_REPORT.md`
  - `PROJECT_CLEANUP_STATUS.md`
  - `SESSION_COMPLETE.md`
  - `TECHNICAL_DEBT_*.md`

### 7. Data Directory Cleanup (📊)

- `data/archives/raw/tmp*.csv` (temporary raw archives)
- `data/metrics/run_*.csv` (run CSV files)
- `data/metrics/run_*.parquet` (run Parquet files)
- `data/metrics/run_*_metrics.json` (run metrics)
- `data/metrics/timeseries/run_*.parquet` (timeseries runs)
- `logs/runs/run_*/` (run log directories)
- `data/archives/cascade/tmp*.csv` (cascade temporary files)

⚠️ **Note**: This script does NOT delete production data files (e.g., `data/raw/sample_loans.csv`)

### 8. IDE & Editor Files (💻)

- `.idea/` (IntelliJ IDEA)
- `.settings/` (Eclipse settings)
- `*.code-workspace` (VS Code workspace files)
- `.vscode/history/` (VS Code history)
- `.vscode/cache/` (VS Code cache)
- `.DS_Store` (macOS Finder metadata)

### 9. Docker Cleanup (🐳)

**Standard Mode (`--execute`)**:
- Stopped containers
- Dangling images (untagged, unreferenced)

**Nuclear Mode (`--nuclear`)**:
- All of the above, plus:
- Unused volumes
- Complete system prune (all unused images, build cache)
- `grafana/data/` directory

### 10. Git Repository Cleanup (🔧)

**Standard Mode (`--execute`)**:
- Fetch and prune remote references
- Delete merged local branches (excluding main/master/develop)
- Standard garbage collection

**Nuclear Mode (`--nuclear`)**:
- All of the above, plus:
- Aggressive garbage collection
- Expire all reflog entries
- Prune unreachable objects

## Modes of Operation

### Dry-Run Mode (Default)

```bash
./scripts/master_cleanup.sh --dry-run
```

- **Safe**: No files are deleted
- **Preview**: Shows what would be deleted
- **Recommended**: Always run this first

### Execute Mode

```bash
./scripts/master_cleanup.sh --execute
```

- **Destructive**: Files are permanently deleted
- **Balanced**: Removes caches, backups, and temporary files
- **Safe**: Preserves production data and important configuration

### Nuclear Mode

```bash
./scripts/master_cleanup.sh --nuclear
```

- **Maximum Destruction**: Removes everything possible
- **Includes**: Docker volumes, git reflog, aggressive gc
- **Use Case**: When you want the absolute cleanest state
- **Warning**: Cannot undo - make backups if unsure

## Safety Features

1. **Dry-Run Default**: Script defaults to preview mode
2. **Confirmation Prompt**: Asks for confirmation before executing
3. **Excludes Production Data**: Does not touch critical business data
4. **Color-Coded Output**: Visual feedback for each operation
5. **Aligns with .gitignore Patterns**: Uses a static ignore list kept in sync with the repository’s `.gitignore` (does not parse `.gitignore` at runtime)

## What This Script Does NOT Delete

✅ **Production Files** (always preserved):
- Source code (`src/`, `python/`, `scripts/`)
- Configuration files (`config/business_rules.yaml`, `pyproject.toml`)
- Documentation (`docs/`, `README.md`)
- Production data (`data/raw/sample_loans.csv`)
- Tests (`tests/`)
- Docker compose files
- GitHub Actions workflows (`.github/workflows/`)
- Environment templates (`.env.example`)

## Cloud Resource Cleanup

### Supabase Cleanup

The script does NOT automatically delete Supabase cloud data. To clean Supabase:

```bash
# Option 1: Manual cleanup via Supabase Dashboard
# 1. Go to https://supabase.com/dashboard
# 2. Select your project
# 3. Navigate to Table Editor
# 4. Delete temporary/test tables manually

# Option 2: SQL cleanup (connect via psql)
psql "$SUPABASE_DB_URL"
# Then run DELETE queries for temporary data
```

### Azure Cleanup

The script does NOT automatically delete Azure resources. To clean Azure:

```bash
# Delete Azure Functions deployment artifacts
az functionapp deployment list-publishing-profiles \
  --name <function-app-name> \
  --resource-group <resource-group>

# Delete old deployments
az functionapp deployment source delete \
  --name <function-app-name> \
  --resource-group <resource-group>

# Clean Azure Storage blobs
az storage blob delete-batch \
  --source <container-name> \
  --pattern "tmp*"
```

## Integration with Existing Scripts

This master cleanup script **consolidates and supersedes**:

1. `scripts/cleanup_repo.sh` - Code quality cleanup
2. `scripts/repo-cleanup.sh` - Git repository cleanup
3. `scripts/commit_cleanup.sh` - Commit-time cleanup
4. `scripts/repo-doctor.sh` - Repository health checks

**Recommendation**: Use `master_cleanup.sh` as your primary cleanup tool.

## Best Practices

### When to Run

✅ **Recommended Times**:
- Before major deployments
- After completing a feature branch
- Weekly maintenance schedule
- Before committing large changes
- After running tests/builds

❌ **Avoid Running**:
- During active development
- While processes are running (tests, builds, servers)
- Without reviewing dry-run output first

### Workflow Integration

```bash
# Typical workflow
cd /path/to/abaco-loans-analytics

# 1. Preview cleanup
./scripts/master_cleanup.sh --dry-run

# 2. Review output carefully
# (check for any unexpected deletions)

# 3. Execute cleanup
./scripts/master_cleanup.sh --execute

# 4. Verify repository state
git status
du -sh .

# 5. Run tests to ensure nothing broke
pytest tests/
```

### Scheduled Cleanup

Add to crontab for automatic weekly cleanup:

```bash
# Every Sunday at 2 AM
0 2 * * 0 cd /path/to/abaco-loans-analytics && ./scripts/master_cleanup.sh --execute >> /var/log/cleanup.log 2>&1
```

## Troubleshooting

### "Permission Denied" Error

```bash
# Fix: Make script executable
chmod +x scripts/master_cleanup.sh
```

### Docker Cleanup Fails

```bash
# Ensure Docker daemon is running
docker ps

# If Docker requires sudo, run with sudo
sudo ./scripts/master_cleanup.sh --execute
```

### Git Branch Deletion Fails

```bash
# Force delete unmerged branches manually
git branch -D <branch-name>

# Or merge the branch first
git checkout main
git merge <branch-name>
```

### Deleted Too Much?

If you accidentally deleted important files:

```bash
# Restore from git (if files were committed)
git checkout HEAD -- <file-path>

# Restore from last commit
git reset --hard HEAD

# Restore deleted files using reflog (if not expired)
git reflog
git checkout <commit-hash> -- <file-path>
```

## Performance Impact

### Before Cleanup (Typical State)

```
Working Tree Size: ~500 MB
Git Directory Size: ~200 MB
Total: ~700 MB
```

### After Cleanup (--execute)

```
Working Tree Size: ~50 MB
Git Directory Size: ~150 MB
Total: ~200 MB
```

### After Nuclear Cleanup (--nuclear)

```
Working Tree Size: ~40 MB
Git Directory Size: ~50 MB
Total: ~90 MB
```

**Savings**: Typically **70-85% reduction** in repository size.

## Environment Variables

The script respects these environment variables:

- `DRY_RUN`: Set to `false` to execute without prompting
- `SKIP_DOCKER`: Set to `true` to skip Docker cleanup
- `SKIP_GIT`: Set to `true` to skip Git operations

```bash
# Example: Headless execution
DRY_RUN=false ./scripts/master_cleanup.sh --execute
```

## Exit Codes

- `0`: Success (cleanup completed)
- `1`: Error (invalid arguments or script failure)

## Comparison with Other Cleanup Scripts

| Feature | master_cleanup.sh | cleanup_repo.sh | repo-cleanup.sh |
|---------|-------------------|-----------------|-----------------|
| Python cleanup | ✅ Comprehensive | ✅ Basic | ❌ No |
| Node cleanup | ✅ Complete | ❌ No | ❌ No |
| Docker cleanup | ✅ Optional | ❌ No | ❌ No |
| Git cleanup | ✅ Full | ❌ No | ✅ Basic |
| Backup removal | ✅ All patterns | ❌ No | ❌ No |
| Data cleanup | ✅ Temp files | ❌ No | ❌ No |
| Dry-run mode | ✅ Yes | ❌ No | ❌ No |
| Cloud cleanup | 📝 Documented | ❌ No | ❌ No |

## Security Considerations

⚠️ **Important**:
- Script does NOT delete `.env` files (contains secrets)
- Does NOT delete `.git/` directory (version history)
- Does NOT delete production configuration files
- Does NOT push changes to remote (manual step)

## Contributing

To add new cleanup patterns:

1. Edit `scripts/master_cleanup.sh`
2. Add pattern to appropriate section (1-10)
3. Use `cleanup_item` or `cleanup_pattern` helper functions
4. Test with `--dry-run` first
5. Document in this guide

## License

This script is part of the Abaco Loans Analytics repository.  
See [LICENSE](../LICENSE) for details.

## Support

For issues or questions:
- Create an issue in GitHub
- Review [REPO_OPERATIONS_MASTER.md](REPO_OPERATIONS_MASTER.md)
- Consult [TROUBLESHOOTING.md](troubleshooting/README.md)

---

**Last Updated**: 2026-02-01  
**Version**: 1.0.0  
**Maintainer**: Abaco Analytics Team
