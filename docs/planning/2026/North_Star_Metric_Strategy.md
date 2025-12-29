⚠️ **STRATEGIC PLANNING DOCUMENT - 2026 TARGETS ONLY**

**DO NOT USE THESE NUMBERS IN PRODUCTION WORKFLOWS**

This document contains strategic goals and planning assumptions for 2026. All dollar amounts, metrics, and targets are planning hypotheses, not current state data.

**For current metrics, query live data sources:**
- AUM: `SELECT SUM(outstanding_principal) FROM fact_loans WHERE status='active'`
- NPL: `SELECT * FROM kpi_timeseries_daily WHERE metric='npl_180' ORDER BY date DESC LIMIT 1`
- Portfolio Health: See production validation report

**Document Status:** Strategic Planning (Resolved: 2025-12-26)  
**Last Review:** 2025-12-26

---

# 🧭 Abaco 2026 — North Star Metric Strategy (NSM)

## 1. Executive summary

**Goal:**

Align the organization around a single metric that captures value creation and sustainable growth for the B2B factoring business.

**Recommended NSM:**

> **Weekly/Monthly Recurrent TPV from Active Clients**

This measures the total processed volume from clients who repeat, reflecting retention, expansion, and portfolio health. It is actionable every week and directly connected to revenue, risk, and governance.

**How it connects to execution:**

- Anchors the origination → cashflow funnel (pancake/replines) by measuring only clients who repeat and generate collections.
- Uses existing guardrails (rotation ≥4.5×, default/NPL <4%, Top-10 concentration ≤30%, single-obligor ≤4%).
- Feeds weekly/monthly board-pack and operational dashboard monitoring (alerts for concentration, DPD/NPL, TPV drops by bucket or channel).

## 2. Context and strategic theses

1. **Target market:** Formal SMEs using accounts receivable for liquidity; e-invoicing adoption eases origination and monitoring.
2. **Competitive edge:** Debtor-centric risk engine and pricing segmented by CreditLineCategory (A–H).
3. **Strategic shift:** Move from measuring only origination to measuring recurrent platform usage and portfolio quality.
4. **Prior gap:** Tracking focused on invoices originated per month; it missed recurrence, expansion, and real cashflow.

## 3. Value engine and key indicators

| Stage | SME action | Value to Abaco | Related metrics |
| --- | --- | --- | --- |
| Acquisition | Onboarding and first operation | New clients | Monthly new logos by segment (Micro/Small/Medium) |
| Engagement | Recurrent factoring usage | Recurrent TPV | **NSM:** Weekly/Monthly Recurrent TPV |
| Conversion | Invoice financing | Revenue and margin | % invoices financed, weighted APR |
| Retention/Expansion | Credit-line upsell | Higher LTV | TPV per recurrent client, bucket upgrades |
| Portfolio health | Collections and cures | Controlled risk | Default rate, DPD/NPL, debtor concentration |

## 4. Definition and calculation

**Metric:** Recurrent TPV from active clients (weekly/monthly).

- **Active clients:** Clients with ≥1 operation in the measurement window.
- **Recurrent:** Clients with ≥2 consecutive periods with TPV > 0 or those returning after ≥90 days (recovered).
- **Calculation:** Sum of Disbursement Amount of financed invoices from recurrent clients in the window.

**Supporting indicators:**

- Financing rate over submitted invoices
- Repeat rate (clients with operations in ≥2 consecutive periods)
- 12m cash-weighted rotation and replines vs plan
- Debtor and client concentration (single-obligor ≤4%, Top-10 ≤30%)
- Default rate 180+ and DPD>15
- Mix-weighted APR by CreditLineCategory

## 5. Alignment with 2025-2026 OKRs

| Objective | NSM-aligned key results | Owner |
| --- | --- | --- |
| Grow with risk control | AUM $7.4M→$16.3M; rotation ≥4.5×; NPL180+ <4%; real default <4%; Top-10 concentration ≤30% | CEO/CRO/CFO |
| Profitability and liquidity | Weighted APR 34–40%; cost of debt ≤13%; DSCR ≥1.2×; utilization 75–90% | CFO |
| Bucketed go-to-market | ≥1 close/KAM/month in $50–150k; upgrades $10–50k→$50–150k; MQL→SQL ≥35–50%; ≤$10k close rate ≥30% | Head of Sales/Head of Growth |
| Production-grade platform | Decision SLA ≤24h, funding SLA ≤48h in ≥90%; live rotation/replines/DPD/NPL panels; SLO ≥99.5% | CTO |
| Portfolio health & collections | CE 6M ≥96%; replines deviation by bucket ±2 p.p.; losses within band (<4%) | Head of Risk |

## 6. Governance and cadence

- **Monitoring:** Weekly (operational) and monthly (board pack) for the NSM and supporting KPIs.
- **Ownership:** NSM DRI: Head of Growth + CEO; Data maintains dashboards; Risk/Finance validate covenants.
- **Alerts:** Concentration breaches, DPD/NPL spikes, replines deviation, TPV drops by segment or channel.

## 7. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Recurrence drop in smaller buckets (G–H) | Adjust pricing/score, reinforce onboarding and reminders; prioritize prime debtors |
| Concentration in a few debtors | Debtor limits, automated alerts, and origination rebalance |
| Misalignment between origination and cashflow | Replines and cash-weighted rotation as guardrails; compare plan vs actual weekly |
| Data quality on invoices/collateral | DTE integration, automated validations, 100% assignment audit |

## 8. Why not use other metrics as the central NSM

- **Invoices originated per month:** Measures acquisition and gross volume only; misses recurrence, quality, and cashflow. Fintechs such as Fundbox, BlueVine, and Kredito24 moved from this to recurrent TPV as they scaled.
- **LTV/CAC:** Critical for unit economics and investor reporting, but slow and aggregated; it does not govern weekly pulse or portfolio quality. SaaS/fintech leaders use it as a complementary metric, not as the NSM.

## 9. NSM benchmarks in the industry

- **Recurrent TPV/GMV:** Stripe, Square, PayPal, Shopify, MercadoPago, Konfio.
- **Recurrent activity (SaaS):** Slack (Weekly Active Teams), Dropbox (files shared), Zoom (meetings), HubSpot (MQLs per user).

## 10. Next steps

1. Publish the recurrent TPV panel with cuts by client (new/recurrent/recovered), bucket, and debtor.
2. Activate alerts for concentration and rotation/replines drops vs plan.
3. Link funnels by channel (Digital ≤$10k, Mixed $10–50k, KAM $50–150k) to the NSM to optimize CAC and churn.
4. Report the NSM and supporting KPIs in the weekly/monthly/QBR cadence.
