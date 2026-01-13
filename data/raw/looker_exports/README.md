# Looker Studio Datasets

This directory contains loan tape data exported from Looker Studio dashboard.

## Dataset Description

The Looker Studio report contains comprehensive loan portfolio analytics:

- **Dashboard URL**: Obtain the production Looker Studio link from the team's secure analytics documentation or access management system (report name: "Loan Portfolio Analytics").

## Files (To be uploaded)

Three primary datasets should be placed in this directory using standardized filenames:

### 1. loan_data.csv

- **Description**: Core loan tape data including loan amounts, rates, terms, and portfolio metrics
- **Source**: Looker Studio - Loan Data Table
- **Update Frequency**: Daily

### 2. customer_data.csv

- **Description**: Customer information and demographics
- **Source**: Looker Studio - Customer Data Table
- **Update Frequency**: Daily

### 3. historic_payment_data.csv

- **Description**: Historical payment records and transaction data
- **Source**: Looker Studio - Historic Payment Table
- **Update Frequency**: Daily

### Looker Studio export filenames

Looker Studio exports may use tool-generated filenames following the pattern:

- `Abaco-Loan-Tape_[Category]_Table-6.csv`

These export names are artifacts of Looker Studio and may change if the report is modified. The table below documents the mapping between the export filenames and the standardized filenames used in this repository:

| Looker export filename                               | Standardized filename         |
| ---------------------------------------------------- | ----------------------------- |
| `Abaco-Loan-Tape_Loan-Data_Table-6.csv`              | `loan_data.csv`               |
| `Abaco-Loan-Tape_Customer-Data_Table-6.csv`          | `customer_data.csv`           |
| `Abaco-Loan-Tape_Historic-Real-Payment_Table-6.csv`  | `historic_payment_data.csv`   |

When adding data to this directory, you may need to rename the exported CSVs from their Looker names to the standardized filenames above.

## Usage

These datasets are used by:

- Risk analytics agents for portfolio monitoring
- Customer segmentation for HubSpot integration
- Financial performance tracking
- Predictive modeling for loan outcomes

Downstream systems must treat these files as read-only, append-only exports. Schema, field semantics, and refresh cadence are governed as part of the data contracts described below.

### Data Contracts & Integration Patterns

- **File naming convention**: Files should use the exact names listed above. If date-partitioned exports are introduced, they MUST follow the pattern `<base-name>_YYYY-MM-DD.csv` and be documented before use by any integration.
- **Schema stability**: Column names, data types, and order are considered stable contracts for downstream consumers. Any breaking change (column rename/removal, type change) requires:
  - Prior review per `docs/analytics/governance.md`
  - A versioned export (e.g. suffix `_v2`) running in parallel until all consumers migrate
- **Refresh / ingestion pattern**:
  - Exports are generated on a daily batch schedule (see Freshness SLA below) and placed in this directory.
  - Consumers (risk analytics, HubSpot integration jobs, financial reporting pipelines, modeling workflows) should poll or pull the latest complete file and never modify files in-place.
- **Error handling**:
  - If a file is missing, incomplete, or fails validation, consumers should fail fast and notify the owner listed in the Data Governance section rather than attempting to repair the file.
  - Partial files (e.g. truncated uploads) must not be ingested.

## Data Governance

The following metadata is required by the analytics data governance standards. For additional details and authoritative policy, see `docs/analytics/governance.md`.

### Data retention policy

- Retain daily Looker exports in this directory for **24 months** unless a stricter retention period is mandated by `docs/analytics/governance.md` or legal/compliance requirements.
- Older files should be purged on at least a **monthly** basis by the data platform operations process.
- Downstream systems must not rely on files older than the documented retention window.

### Data lineage

- **Source systems**:
  - Production loan servicing system (loan accounts, balances, terms, payment schedules)
  - Customer relationship management (CRM) / customer master data (customer profiles and demographics)
- **Transformation path**:
  - Source data is ingested into the central analytics data warehouse according to the processes defined in `docs/analytics/governance.md`.
  - Curated warehouse views are exposed to Looker Studio dashboards.
  - These CSV files are exported from those Looker Studio dashboards and placed into this directory without manual modification.
- **Prohibited actions**:
  - Do **not** manually edit these CSVs after export.
  - Any required corrections must be made upstream (source systems, warehouse models, or Looker definitions) and then re-exported.

### Freshness SLA

- Exports are expected to be refreshed **once per day**.
- Target availability of the previous day’s data in this directory is **06:00 UTC**.
- Downstream jobs and reports depending on these files should be scheduled to run **after** the SLA time and tolerate up to **24 hours** of data lag.
- Any deviation from this SLA (delays, missed runs) should be communicated by the owner/responsible party to known consumers.

### Data quality checks

The following validations should be applied before files are considered ready for consumption:

- **Schema validation**:
  - Expected columns are present for each file (no missing required fields).
  - No unexpected columns are introduced without updating this README and notifying consumers.
- **Key integrity**:
  - Loan and customer identifiers are non-null and unique where required by the respective dataset.
- **Type / format checks**:
  - Numeric fields (e.g. principal, interest rate, balances) contain valid numeric values.
  - Date fields follow the agreed format (e.g. `YYYY-MM-DD`) and represent valid calendar dates.
- **Range / consistency checks**:
  - Payment records in `historic_payment_data.csv` must reference valid loan identifiers present in the loan tape.
  - No records are present with payment dates more than 30 calendar days in the future relative to the file generation date.
- Any failed checks should block publication of the file until resolved.

### Owner / responsible party

- **Primary owner**: Analytics / data platform team responsible for the loan portfolio reporting pipeline.
- For current contact details (team mailing list, on-call rotation, escalation path), refer to the **Contacts** section of `docs/analytics/governance.md`.
- All questions, incident reports, or change requests related to these exports should be directed to this owner.

### Access controls

- These files contain **production loan portfolio information** and may include customer-related attributes; they must be treated as **sensitive data**.
- Access to this directory is restricted to authorized personnel with an approved business need (e.g. risk, finance, analytics, selected engineering roles) in accordance with the role-based access policies defined in `docs/analytics/governance.md`.
- Files must not be copied to personal devices or unsanctioned storage locations.
- Any sharing with third parties requires prior approval through the established data sharing review process.

### Audit requirements

- Access to this directory and to the individual CSV files must be **logged** in accordance with the audit requirements specified in `docs/analytics/governance.md`.
- Changes to access control lists (ACLs) for this location should also be logged and periodically reviewed.
- Downstream systems consuming these files should retain operational logs sufficient to trace which jobs, users, or services accessed which files and when.

## Notes

- Files are CSV format exported from Looker Studio.
- Data contains production loan portfolio information and should be handled according to internal data classification and handling standards.
- Upload CSV files directly to this directory via GitHub CLI or desktop client; do not modify files after upload.
