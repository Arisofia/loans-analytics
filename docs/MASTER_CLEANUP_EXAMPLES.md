# Master Cleanup Script - Examples & Demonstrations

## Example 1: First Time Dry-Run

```bash
$ ./scripts/master_cleanup.sh --dry-run
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           🧹 MASTER CLEANUP SCRIPT - ABACO ANALYTICS           ║
║                                                                ║
║  ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE. PRODUCTION.    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

🔍 MODE: DRY-RUN (Preview Only - No Files Deleted)

═══════════════════════════════════════════════════════════════

[1/10] 🐍 Python Environment Cleanup
  Searching for __pycache__ directories...
    Found 12 __pycache__ director(ies)
    [WOULD DELETE] __pycache__: ./src/pipeline/__pycache__
    [WOULD DELETE] __pycache__: ./python/kpis/__pycache__
    ...
  Searching for Python bytecode files...
    Found 45 file(s)
    [WOULD DELETE] ./src/pipeline/calculation.pyc
    ...

[2/10] 📦 Node/NPM Environment Cleanup
  [WOULD DELETE] node modules: node_modules
    (directory size: 250 MB)

[3/10] 🏗️  Build Artifacts Cleanup
  [WOULD DELETE] Gradle cache: .gradle
    (directory size: 45 MB)

[4/10] 💾 Backup & Copy Files Cleanup
  Searching for backup files...
    Found 3 file(s)
    [WOULD DELETE] ./scripts/cleanup_repo.sh.backup
    [WOULD DELETE] ./config/pipeline.yml.backup
    ...

[10/10] 🔧 Git Repository Cleanup
(Skipped in dry-run mode)

═══════════════════════════════════════════════════════════════

🔍 DRY-RUN COMPLETE

No files were deleted. This was a preview only.

To actually execute the cleanup:
  ./scripts/master_cleanup.sh --execute

For maximum cleanup (including Docker, volumes, reflog):
  ./scripts/master_cleanup.sh --nuclear
```

## Example 2: Execute Standard Cleanup

```bash
$ ./scripts/master_cleanup.sh --execute
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           🧹 MASTER CLEANUP SCRIPT - ABACO ANALYTICS           ║
║                                                                ║
║  ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE. PRODUCTION.    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

💥 MODE: EXECUTE (FILES WILL BE DELETED!)

Press CTRL+C to cancel or Enter to continue...
[User presses Enter]

═══════════════════════════════════════════════════════════════

[1/10] 🐍 Python Environment Cleanup
  [DELETING] pytest cache: .pytest_cache
    ✓ Deleted
  Searching for __pycache__ directories...
    Found 12 __pycache__ director(ies)
    [DELETING] __pycache__: ./src/pipeline/__pycache__
    ✓ Deleted
    ...

[2/10] 📦 Node/NPM Environment Cleanup
  [DELETING] node modules: node_modules
    ✓ Deleted (freed 250 MB)

[10/10] 🔧 Git Repository Cleanup
  Fetching and pruning remote references...
    ✓ Complete
  Checking for merged local branches...
    Found 3 merged branch(es)
      Deleting: feature/old-feature
      Deleting: fix/resolved-bug
      Deleting: chore/cleanup-docs
    ✓ Merged branches deleted
  Running standard garbage collection...
    ✓ Complete

═══════════════════════════════════════════════════════════════

✅ CLEANUP COMPLETE

Repository Statistics:
  Git Directory Size: 45M
  Working Tree Size: 180M
  Current Branch: main

✨ Your repository is now clean!
   ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE.

═══════════════════════════════════════════════════════════════
```

## Example 3: Nuclear Mode (Maximum Cleanup)

```bash
$ ./scripts/master_cleanup.sh --nuclear
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           🧹 MASTER CLEANUP SCRIPT - ABACO ANALYTICS           ║
║                                                                ║
║  ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE. PRODUCTION.    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

💥 MODE: EXECUTE (FILES WILL BE DELETED!)
☢️  NUCLEAR MODE ACTIVE - MAXIMUM DESTRUCTION

Press CTRL+C to cancel or Enter to continue...
[User presses Enter]

═══════════════════════════════════════════════════════════════

[1/10] 🐍 Python Environment Cleanup
  [... same as execute mode ...]

[9/10] 🐳 Docker Cleanup
  Docker is installed - checking resources...
    [DELETING] 2 stopped container(s)
      ✓ Deleted
    [DELETING] 5 dangling image(s)
      ✓ Deleted
    [NUCLEAR] [DELETING] 3 unused volume(s)
      ✓ Deleted
    [NUCLEAR] Running docker system prune...
      ✓ Complete (freed 850 MB)

[10/10] 🔧 Git Repository Cleanup
  Fetching and pruning remote references...
    ✓ Complete
  Checking for merged local branches...
    ✓ Merged branches deleted
  [NUCLEAR] Running aggressive garbage collection...
    ✓ Complete
  [NUCLEAR] Expiring reflog entries...
    ✓ Complete

═══════════════════════════════════════════════════════════════

✅ CLEANUP COMPLETE

Repository Statistics:
  Git Directory Size: 28M
  Working Tree Size: 95M
  Current Branch: main

✨ Your repository is now clean!
   ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE.

═══════════════════════════════════════════════════════════════
```

## Example 4: Typical Workflow

```bash
# Step 1: Check repository size before cleanup
$ du -sh .
720M    .

$ du -sh .git
185M    .git

# Step 2: Preview cleanup
$ ./scripts/master_cleanup.sh --dry-run
[... output shows what will be deleted ...]

# Step 3: Execute cleanup
$ ./scripts/master_cleanup.sh --execute
[... cleanup runs ...]

# Step 4: Verify results
$ du -sh .
195M    .

$ du -sh .git
45M     .git

# Size reduction: 720M → 195M (73% reduction!)

# Step 5: Verify git status
$ git status
On branch main
nothing to commit, working tree clean

# Step 6: Run tests to ensure nothing broke
$ pytest tests/ -q
151 passed in 12.3s

# Step 7: Continue development with clean repository
$ # Ready to work!
```

## Example 5: Scheduled Cleanup (Crontab)

```bash
# Edit crontab
$ crontab -e

# Add this line for automatic weekly cleanup every Sunday at 2 AM
0 2 * * 0 cd /path/to/abaco-loans-analytics && ./scripts/master_cleanup.sh --execute >> /var/log/cleanup.log 2>&1

# Save and exit

# Verify crontab
$ crontab -l
0 2 * * 0 cd /path/to/abaco-loans-analytics && ./scripts/master_cleanup.sh --execute >> /var/log/cleanup.log 2>&1
```

## Example 6: Cloud Cleanup (Manual)

### Supabase Cleanup

```bash
# Connect to Supabase via psql
$ psql "$SUPABASE_DB_URL"

# List temporary tables
postgres=> \dt *tmp*
                   List of relations
 Schema |        Name         | Type  |  Owner
--------+---------------------+-------+----------
 public | test_tmp_loans      | table | postgres
 public | migration_tmp_data  | table | postgres

# Delete temporary data
postgres=> DELETE FROM test_tmp_loans WHERE created_at < NOW() - INTERVAL '7 days';
DELETE 1234

postgres=> DROP TABLE migration_tmp_data;
DROP TABLE

# Exit
postgres=> \q
```

### Azure Cleanup

```bash
# List Azure Storage blobs
$ az storage blob list \
  --container-name abaco-data \
  --account-name abacoanalytics \
  --output table

Name                      Blob Type    Last Modified
------------------------  -----------  --------------------
tmp_run_20260125.csv      BlockBlob    2026-01-25T10:30:00
tmp_run_20260128.csv      BlockBlob    2026-01-28T15:45:00

# Delete temporary blobs
$ az storage blob delete-batch \
  --source abaco-data \
  --pattern "tmp_*" \
  --account-name abacoanalytics

Deleting tmp_run_20260125.csv
Deleting tmp_run_20260128.csv
Total: 2 blobs deleted
```

## Size Reduction Comparison

| Scenario | Before | After | Reduction |
|----------|--------|-------|-----------|
| **Fresh Clone** | 350 MB | 340 MB | 3% |
| **After Development** | 720 MB | 195 MB | 73% |
| **With node_modules** | 1.2 GB | 180 MB | 85% |
| **Nuclear Mode** | 720 MB | 95 MB | 87% |

## Common Output Messages

### ✅ Success Messages

```
✓ No backup files found
✓ Deleted
✓ Complete
✓ Merged branches deleted
```

### ⚠️ Warning Messages

```
[WOULD DELETE] <file> (dry-run only)
[DELETING] <file> (actual deletion)
[NUCLEAR] <action> (nuclear mode only)
```

### ❌ Error Messages

```
Error: Not in a git repository
Permission denied: Cannot delete <file>
Docker daemon not running
```

---

**Note**: All examples above are representative. Actual output will vary based on your repository's current state.
