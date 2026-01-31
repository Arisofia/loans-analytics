# Technical Debt Tracking - Action Items

**Last Updated**: 2026-01-31  
**Status**: Active Tracking  
**Owner**: Development Team

This document tracks individual technical debt items identified in `../../TECHNICAL_DEBT_ANALYSIS.md` with actionable tasks and progress tracking.

---

## 🔴 HIGH PRIORITY - Sprint 1 (Current)

### TD-001: Python Version Target Mismatch ⚠️ CRITICAL
**Category**: Code Quality  
**Effort**: 15 minutes  
**Status**: 🟡 Ready to Fix

**Problem**: `pyproject.toml` targets Python 3.9 but codebase uses Python 3.10+ syntax

**Action Steps**:
- [ ] Update `pyproject.toml`: Change `target-version = ['py39']` to `['py310', 'py311', 'py312']`
- [ ] Update README.md to document Python 3.10+ requirement
- [ ] Verify CI/CD pipelines use Python 3.10+

---

### TD-002: Test Location Consolidation Plan
**Category**: Structure  
**Effort**: 2-6 hours  
**Status**: 🔵 Planning Phase

**Problem**: Tests scattered across 3 locations creating confusion

**Proposed Structure**:
```
tests/
├── unit/
├── integration/
└── e2e/
```

---

### TD-003: Configuration Documentation
**Category**: Documentation  
**Effort**: 2 hours  
**Status**: 🔵 Not Started

**Problem**: Config file relationships and precedence undocumented

**Action**: Create `docs/CONFIGURATION_GUIDE.md`

---

## 🟡 MEDIUM PRIORITY - Sprint 2-4

### TD-004: Script Directory Organization
### TD-005: Large File Refactoring
### TD-006: Dependency Version Strategy
### TD-007: GitHub Workflows Consolidation

## 🟢 LOW PRIORITY

### TD-008: Documentation Consolidation
### TD-009: Archive Cleanup
### TD-010: Test Naming Consistency
### TD-011: Linting Configuration Audit
### TD-012: TypeScript Integration Documentation

---

## Metrics Dashboard

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Test locations | 3 | 1 | 🔴 |
| Python version | 3.9 | 3.10+ | 🔴 |
| GitHub workflows | 53 | <40 | 🔴 |
| Files >500 lines | 5 | 2 | 🔴 |

*See full details in complete tracking document*
