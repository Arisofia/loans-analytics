# Master Cleanup Quick Reference Card

## 🚀 Quick Commands

```bash
# Preview cleanup (safe)
./scripts/master_cleanup.sh --dry-run

# Execute cleanup
./scripts/master_cleanup.sh --execute

# Nuclear option (maximum cleanup)
./scripts/master_cleanup.sh --nuclear
```

## 📋 What Gets Deleted

| Category | Files/Directories |
|----------|-------------------|
| **Python** | `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `*.pyc` |
| **Node** | `node_modules/`, `.npm/`, `.next/`, `dist/`, `out/` |
| **Build** | `.gradle/`, `build/`, `coverage/` |
| **Backups** | `*.backup`, `*.bak`, `*.old`, `*.copy`, `* (1).*` |
| **Temp** | `tmp/`, `*.tmp`, `*.temp`, `*.swp` |
| **Logs** | `logs/`, `*.log`, `test-results/`, selected reports (`OPTIMIZATION_REPORT.md`, `TECHNICAL_DEBT_*.md`, ...) |
| **Data** | `data/metrics/run_*`, `logs/runs/run_*` |
| **IDE** | `.idea/`, `.vscode/cache/`, `.DS_Store` |
| **Docker** | Stopped containers, dangling images |
| **Git** | Merged branches, reflog (nuclear) |

## ✅ What's Preserved

- ✅ Source code (`src/`, `python/`, `scripts/`)
- ✅ Configuration (`config/`, `pyproject.toml`)
- ✅ Documentation (`docs/`, `README.md`)
- ✅ Production data directory (`data/raw/`)
- ✅ Tests (`tests/`)
- ✅ Environment templates (`.env.example`)
- ✅ Git history (`.git/`)

## 🎯 Mode Comparison

| Mode | Destructive? | Docker Volumes? | Git Reflog? | Use Case |
|------|--------------|-----------------|-------------|----------|
| `--dry-run` | ❌ No | N/A | N/A | Preview only |
| `--execute` | ⚠️ Yes | ❌ No | ❌ No | Standard cleanup |
| `--nuclear` | 🔥 Maximum | ✅ Yes | ✅ Yes | Deep clean |

## 💡 Best Practices

### ✅ DO
- Run `--dry-run` first
- Review output carefully
- Run before deployments
- Use weekly for maintenance
- Check git status after

### ❌ DON'T
- Run during active development
- Skip the dry-run
- Run without reviewing output
- Delete production data manually
- Run with processes active

## 🔧 Typical Workflow

```bash
# 1. Preview
./scripts/master_cleanup.sh --dry-run

# 2. Review (check for surprises)
# Look for any files you want to keep

# 3. Execute
./scripts/master_cleanup.sh --execute

# 4. Verify
git status
du -sh .

# 5. Test
pytest tests/
```

## 📊 Expected Size Reduction

```
Before:  ~700 MB (working tree + git)
After:   ~200 MB (--execute)
Nuclear: ~90 MB  (--nuclear)
Savings: 70-85%
```

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Permission denied | `chmod +x scripts/master_cleanup.sh` |
| Docker fails | Ensure Docker daemon is running |
| Branch delete fails | `git branch -D <branch>` to force |
| Deleted too much | `git checkout HEAD -- <file>` |

## 🌐 Cloud Cleanup

**Supabase** (manual):
```bash
# Via Dashboard: supabase.com/dashboard
# Or SQL: psql "$SUPABASE_DB_URL"
```

**Azure** (manual):
```bash
az storage blob delete-batch --source <container> --pattern "tmp*"
```

## 🔗 Related Scripts

- `scripts/cleanup_repo.sh` - Code quality only
- `scripts/repo-cleanup.sh` - Git only
- `scripts/repo-doctor.sh` - Health checks

**Use `master_cleanup.sh` as your primary tool.**

## 📚 Full Documentation

See [docs/MASTER_CLEANUP_GUIDE.md](MASTER_CLEANUP_GUIDE.md) for complete details.

---

**Version**: 1.0.0 | **Updated**: 2026-02-01
