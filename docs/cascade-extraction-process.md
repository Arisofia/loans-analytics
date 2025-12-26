⚠️ **HISTORICAL DATA EXTRACTION - POINT-IN-TIME SNAPSHOT**

**DO NOT USE FOR CURRENT METRICS**

This document records a single extraction event (December 4, 2025) from Cascade Debt. All dollar amounts and metrics represent a historical snapshot only. Current data may have changed significantly.

**For current live metrics, use:**
- Real-time dashboard: See production validation reports
- Database query: `SELECT * FROM kpi_timeseries_daily ORDER BY date DESC LIMIT 1`

**Document Status:** Historical Archive (Extraction Date: 2025-12-04)  
**Data Freshness:** As of December 3, 2025 UTC (ARCHIVED)

---

# Cascade Debt Data Extraction Process

## Overview

This document records the complete extraction process of Cascade Debt platform data for Abaco Capital's loan analytics repository.

**Extraction Date**: December 4, 2025, 8:00 AM CST
**Data Freshness**: Current as of December 3, 2025 UTC
**Platform**: Cascade Debt (https://app.cascadedebt.com)
**Project**: Abaco Capital
**Extraction Method**: Direct page text extraction from Cascade UI

## Extracted Data Sources

### Phase 1: Analytics Views (Completed)

Successfully extracted 9 comprehensive analytics views:

1. **Traction Analytics**
   - Loan Volume: 55.02M USD (as of Dec 2, 2025)
   - Active Clients: 327 unique borrowers
   - 36 months of historical monthly data
   - URL: https://app.cascadedebt.com/analytics/risk/traction?pid=abaco

2. **Delinquency (Portfolio at Risk)**
   - PAR90: 1.61% (as of latest)
   - 36 months of historical PAR7 data
   - DPD breakdown: 7/30/60/90+ day buckets
   - URL: https://app.cascadedebt.com/analytics/risk/delinquency?pid=abaco

3. **Collection Rates**
   - Latest Collection Rate: 2.57% (Dec 31, 2025)
   - 36 months complete payment history
   - Total Payments Received vs Scheduled tracking
   - URL: https://app.cascadedebt.com/analytics/risk/collection?pid=abaco

4. **Curves (Conditional Default Rate)**
   - CDR Analysis: Current 0.91%
   - Single Month Mortality trends
   - Conditional Prepayment Rate data
   - URL: https://app.cascadedebt.com/analytics/risk/curves?pid=abaco

5. **Cohort Analysis** (Legacy - Previously extracted)
   - Vintage maturation patterns
   - Performance by origination cohort

6. **Loan Characteristics**
   - Average APR: 38.99% (Last 12 months)
   - Interest rate and term distributions
   - URL: https://app.cascadedebt.com/analytics/risk/characteristics?pid=abaco

7. **Cashflow Simulation**
   - CDR/CPR scenario modeling
   - Projected cash flows under various conditions
   - URL: https://app.cascadedebt.com/analytics/risk/cashflow-simulation?pid=abaco

8. **Financial Key Indicators** (Legacy)
   - Portfolio-level metrics dashboard

9. **Financial Statements** (Legacy)
   - Balance sheet and income statement data

### Phase 2: Monitor/Covenant Data (Completed)

Extracted covenant monitoring and facility-level data:

1. **Borrowing Base**
   - Total Receivable: $8,001,835.93 (as of Dec 2, 2025)
   - Total Eligible: $7,231,232.07
   - Discounted Balance: $6,809,339.34
   - Collateralization: 274.36%
   - Surplus: $3,487,278.80
   - DPD Discount Schedule (5 tiers): 0-7 DPD through 120+ DPD
   - URL: https://app.cascadedebt.com/manage/monitor/borrowing-base?pid=abaco

2. **Portfolio Covenants**
   - Default Ratio 30 DPD: 0.00%
   - Trigger Levels: 10% / 12% (soft/hard)
   - Status: PASS - No covenant breaches detected
   - URL: https://app.cascadedebt.com/manage/monitor/portfolio-covenants?pid=abaco

3. **Financial Covenants**
   - Debt/Equity Ratio: 1.93
   - Limit: 6.00
   - Compliance Status: PASS
   - Measurement Date: 2025-03-31
   - URL: https://app.cascadedebt.com/manage/monitor/financial-covenants?pid=abaco

4. **Payment Schedule**
   - Next Payment: $75,000 scheduled for 2025-12-31
   - Cash Available: $249,323.89
   - Principal Outstanding: $2,000,000
   - Complete payment schedule through Q4 2028 (15+ periods)
   - URL: https://app.cascadedebt.com/manage/monitor/cashflows?pid=abaco

5. **Document Centre (Actions)**
   - Advance Requests: 4 documents on file
   - Disbursement Requests: Multiple tranches
   - Status tracking for each document
   - URL: https://app.cascadedebt.com/manage/monitor/actions?pid=abaco&tab=document-centre
