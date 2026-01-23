# Data Folder

- data/archives: Archived raw inputs (Abaco loan tapes, cascade uploads, Looker exports, etc.).
  - `data/archives/cascade/` - cascade ingest outputs and loan tape archives
  - `data/archives/looker_exports/` - Looker export CSVs (PAR snapshots and fallbacks)
  - `data/archives/financial_statements/` - optional financial statement uploads (CSV/XLSX)
- data/support: Synthetic support tables for marketing, targets, risk params, etc.

Notes:

- The `data/archives/` directory contains authoritative archived input artifacts; do not commit large raw files to git. Use external storage or CI artifacts for large data.
