# data/raw

Unified analytics raw inputs for portfolio analysis.

## Two-source architecture

- Loan Tape CSVs (historical/pre-2026):
  - loan_data.csv
  - payment_schedule.csv
  - real_payment.csv
  - customer_data.csv
  - collateral.csv
- Control de Mora / Google Sheets (post-2026):
  - gsheets://INTERMEDIA (via service account)

## Naming contract

`LoanTapeLoader` expects these canonical filenames under `data/raw/`.

## Security

Real raw CSVs in this folder are ignored by git (`data/raw/*.csv`).
Keep credentials out of git (`credentials/`).

## Unified run

```bash
python scripts/data/run_data_pipeline.py \
  --input data/raw/loan_data.csv
```
