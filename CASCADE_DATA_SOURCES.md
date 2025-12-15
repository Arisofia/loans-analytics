# Cascade Debt Platform - Data Sources

**Project:** Abaco Loans Analytics
**Platform:** Cascade Debt (cascadedebt.com)
**Portfolio ID:** abaco
**Last Updated:** December 15, 2025
**Data as of:** December 11, 2025 (Last platform update: December 14, 2025)

## Overview

This document contains the URLs and instructions for downloading current data from the Cascade Debt platform for the Abaco portfolio.

## Data Export URLs

### 1. Loan Tape Export
**Description:** Complete loan-level data export
**URL:** `https://app.cascadedebt.com/data/exports/loan-tape?pid=abaco`
**Format:** CSV/XLSX
**Contents:** 
- Individual loan details
- Borrower information
- Payment history
- Current loan status
- Outstanding balances

### 2. Financial Statements - Profit & Loss
**Description:** Income statement and P&L metrics
**URL:** `https://app.cascadedebt.com/analytics/financials/statements?pid=abaco&tab=profit-%26-loss`
**Format:** Exportable via Export button (CSV, JSON, XLSX)
**Contents:**
- Revenue metrics
- Operating expenses
- Net income trends
- Monthly comparisons

### 3. Financial Statements - Balance Sheet
**Description:** Assets, liabilities, and equity statements
**URL:** `https://app.cascadedebt.com/analytics/financials/statements?pid=abaco&tab=balance-sheet`
**Format:** Exportable via Export button (CSV, JSON, XLSX)
**Contents:**
- Total assets
- Cash position
- Debt obligations
- Net worth
- Equity ratios

## Key Portfolio Metrics (as of Dec 11, 2025)

### Traction
- **Total Unique Clients:** 332
- **Total Volume:** $56.61M USD
- **Outstanding Portfolio:** $7.36M USD
- **Active Loans:** 947
- **Active Borrowers:** 118

### Risk Metrics
- **PAR90 (Latest):** 0.68%
- **RDR90 @ 12 Months:** 0.93%
- **Collection Rate:** 41.26%
- **Average APR:** 38.98%

### Financial Summary
- **Total Assets:** $6.2M USD
- **Cash Balance:** $287K USD
- **Net Income:** -$3.1M USD
- **Debt/Equity Ratio:** 1.93
- **Runway:** 48 months

## How to Export Data

1. **Login to Cascade:** Navigate to `https://app.cascadedebt.com/`
2. **Select Portfolio:** Ensure `pid=abaco` is selected
3. **Navigate to desired section** by copying a URL from this document and pasting it into your browser
4. **Click Export button** (top right of most analytics pages)
5. **Choose format:** CSV, JSON, XLSX, or PDF
6. **Download file** to local system

## Export Button Formats Available

- **PNG** - Image export of charts
- **JPG** - Image export
- **PDF** - Document export
- **JSON** - Structured data
- **CSV** - Tabular data
- **XLSX** - Excel format
- **HTML** - Web format

## Additional Analytics Sections

### Risk Analytics
- [Key Indicators](https://app.cascadedebt.com/analytics/risk/indicators?pid=abaco)
- [Traction](https://app.cascadedebt.com/analytics/risk/traction?pid=abaco)
- [Delinquency](https://app.cascadedebt.com/analytics/risk/delinquency?pid=abaco)
- [Collection](https://app.cascadedebt.com/analytics/risk/collection?pid=abaco)
- [Curves](https://app.cascadedebt.com/analytics/risk/curves?pid=abaco)
- [Cohort](https://app.cascadedebt.com/analytics/risk/cohort?pid=abaco)
- [Characteristics](https://app.cascadedebt.com/analytics/risk/characteristics?pid=abaco)

### Financial Analytics
- Overview: `https://app.cascadedebt.com/analytics/financials/overview?pid=abaco`
- Key Indicators: `https://app.cascadedebt.com/analytics/financials/key-indicators?pid=abaco`
- Statements: `https://app.cascadedebt.com/analytics/financials/statements?pid=abaco`

### Analytics Pro (Advanced)
- Collection Categories: `https://app.cascadedebt.com/analytics-pro/categories/collection?pid=abaco`

## Notes

- All URLs require authentication to Cascade Debt platform
- Data updates typically occur daily
- Export limits may apply based on subscription tier
- Historical data available from January 2023 onwards
- Currency: USD (with spot exchange rate conversions available)

## Contact & Support

- **Platform:** Cascade Debt
- **Support:** https://support.cascadedebt.com
- **Documentation:** https://knowledgebase.cascadedebt.com

---
*Document maintained by: Abaco Analytics Team*
*Repository: github.com/Abaco-Technol/abaco-loans-analytics*
