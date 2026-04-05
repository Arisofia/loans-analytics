# Google Sheets Integration Setup Guide

## Overview

This guide explains how to complete the Google Sheets data integration for the Loans Analytics pipeline. Configure your own spreadsheet ID and Google Cloud service account credentials before using this path.

## Credentials Status

**Required:**
- Spreadsheet ID for your source workbook
- Google Cloud project with Sheets API enabled
- Service account with access to the workbook
- Downloaded JSON key file stored outside version control

## Step 1: Generate Google Cloud Service Account Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Google Cloud project
3. Navigate to **IAM & Admin → Service Accounts**
4. Find the service account you want to use for Sheets access (or create one if missing)
5. Click **Keys** tab → **Add Key** → **Create new key**
6. Choose **JSON** format
7. Download the key file

## Step 2: Update Credentials File

Replace the placeholder in `credentials/google-service-account.json`:

```bash
# Copy your downloaded JSON file
cp ~/Downloads/<your-service-account-key>.json credentials/google-service-account.json
```

The file should contain:
- `private_key`: The actual RSA private key (multi-line)
- `client_email`: Service account email
- `client_id`: Service account ID
- `project_id`: GCP project ID
- All other OAuth 2.0 fields

## Step 3: Verify Integration

For all pipeline execution commands and Google Sheets integration examples, see **[Canonical Script Map - Data Pipeline](operations/SCRIPT_CANONICAL_MAP.md#data-pipeline)**.

**Quick test:**

```bash
python scripts/data/run_data_pipeline.py --input gsheets://DESEMBOLSOS
```

## Step 4: Enable Google Sheets in Pipeline

Google Sheets integration is pre-configured in `config/pipeline.yml` with:

```yaml
ingestion:
  google_sheets:
    enabled: true
    credentials_path: "credentials/google-service-account.json"
    spreadsheet_id: "<your-spreadsheet-id>"
    worksheet: "DESEMBOLSOS"
```

Run the pipeline as documented in **[Canonical Script Map](operations/SCRIPT_CANONICAL_MAP.md#data-pipeline)**.

## Expected Sheets Structure

The Google Sheet should contain two tabs:

### DESEMBOLSOS Tab (Active Disbursements)
**Required columns:**
- `CodCliente` — Customer code
- `FechaDesembolso` — Disbursement date
- `ValorAprobado` — Approved amount
- (Other loan details: interest rate, term, etc.)

### INTERMEDIA Tab (Intermediate/Control de Mora)
**Required columns:**
- `CodCliente` — Customer code
- `Cliente` — Customer name
- `NumeroInterno` — Internal reference
- `FechaDesembolso` — Disbursement date
- `TotalSaldoVigente` — Outstanding balance

## Troubleshooting

| Error | Solution |
|-------|----------|
| `CRITICAL: Could not open spreadsheet` | Verify spreadsheet ID is correct and service account has access rights |
| `CRITICAL: Tab 'DESEMBOLSOS' not found` | Check sheet name matches exactly (case-sensitive) |
| `CRITICAL: Google Sheets authentication failed` | Validate private key in `google-service-account.json` is valid JSON |
| `CRITICAL: Tab missing required columns` | Check column names match exactly (case-sensitive) |

## Security Notes

⚠️ **IMPORTANT:**
- `credentials/google-service-account.json` is **gitignored** — never commit credentials
- Private key is sensitive — store securely
- Service account should have **Viewer** role on the Google Sheet only
- Consider using Google Cloud IAM to control access per service account

## Configuration Files Modified

- ✅ `config/pipeline.yml` — Added Google Sheets ingestion config
- ✅ `.env` — Added Google Sheets environment variables
- ✅ `.env.example` — Added template for Google Sheets setup
- ✅ `credentials/google-service-account.json` — Created (placeholder, needs real key)

## Next Steps

1. **Download the service account JSON key** from Google Cloud Console
2. **Replace the placeholder** in `credentials/google-service-account.json`
3. **Test the integration** using the verification commands above
4. **Run the full pipeline** to ingest data from Google Sheets
