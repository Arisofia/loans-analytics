# Migration Standardization Plan (Phase 2b)

**Status**: Audit Complete (Phase 2a) → Ready for Implementation (Phase 2b)  
**Date Analyzed**: 2026-03-19  
**Total Migrations**: 31 SQL files  
**Estimated Implementation Time**: 4-6 hours  

---

## Executive Summary

The Abaco Loans Analytics repository uses 3 incompatible migration naming conventions, creating risk for execution order violations. This plan standardizes all migrations to **ISO 8601 timestamp format** (`YYYYMMDDHHMMSS_description.sql`), ensures deterministic execution order (alphabetic sort = logical order), and eliminates duplicate migrations.

**Key Benefits**:
- ✅ Deterministic execution order (alphabetic = chronological)
- ✅ No duplicate migration conflicts
- ✅ Scalable for future migrations
- ✅ Eliminates dependency on manual `migration_index.yml`
- ✅ Compatible with standard migration frameworks (Alembic, Flyway, etc.)

---

## Current State: 31 Migrations in 3 Naming Styles

### 1️⃣ Sequential Bare (3 files) — DEPRECATED
Used in earliest migrations; not scalable.

| Old Name | Size | Status | New Name | Action |
|----------|------|--------|----------|--------|
| `00_init_base_tables.sql` | 1.7 KB | Essential | `20250101000000_init_base_tables.sql` | RENAME |
| `001_create_lineage_schema.sql` | 2.1 KB | Essential | `20250101000100_create_lineage_schema.sql` | RENAME |
| `002_create_kpi_timeseries_daily.sql` | 3.0 KB | Essential | `20250101000200_create_kpi_timeseries_daily.sql` | RENAME |

**Rationale for Dates**: No original timestamps available; assigned `20250101` (arbitrary baseline) with sequential hour offsets for determinism.

---

### 2️⃣ Date Short (19 files) — PARTIAL ADOPTION
Used for majority of migrations; mostly deterministic when sorted alphabetically.

| Old Name | Size | New Name | Action |
|----------|------|----------|--------|
| `20251230_create_kpi_tables.sql` | 1.3 KB | `20251230000000_create_kpi_tables.sql` | RENAME |
| `20251231_pipeline_audit_tables.sql` | 3.8 KB | `20251231000000_pipeline_audit_tables.sql` | RENAME |
| `20260101_analytics_kpi_views.sql` | 18.3 KB | `20260101000000_analytics_kpi_views.sql` | RENAME |
| `20260105_security_hardening.sql` | 1.7 KB | `20260105000000_security_hardening.sql` | RENAME |
| `20260128_create_historical_kpis_table.sql` | 5.4 KB | `20260128000000_create_historical_kpis_table.sql` | RENAME |
| `20260201_create_historical_kpis.sql` | 2.3 KB | `20260201000000_create_historical_kpis.sql` | RENAME |
| `20260204_enable_rls.sql` | 3.0 KB | ❌ DELETE (duplicate of #20260204100000) | DELETE |
| `20260204_fix_broadcast_trigger.sql` | 3.6 KB | ❌ DELETE (older version of #20260204120000) | DELETE |
| `20260204_fix_kpi_values_policy.sql` | 5.1 KB | ❌ DELETE (older version of #20260204120500) | DELETE |
| `20260204_rls_policies.sql` | 7.5 KB | `20260204000000_rls_policies.sql` | RENAME |
| `20260205_create_public_kpi_values_view.sql` | 209 B | `20260205000000_create_public_kpi_values_view.sql` | RENAME |
| `20260208_create_fact_loans.sql` | 3.4 KB | `20260208000000_create_fact_loans.sql` | RENAME |

---

### 3️⃣ Timestamp Full (9 files) — CURRENT STANDARD
Most recent migrations; already deterministic.

| Old Name | Size | Status | Action |
|----------|------|--------|--------|
| `20260204035559_remote_schema.sql` | 18.7 KB | Keep as-is | NO CHANGE |
| `20260204050000_create_monitoring_schema.sql` | 2.3 KB | Keep as-is | NO CHANGE |
| `20260204100000_enable_rls_all_tables.sql` | 8.1 KB | ✅ KEEP (comprehensive version) | NO CHANGE |
| `20260204120000_fix_broadcast_trigger.sql` | 1.0 KB | ✅ KEEP (latest fix) | NO CHANGE |
| `20260204120500_fix_kpi_values_policy.sql` | 2.5 KB | ✅ KEEP (latest fix) | NO CHANGE |
| `20260205200000_grant_monitoring_schema_access.sql` | 927 B | Keep as-is | NO CHANGE |
| `20260205201000_create_kpi_public_views.sql` | 1.1 KB | Keep as-is | NO CHANGE |
| `20260206100000_add_rls_status_rpc.sql` | 715 B | Keep as-is | NO CHANGE |
| `20260206220000_enable_rls_missing_tables.sql` | 333 B | Keep as-is | NO CHANGE |
| `20260207100000_create_operational_events_commands.sql` | 3.5 KB | Keep as-is | NO CHANGE |
| `20260208000000_harden_monitoring_rls.sql` | 1.2 KB | Keep as-is | NO CHANGE |
| `20260223160000_add_monitoring_kpi_compatibility.sql` | 5.1 KB | Keep as-is | NO CHANGE |
| `20260223162000_add_daily_kpi_snapshot_job.sql` | 3.5 KB | Keep as-is | NO CHANGE |
| `20260223163000_refresh_public_kpi_views_for_compat.sql` | 652 B | Keep as-is | NO CHANGE |
| `20260223164000_add_missing_pipeline_kpi_definitions.sql` | 579 B | Keep as-is | NO CHANGE |
| `20260226220000_reconcile_monitoring_kpi_schema_and_rls.sql` | 28.7 KB | Keep as-is | NO CHANGE |

---

## Implementation Checklist (Phase 2b)

### Step 1: Backup & Documentation (30 min)
- [ ] Create backup of `db/migrations/` directory
- [ ] Document current `migration_index.yml` (if needed for reference)
- [ ] Commit current state: "docs: Document pre-standardization migration state"

### Step 2: Delete Duplicate Migrations (15 min)
These duplicates were fixed by later migrations and should not be rerun:

```bash
git rm db/migrations/20260204_enable_rls.sql
git rm db/migrations/20260204_fix_broadcast_trigger.sql
git rm db/migrations/20260204_fix_kpi_values_policy.sql
```

**Rationale**:
- `20260204_enable_rls.sql` → Superseded by `20260204100000_enable_rls_all_tables.sql` (more comprehensive)
- `20260204_fix_broadcast_trigger.sql` → Superseded by `20260204120000_fix_broadcast_trigger.sql` (1KB fix)
- `20260204_fix_kpi_values_policy.sql` → Superseded by `20260204120500_fix_kpi_values_policy.sql` (2.5KB fix)

### Step 3: Rename Sequential Migrations (10 min)
Rename the 3 legacy sequential migrations to ISO 8601 format:

```bash
git mv db/migrations/00_init_base_tables.sql db/migrations/20250101000000_init_base_tables.sql
git mv db/migrations/001_create_lineage_schema.sql db/migrations/20250101000100_create_lineage_schema.sql
git mv db/migrations/002_create_kpi_timeseries_daily.sql db/migrations/20250101000200_create_kpi_timeseries_daily.sql
```

### Step 4: Rename Date Short Migrations (15 min)
Rename 9 date-short migrations to include time component (assume midnight `000000`):

```bash
git mv db/migrations/20251230_create_kpi_tables.sql db/migrations/20251230000000_create_kpi_tables.sql
git mv db/migrations/20251231_pipeline_audit_tables.sql db/migrations/20251231000000_pipeline_audit_tables.sql
# ... (8 more similar renames)
```

### Step 5: Update File References (30 min)
- [ ] Search for any hardcoded references to old migration names
- [ ] Update documentation/deployment scripts if needed
- [ ] Update `migration_index.yml` if it exists (or delete if no longer needed)

### Step 6: Verify Execution Order (30 min)
```bash
ls -1 db/migrations/*.sql | sort  # Should match intended execution order
```

Compare with previous order; alert if different.

### Step 7: Test in Development (1-2 hours)
- [ ] Run migrations in dev/test environment
- [ ] Verify all tables/constraints created correctly
- [ ] Run data pipeline with new migration structure
- [ ] Verify no unique constraint violations
- [ ] Check for any missing permissions or schema issues

### Step 8: Commit & Document (15 min)
```bash
git commit -m "refactor: Standardize migration naming to ISO 8601 timestamps (R-06)

- Renamed 3 legacy sequential migrations (00_, 001_, 002_) to ISO 8601 format
- Renamed 9 date-short migrations (YYYYMMDD_) to full timestamp format (YYYYMMDDhhmmss_)
- Deleted 3 duplicate migrations (superseded by later fixes)
  - Removed: 20260204_enable_rls.sql (superseded by 20260204100000_enable_rls_all_tables.sql)
  - Removed: 20260204_fix_broadcast_trigger.sql (superseded by 20260204120000_fix_broadcast_trigger.sql)
  - Removed: 20260204_fix_kpi_values_policy.sql (superseded by 20260204120500_fix_kpi_values_policy.sql)
- All 28 remaining migrations now use deterministic ISO 8601 format
- Alphabetic sort = execution order (no manual index required)
- Tested in dev environment with full data pipeline"
```

---

## Risk Mitigation

### Before Implementation
- [ ] Backup database
- [ ] Create feature branch: `refactor/migration-standardization-2026-03-19`
- [ ] Test all migrations run successfully

### During Implementation
- [ ] Commit after each major step for easy rollback
- [ ] Verify alphabetic sort matches intended order
- [ ] Check for missing dependencies

### After Implementation
- [ ] Run full data pipeline
- [ ] Verify all downstream processes work correctly
- [ ] Test both fresh migrations and incremental updates
- [ ] Monitor for any constraint violations in production

---

## Success Criteria

- ✅ All 28 migrations use ISO 8601 format (`YYYYMMDDhhmmss_description.sql`)
- ✅ 3 duplicates removed; no data loss
- ✅ Alphabetic sort = execution order (deterministic)
- ✅ All migrations run without constraint violations
- ✅ `migration_index.yml` deleted or simplified
- ✅ Documentation updated
- ✅ CI/CD passes with new migration structure

---

## Timeline

| Phase | Activity | Duration | Owner |
|-------|----------|----------|-------|
| 2a | Audit & Analysis | 1-2 hrs | ✅ COMPLETE |
| 2b | Backup & Planning | 30 min | Next Session |
| 2b | Delete Duplicates | 15 min | Next Session |
| 2b | Rename Migrations | 25 min | Next Session |
| 2b | Update References | 30 min | Next Session |
| 2b | Dev Testing | 1-2 hrs | Next Session |
| 2b | Commit & Push | 15 min | Next Session |
| **Total** | **Implementation** | **4-6 hrs** | **Next Session** |

---

## Post-Implementation Cleanup

Once migrations are standardized, consider:

1. **Delete `migration_index.yml`** (if it exists and is no longer needed)
   - With deterministic ISO 8601 naming, manual index is unnecessary
   
2. **Update CI/CD** (if migrations are run in pipeline)
   - Verify glob patterns `db/migrations/*.sql` still work
   - Check any database migration tools (Alembic, Flyway) configurations

3. **Documentation Updates**
   - Update [docs/SETUP_GUIDE_CONSOLIDATED.md](../SETUP_GUIDE_CONSOLIDATED.md)
   - Update [docs/SUPABASE_SETUP_GUIDE.md](../SUPABASE_SETUP_GUIDE.md)
   - Add migration naming convention to [docs/GOVERNANCE.md](../GOVERNANCE.md)

---

## Appendix: Full Migration Inventory

### Current Full List (by type)

**Sequential (3)**:
```
00_init_base_tables.sql
001_create_lineage_schema.sql
002_create_kpi_timeseries_daily.sql
```

**Date-Short (19)**:
```
20251230_create_kpi_tables.sql
20251231_pipeline_audit_tables.sql
20260101_analytics_kpi_views.sql
20260105_security_hardening.sql
20260128_create_historical_kpis_table.sql
20260201_create_historical_kpis.sql
20260204_enable_rls.sql (DUPLICATE - DELETE)
20260204_fix_broadcast_trigger.sql (DUPLICATE - DELETE)
20260204_fix_kpi_values_policy.sql (DUPLICATE - DELETE)
20260204_rls_policies.sql
20260205_create_public_kpi_values_view.sql
20260208_create_fact_loans.sql
```

**Timestamp-Full (9)**:
```
20260204035559_remote_schema.sql
20260204050000_create_monitoring_schema.sql
20260204100000_enable_rls_all_tables.sql (KEEP)
20260204120000_fix_broadcast_trigger.sql (KEEP)
20260204120500_fix_kpi_values_policy.sql (KEEP)
20260205200000_grant_monitoring_schema_access.sql
20260205201000_create_kpi_public_views.sql
20260206100000_add_rls_status_rpc.sql
20260206220000_enable_rls_missing_tables.sql
20260207100000_create_operational_events_commands.sql
20260208000000_harden_monitoring_rls.sql
20260223160000_add_monitoring_kpi_compatibility.sql
20260223162000_add_daily_kpi_snapshot_job.sql
20260223163000_refresh_public_kpi_views_for_compat.sql
20260223164000_add_missing_pipeline_kpi_definitions.sql
20260226220000_reconcile_monitoring_kpi_schema_and_rls.sql
```

### Final Count After Implementation
- **Starting**: 31 migrations (3 naming styles)
- **Deletions**: 3 duplicates
- **Final**: 28 migrations (1 naming style: ISO 8601)

---

## Related Issues

- **R-06**: Migration Naming Audit (Source of this plan)
- **R-18**: Empty ingest directory (Separate cleanup)
- **PR**: Will be created for this refactoring

## References

- [ISO 8601 Date Format](https://en.wikipedia.org/wiki/ISO_8601)
- [Supabase Migrations](https://supabase.com/docs/guides/database/migrations)
- [Alembic Migration Format](https://alembic.sqlalchemy.org/en/latest/)

---

**Plan Created**: 2026-03-19  
**Ready for Implementation**: ✅ YES  
**Estimated Effort**: 4-6 hours  
**Complexity**: MEDIUM  
**Risk Level**: LOW (with proper testing)
