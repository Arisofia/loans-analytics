# CEO Operating System OKR Overview (English)
This document summarizes the provided OKRs, risk guardrails, and near-term actions for the Abaco platform. It keeps the original content but structures it for quick reference.
## Data Model & Measurement Rules

- **Unit of analysis:** Each row in the core tables represents a **credit line/loan**; aggregations roll up to **client_id**.
- **Concentration:** Enforced **by client_id** (not payer). Top-10 clients by outstanding balance must remain **<30%**; single-obligor per client **<4%**.
- **Segmentation:** Balance buckets or quantiles are computed per loan/credit line, then summarized to client.
- **Customer type:** New, Recurrent, and Recovered are tagged at the **client_id** level and applied consistently to all their lines.
- **Risk grouping:** Delinquency, utilization, and covenant checks start at the **loan/credit line** level and then aggregate to client.
## OKR 1 — Growth (CGO)

- **Primary metric:** 500 active SMEs by Q4-26 (from 56; 8.9×). Monthly tracking with weekly acquisition targets.
- **Top-10 concentration:** <30% by client (currently 19.87%, maintain). Weekly monitoring; daily alerts if above threshold.
- **Single-obligor:** <4% per customer (policy). Weekly checks with alerts.
- **CAC targets:** <\$600 via embedded channels or <\$2K via KAM. Monthly cohort review.
- **DRI & cadence:** CGO; monthly business review.
## OKR 2 — Speed & Engagement (CPO + Head Credit Ops)

- 2,000 invoices/month submitted (≈4 per customer/month).
- Time-to-funding improvement: 48h → 12h via LoanPro + Taktile automation by Mar-26.
- Eligibility rate ≥75%; STP ≥80% with minimal manual work.
- **DRIs:** CPO + Head Credit Ops; bi-weekly cadence.
## OKR 3 — Quality & Guardrails (CRO)

- Default cohort <1.2% quarterly (vs 4% covenant).
- NPL180+ <4% of portfolio; 90-day holds trigger collections.
- Rotation ≥4.5× maintained (currently 5.5×) with seasonal monitoring.
- Data quality ≥95% with weekly audit and month-end remediation.
- Abaco Financial: wind down or separate; Abaco Tech: keep <1.5% default through scoring and early intervention.
- **DRI:** CRO; weekly credit committee.
## OKR 4 — Platform & Automation (CTO)

- LoanPro + Taktile Phase 1 live by Mar-26 (decision engine + monitoring dashboards).
- Front-end + CRM/backoffice operational by Dec-25 (HubSpot + customer portal).
- Embedded SDK for ISVs by Feb-26 with LoanPro/Taktile integration.
- Data warehouse operational by Jan-26 with ≤6h latency and BI dashboards.
- **DRI:** CTO; bi-weekly program review.
## OKR 5 — Funnel & Unit Economics (VP Sales + Head Digital)

- Monthly origination targets by phase (decline Q4-25 → acceleration Q3-26 → consolidation Q4-26).
- CAC optimization by channel: KAM $1.5K–2K; Digital $300–600; Embedded $50–150. Aim for 60% of new customers via embedded by Q4-26.
- LTV:CAC >4:1 blended (Embedded 27–100:1; Digital 5–10:1; KAM 1.8:1). Target 6–8:1 by Q4-26.
- Bucket growth: <$50K grow 50–60%; >$200K grow <10%; maintain Top-10 <30%.
- **DRIs:** VP Sales + Head Digital; weekly sales review.
## Finance/Capital (CFO)

- Facility per advance: 85% available; ineligible 5%; excess 5%; quarterly compliance.
- Maintain 3-month OpEx liquidity buffer; monitor burn and runway.
- EBITDA breakeven by H2-26 (Q4 positive cash generation).
- Series B capital confirmed by Q1-26 (if growth thesis holds).
- **DRI:** CFO; monthly board meeting.
## Reasons & Root Causes (Path Rationale)

- **Q4-2025 trough (-$903K):** holiday seasonality, Abaco Financial collapse, deliberate platform-build pause, slower factoring market. Planned consolidation.
- **Jan-2026 inflection (+$2,271K):** LoanPro + Taktile live (STP 80%+), embedded channels start, KAM team fully staffed, platform capacity ready, new fiscal-year spend.
- **Q2-2026 volatility (+$1,055K):** customer mix shifts, prepayment swings, natural churn (~25%/month), April dip managed by KAM reactivation. Normal dynamics.
- **Q3-2026 acceleration (+$3,084K):** platform maturity, 50–60% embedded originations, optimized unit economics, mid-year budget releases, operational scale.
- **Q4-2026 consolidation (+$1,916K):** shift to profitability over growth, market saturation (~4% reach), warehouse limits (85% advance), EBITDA positive; strategic deceleration.
- **Abaco Financial crisis:** unsustainable defaults (>8%), wrong segment, manual process, high CAC; solution is wind-down and consolidation into Abaco Technologies.
- **Abaco Technologies success:** better underwriting, embedded-ready product, right B2B SME segment, dedicated KAMs + digital marketing.
- **Bucket rebalancing:** favor <$50K (LTV:CAC >20:1) to reduce concentration risk; large customers carry risk with lower economics.
- **Data quality issues (78% complete):** missing KAM assignments, collateral, government exposure, and industry classification; weekly remediation planned by Nov-2025.
## Current vs Target Metrics

- **Current (Oct-14, 2025):** AUM $7,368K; 56 customers; rotation 5.5×; Top-10 concentration 19.87%; STP 40%; T2F 48h; EBITDA approx. -$15K/month; data quality 78%.
- **Target (Dec-2026):** AUM $16,419K; 500 customers; rotation ≥4.5×; default <1.5%; Top-10 <30%; single-obligor <4%; STP 80%+; T2F 12h; EBITDA +$50K/month; data quality >95%.
## Monthly Journey Highlights (Sep-2025 → Dec-2026)

- **Q4-2025:** planned trough (-$903K AUM, -$170K EBITDA).
- **Q1-2026:** inflection (+$3,899K AUM, +$20K EBITDA).
- **Q2-2026:** volatile growth (+$1,055K AUM, +$80K EBITDA).
- **Q3-2026:** acceleration (+$3,084K AUM, +$190K EBITDA).
- **Q4-2026:** consolidation (+$1,916K AUM, +$350K EBITDA).
## Immediate Actions (Oct-16 → Nov-16)

- Week 1: finalize Abaco Financial wind-down, classify unassigned customers, remediate data quality, kick off LoanPro integration, finalize Series B narrative, deliver board presentation.
- Week 2: pilot Taktile scoring, set up HubSpot, hire KAMs (1→4), launch digital campaigns, sign embedded ISV partnerships, deploy weekly dashboard.
- Week 3: platform testing, covenant monitoring alerts (Top-10, default, DPD), OKR tracking system, data warehouse design, finalize Series B deck, establish risk committee.
- Week 4: go-live readiness (LoanPro, Taktile), customer comms, stress testing, investor meetings, monthly KPI review, Q4 trough mitigation plan.
## Governance Cadence

- Weekly: CRO-led credit committee; VP Sales-led sales review.
- Bi-weekly: CTO tech standup; CPO product review.
- Monthly: CGO growth review; CFO board meeting.
- Quarterly: CEO board meeting; automated dashboard refresh daily at 6 AM UTC.
## Final Summary

- Non-linear path from $7.4M AUM and 56 customers to $16.4M and 500 customers by Dec-26 with embedded channels, platform automation, and disciplined guardrails.
- Focus on concentration by client (not payer), single-obligor limits, data quality improvement, and low-CAC embedded growth.
- Immediate priority: confirm strategy, align board/investors, accelerate platform build, expand team, ship dashboard, and launch Series B.
