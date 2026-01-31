# Technical Debt Quick Reference

**Last Updated**: 2026-01-31  
**Purpose**: Quick reference card for technical debt findings

---

## 🚨 CRITICAL ISSUES (Fix Immediately)

### Python Version Mismatch
- **File**: `pyproject.toml:19`
- **Issue**: Targets Python 3.9, should be 3.10+
- **Fix**: Change `target-version = ['py39']` to `['py310', 'py311', 'py312']`
- **Time**: 15 minutes

---

## 📊 KEY METRICS

| Category | Count | Target | Priority |
|----------|-------|--------|----------|
| Test Locations | 3 dirs | 1 dir | 🔴 HIGH |
| GitHub Workflows | 53 files | <40 | 🟡 MEDIUM |
| Python Files >500 lines | 5 | 2 | 🟡 MEDIUM |
| Scripts (unorganized) | 23 | 0 | 🟡 MEDIUM |
| Documentation Files | 279 | <200 | 🟢 LOW |
| Archive Files | 10 | 0 | 🟢 LOW |

---

## 🎯 TOP 5 QUICK WINS (< 1 hour each)

1. **Python Version Fix** (15 min) - Fix pyproject.toml
2. **Archive Cleanup** (30 min) - Remove old files from archives/
3. **Test Naming** (30 min) - Rename non-standard test files
4. **Documentation Headers** (45 min) - Add "Last Updated" to all docs
5. **Script README** (45 min) - Document purpose of each script

---

## 📁 FILE LOCATIONS

### Largest Files (Review for Refactoring)
```
966 lines - python/multi_agent/orchestrator.py
821 lines - python/multi_agent/historical_context.py
714 lines - src/pipeline/transformation.py
447 lines - src/pipeline/output.py
442 lines - src/pipeline/calculation.py
```

### Test Locations (Consolidate)
```
tests/               # Main test directory
python/multi_agent/  # 8 test files mixed with source
python/tests/        # Additional test location
```

### Scripts to Organize (23 files)
```
scripts/deployment/   # deploy_to_azure.sh, rollback_deployment.sh
scripts/operations/   # health_check.py, metrics_exporter.py
scripts/development/  # validate_structure.py, repo-doctor.sh
scripts/testing/      # load_test_supabase.py, benchmark_costs.py
```

---

## 🛠️ RECOMMENDED TOOLS

- **Code Quality**: Ruff (modern, fast linter)
- **Dependency Updates**: Dependabot or Renovate
- **File Size Monitor**: Custom pre-commit hook
- **Workflow Optimization**: GitHub Actions matrix strategies

---

## 📅 SPRINT PLAN

### Sprint 1 (Week of 2026-01-31)
- [ ] Fix Python version target
- [ ] Document test consolidation plan
- [ ] Create configuration guide

### Sprint 2-4 (Feb-Mar 2026)
- [ ] Organize scripts directory
- [ ] Refactor large files
- [ ] Consolidate workflows

### Ongoing (Q2 2026)
- [ ] Clean up archives
- [ ] Consolidate documentation
- [ ] Audit linting rules

---

## 📚 FULL DOCUMENTATION

- **Complete Analysis**: `../../TECHNICAL_DEBT_ANALYSIS.md`
- **Detailed Tracking**: `DEBT_TRACKING.md` (when created)
- **This Summary**: `QUICK_REFERENCE.md`

---

*Keep this updated as debt is addressed*
