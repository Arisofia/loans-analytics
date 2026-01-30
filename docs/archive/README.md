# 📁 Archived Documentation

> **⚠️ HISTORICAL / ARCHIVED DOCUMENTS**
>
> The documents in this folder are preserved for **audit trail and governance purposes only**.
> They document past states of the system, migration decisions, and historical architecture.
>
> **DO NOT USE FOR CURRENT IMPLEMENTATION GUIDANCE.**

## Why These Are Kept

1. **Audit Trail**: Documents how data was processed historically (required for compliance)
2. **Onboarding Context**: Explains "why we moved away from X" for new team members
3. **Due Diligence**: Preserves decision history for stakeholders

## Deprecated Integrations (Retired 2026-01)

The following integrations mentioned in archived documents have been fully retired:

| Integration             | Status     | Replacement                         |
| ----------------------- | ---------- | ----------------------------------- |
| **Cascade API**         | ❌ Retired | CSV files + Supabase direct queries |
| **Slack Notifications** | ❌ Retired | Grafana alerts + Azure diagnostics  |
| **HubSpot CRM Sync**    | ❌ Retired | N/A (discontinued feature)          |
| **Notion Database**     | ❌ Retired | N/A (discontinued feature)          |
| **Looker**              | ❌ Retired | Streamlit + Grafana dashboards      |

## Current Architecture

For current implementation guidance, see:

- [../OPERATIONS.md](../OPERATIONS.md) - Operational runbook
- [../DEVELOPMENT.md](../DEVELOPMENT.md) - Development setup
- [../../README.md](../../README.md) - Project overview
- [../../config/pipeline.yml](../../config/pipeline.yml) - Pipeline configuration
