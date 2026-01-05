# Data Governance Policy

## Purpose

This document establishes the golden rules for how data is documented, stored, and referenced throughout the Abaco Technologies repository. It ensures that:

- **Production workflows** always query live data sources
- **Documentation files** describe processes, not static data
- **Strategic planning documents** are clearly labeled as targets, not actuals
- **Data governance** maintains a single source of truth

---

## Golden Rules

### 1. Markdown Files Are Documentation ONLY

**Rule:** `.md` files describe **HOW to get data**, not **WHAT the data is**.

✅ **Acceptable in .md files:**

- Process descriptions ("Calculate AUM by summing outstanding_principal...")
- Formulas and calculations ("NPL = total_defaults / total_loans")
- Timestamps for documentation updates ("Last Updated: 2025-12-26")
- Query examples ("SELECT SUM(outstanding_principal) FROM fact_loans...")
- Configuration references ("See config/pipeline.yml for...")

❌ **Prohibited in .md files:**

- Hard-coded metrics ("Current AUM is $7.4M")
- Specific customer counts ("We have 56 customers")
- Target numbers without "TARGET" or "PLANNING" labels
- Static numbers with implicit "current state" meaning

**Rationale:** Documentation changes are infrequent; data changes hourly. Hard-coded numbers become stale and create inconsistencies.

---

### 2. Source of Truth Hierarchy

**Priority 1 (Highest): Live Database Tables**

- `fact_loans` — Loan and disbursement source data
- `kpi_timeseries_daily` — Daily KPI snapshots
- `fact_cash_flows` — Payment and collection records
- All other operational tables

**Priority 2: Configuration Files**

- `config/pipeline.yml` — Pipeline parameters
- `config/kpis.yml` — KPI definitions
- `config/environments/*.yml` — Environment configurations
- `.env`, secrets, and system configs

**Priority 3 (Lowest): Documentation**

- `.md` files — Process guides, how-tos, reference materials
- Release notes and changelogs
- Architecture decision records (ADRs)

**Rule:** Always query Priority 1 data. Never copy Priority 1 data into Priority 3 documents.

---

### 3. File Organization

**Operational Documentation** (`/docs/`)

- `process/` — How to run pipelines, workflows, and manual tasks
- `api/` — API documentation and integration guides
- `architecture/` — System design and decision records
- `data-dictionary/` — Schema definitions (generated from code, not hand-written)

**Strategic Planning** (`/docs/planning/`)

- `2026/` — 2026 strategic targets and North Star metrics
- `2025/` — 2025 OKRs and executive planning documents
- All files in this directory include warnings: "⚠️ PLANNING TARGETS ONLY"

**Historical Records** (`/archives/`)

- `extractions/` — Past data extraction snapshots
- `compliance/` — Historical audit reports and validation summaries
- `snapshots/` — Point-in-time operational snapshots

**Live Data** (`/data/`)

- Daily exports and fresh data files
- Current metrics and dashboards
- Source of truth for time-series data

---

### 4. Static Data Detection & Prevention

**How to identify static data in .md files:**

| Pattern | Example | Verdict | Action |
|---------|---------|---------|--------|
| Dollar amount with context | "Current AUM is $7.4M" | 🔴 STATIC | Remove or move to /docs/planning/ + add warning |
| Customer count | "We have 56 customers" | 🔴 STATIC | Replace with query: "SELECT COUNT(DISTINCT client_id)" |
| Date-specific metric | "As of December 2025, NPL is 3.8%" | 🔴 STATIC | Move to query or to /archives/ |
| Target labeled "TARGET" | "TARGET AUM: $16.3M for 2026" | 🟢 OK if in /docs/planning/ | Keep with warning label |
| Process description | "Sum outstanding_principal from fact_loans" | 🟢 OK | Keep in operational docs |
| Timestamp of doc update | "Last Updated: 2025-12-26" | 🟢 OK | Keep (meta-information) |

---

### 5. Planning Documents: Special Handling

**All files in `/docs/planning/` must include a header:**

```markdown
⚠️ **STRATEGIC PLANNING DOCUMENT - {YEAR} TARGETS ONLY**

**DO NOT USE THESE NUMBERS IN PRODUCTION WORKFLOWS**

This document contains {planning targets / OKRs / strategic goals} for {year}.
All dollar amounts, metrics, and targets are planning hypotheses, not current state data.

**For current metrics, query live data sources:**
- AUM: `SELECT SUM(outstanding_principal) FROM fact_loans WHERE status='active'`
- NPL: `SELECT * FROM kpi_timeseries_daily WHERE metric='npl_180' ORDER BY date DESC LIMIT 1`

**Document Status:** Strategic Planning (Last Review: YYYY-MM-DD)

---
```

---

### 6. Archive Policy

**When to archive:**

- Documentation older than 6 months and no longer actively used
- Historical snapshots or reports (compliance, audits, validation)
- Past extraction processes or deprecated procedures
- Point-in-time metrics that are no longer relevant

**Archive structure:**

```text
archives/
├── extractions/2025-12-04/     # Dated extractions
├── extractions/2025-12-11/
├── compliance/2025-12-08_validation_summary.md
├── snapshots/operational_2025-q4/
└── deprecated/
```

**Archive files remain searchable** but are excluded from main documentation navigation.

---

### 7. Enforcement & Tooling

**Pre-commit hook to prevent static data:**

```bash
#!/bin/bash
# Check for dollar amounts in .md files (except /archives/ and /docs/planning/)
if grep -r '\$[0-9]\+[KMB]\?' docs/ --include="*.md" \
    --exclude-dir="planning" --exclude-dir="archives"; then
  echo "❌ ERROR: Static dollar amounts found in documentation"
  echo "Move to /docs/planning/ or use query examples instead"
  exit 1
fi
```

**CI/CD check to flag static metrics:**

- Scan .md files for patterns: `\$\d+[KMB]?`, `\d+\s+(customers|clients|users)`
- Exclude /docs/planning/ and /archives/
- Warn if found; fail if in core operational docs

---

### 8. Roles & Responsibilities

| Role | Responsibility |
|------|-----------------|
| **Data Team** | Maintain live data sources; generate exports; keep dashboards fresh |
| **Product/Engineering** | Update operational docs in `/docs/`; keep ADRs current |
| **Executive/Strategy** | Maintain planning docs in `/docs/planning/`; review quarterly |
| **Compliance** | Archive audit reports to `/archives/compliance/` with dates |
| **DevOps/Infrastructure** | Enforce pre-commit hooks and CI/CD checks |

---

### 9. Migration Guide: Fixing Static Data

**For files with hard-coded metrics:**

1. **Identify the metric** (e.g., "Current AUM is $7.4M")
2. **Ask:** Is this current state or a planning target?
   - **Current state?** → Replace with query or remove
   - **Planning target?** → Move file to /docs/planning/ and add warning header
3. **Update references** in other docs to point to live sources
4. **Test** that queries return expected results
5. **Commit** with message: "chore: remove static data from {filename}"

---

### 10. Examples

#### ✅ Good: Process Documentation

```markdown
# How to Calculate AUM

To determine current Assets Under Management:

1. Query all active loans:
   ```sql
   SELECT
     SUM(outstanding_principal) as aum
   FROM fact_loans
   WHERE status = 'active'
     AND created_at <= NOW();
   ```

1. Group by client for portfolio breakdown:

   ```sql
   SELECT
     client_id,
     SUM(outstanding_principal) as client_aum
   FROM fact_loans
   WHERE status = 'active'
   GROUP BY client_id
   ORDER BY client_aum DESC;
   ```

Last Updated: 2025-12-26

```text

#### ❌ Bad: Static Data in Operational Docs

```markdown
# Current Portfolio Status

Our current AUM is $7.4M with 56 active customers.
Our NPL rate is currently 3.8%.
```

#### ✅ Good: Strategic Planning Document

```markdown
⚠️ **STRATEGIC PLANNING DOCUMENT - 2026 TARGETS ONLY**

# 2026 North Star Metrics

| Metric | 2025 Current | 2026 Target |
|--------|--------------|-------------|
| AUM    | $7.4M        | $16.3M      |
| Customers | 56        | 500         |
| NPL Rate  | 3.8%     | <4.0%      |
```

---

## Questions?

- **"Can I put a number in docs?"** → Only if it describes a process or formula, not a current metric
- **"Where should planning targets go?"** → `/docs/planning/` with a warning header
- **"How do I know if a number is stale?"** → If it came from a manual export or report, it's likely stale
- **"Can I reference a dashboard?"** → Yes, but don't copy numbers from it into .md files

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-26 | Data Governance | Initial policy document |
