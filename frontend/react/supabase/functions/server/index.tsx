/**
 * Supabase Edge Function — Hono server for ÁBACO Loans Analytics
 * Serves data sections for the React frontend via KV store.
 *
 * Endpoints:
 *   GET  /make-server-a903c193/data/:section  — read section data
 *   PUT  /make-server-a903c193/data/:section  — write section data
 *   POST /make-server-a903c193/seed           — seed default data
 *
 * Deploy: `supabase functions deploy server`
 */

import { Hono } from "jsr:@hono/hono";
import { cors } from "jsr:@hono/hono/cors";
import { logger } from "jsr:@hono/hono/logger";
import * as kv from "./kv_store.tsx";

const app = new Hono().basePath("/make-server-a903c193");

app.use("*", cors());
app.use("*", logger());

// ─── Default seed data ───────────────────────────────────────────
const DEFAULT_DATA: Record<string, unknown> = {
  summary: {
    kpis: {
      total_outstanding: 8_520_000,
      active_loans: 356,
      par30: 5.7,
      expected_loss: 2.4,
      collection_rate: 97.8,
      active_borrowers: 312,
    },
    alerts: [
      { id: "a1", type: "risk", message: "PAR30 is at 5.7% and above covenant max of 4.0%", severity: "critical", timestamp: "2026-03-28T10:30:00Z" },
      { id: "a2", type: "collections", message: "Collection rate at 97.8% is below 98.5% covenant floor", severity: "critical", timestamp: "2026-03-28T09:00:00Z" },
      { id: "a3", type: "compliance", message: "2 active covenant breaches require lender update", severity: "warning", timestamp: "2026-03-28T08:00:00Z" },
    ],
    cashflow_trend: [
      { month: "Aug", inflow: 1200000, outflow: 980000 },
      { month: "Sep", inflow: 1350000, outflow: 1020000 },
      { month: "Oct", inflow: 1280000, outflow: 1100000 },
      { month: "Nov", inflow: 1420000, outflow: 1050000 },
      { month: "Dec", inflow: 1380000, outflow: 1150000 },
      { month: "Jan", inflow: 1450000, outflow: 1080000 },
    ],
    portfolio_mix: [
      { name: "Current", value: 72, color: "#a78bfa" },
      { name: "1-30 DPD", value: 15, color: "#f59e0b" },
      { name: "31-60 DPD", value: 8, color: "#f97316" },
      { name: "61-90 DPD", value: 3, color: "#ef4444" },
      { name: "90+ DPD", value: 2, color: "#dc2626" },
    ],
    health_summary: {
      credit_quality: "Fair",
      liquidity: "Strong",
      profitability: "Good",
      growth: "Moderate",
    },
  },

  portfolio: {
    metrics: { aum: 8_520_000, active_loans: 356, avg_apr: 35.4, default_rate: 5.7 },
    outstanding_trend: [
      { month: "Aug", outstanding: 7200000 },
      { month: "Sep", outstanding: 7450000 },
      { month: "Oct", outstanding: 7680000 },
      { month: "Nov", outstanding: 7900000 },
      { month: "Dec", outstanding: 8050000 },
      { month: "Jan", outstanding: 8150000 },
    ],
    status_distribution: [
      { name: "Current", value: 246, color: "#a78bfa" },
      { name: "Grace Period", value: 38, color: "#60a5fa" },
      { name: "Delinquent", value: 42, color: "#f59e0b" },
      { name: "Default", value: 10, color: "#ef4444" },
      { name: "Paid Off", value: 6, color: "#34d399" },
    ],
  },

  risk: {
    metrics: { par30: 5.7, par60: 3.2, par90: 1.9, expected_loss: 2.4 },
    risk_alerts: [
      { id: "r1", message: "Vintage Q3-2024 showing elevated roll rates", severity: "warning" },
      { id: "r2", message: "Concentration risk: top 10 borrowers = 18% of portfolio", severity: "warning" },
      { id: "r3", message: "Expected loss within acceptable range", severity: "info" },
    ],
    delinquency_trend: [
      { month: "Jul", par30: 3.8, par60: 2.1, par90: 1.2 },
      { month: "Aug", par30: 4.1, par60: 2.3, par90: 1.3 },
      { month: "Sep", par30: 4.4, par60: 2.5, par90: 1.4 },
      { month: "Oct", par30: 4.7, par60: 2.7, par90: 1.5 },
      { month: "Nov", par30: 5.0, par60: 2.9, par90: 1.6 },
      { month: "Dec", par30: 5.2, par60: 3.0, par90: 1.7 },
      { month: "Jan", par30: 5.4, par60: 3.1, par90: 1.8 },
      { month: "Feb", par30: 5.6, par60: 3.2, par90: 1.9 },
      { month: "Mar", par30: 5.7, par60: 3.2, par90: 1.9 },
    ],
  },

  collections: {
    metrics: { collection_rate: 94.2, dpd_over_30: 52, collections_mtd: 485000, contact_rate: 78.5 },
    dpd_distribution: [
      { bucket: "1-15 DPD", count: 45, amount: 180000, percentage: 35 },
      { bucket: "16-30 DPD", count: 28, amount: 145000, percentage: 22 },
      { bucket: "31-60 DPD", count: 32, amount: 210000, percentage: 25 },
      { bucket: "61-90 DPD", count: 12, amount: 95000, percentage: 10 },
      { bucket: "90+ DPD", count: 8, amount: 85000, percentage: 8 },
    ],
    collections_trend: [
      { month: "Aug", collected: 420000, target: 450000 },
      { month: "Sep", collected: 445000, target: 460000 },
      { month: "Oct", collected: 460000, target: 470000 },
      { month: "Nov", collected: 475000, target: 480000 },
      { month: "Dec", collected: 490000, target: 490000 },
      { month: "Jan", collected: 485000, target: 500000 },
    ],
  },

  treasury: {
    metrics: { cash_reserve: 2_400_000, liquidity_ratio: 1.8, advance_rate: 75.2, utilization: 68.5 },
    cashflow_projection: [
      { week: "W1", inflow: 350000, outflow: 280000, net: 70000 },
      { week: "W2", inflow: 320000, outflow: 310000, net: 10000 },
      { week: "W3", inflow: 380000, outflow: 260000, net: 120000 },
      { week: "W4", inflow: 340000, outflow: 290000, net: 50000 },
    ],
    eligible_portfolio: [
      { category: "Current Loans", amount: 6000000, eligible: 5400000, rate: 90 },
      { category: "1-30 DPD", amount: 1200000, eligible: 720000, rate: 60 },
      { category: "31-60 DPD", amount: 650000, eligible: 195000, rate: 30 },
      { category: "61+ DPD", amount: 300000, eligible: 0, rate: 0 },
    ],
  },

  sales: {
    metrics: { new_loans_mtd: 48, repeat_rate: 32.5, cac: 125, ltv_cac_ratio: 4.2 },
    sales_funnel: [
      { stage: "Leads", count: 520 },
      { stage: "Applications", count: 185 },
      { stage: "Approved", count: 92 },
      { stage: "Disbursed", count: 48 },
    ],
    funnel_rates: { application_rate: 35.6, approval_rate: 49.7 },
    growth_trajectory: [
      { month: "Aug", disbursements: 1800000, target: 1750000 },
      { month: "Sep", disbursements: 1950000, target: 1850000 },
      { month: "Oct", disbursements: 2100000, target: 2000000 },
      { month: "Nov", disbursements: 2050000, target: 2100000 },
      { month: "Dec", disbursements: 2250000, target: 2200000 },
      { month: "Jan", disbursements: 2180000, target: 2300000 },
    ],
  },

  vintage: {
    metrics: { avg_mob: 8.5, vintage_default: 3.2, roll_rate_30_60: 15.8, cure_rate: 35.2 },
    vintage_curves: [
      { mob: 1, "Q1-24": 0.5, "Q2-24": 0.8, "Q3-24": 1.0, "Q4-24": 0.6, "Q1-25": 0.4 },
      { mob: 2, "Q1-24": 1.2, "Q2-24": 1.5, "Q3-24": 2.1, "Q4-24": 1.3, "Q1-25": 0.9 },
      { mob: 3, "Q1-24": 1.8, "Q2-24": 2.2, "Q3-24": 3.0, "Q4-24": 2.0, "Q1-25": null },
      { mob: 4, "Q1-24": 2.3, "Q2-24": 2.8, "Q3-24": 3.6, "Q4-24": null, "Q1-25": null },
      { mob: 5, "Q1-24": 2.7, "Q2-24": 3.2, "Q3-24": null, "Q4-24": null, "Q1-25": null },
      { mob: 6, "Q1-24": 3.0, "Q2-24": null, "Q3-24": null, "Q4-24": null, "Q1-25": null },
    ],
    vintage_lines: [
      { key: "Q1-24", name: "Q1 2024", color: "#a78bfa" },
      { key: "Q2-24", name: "Q2 2024", color: "#60a5fa" },
      { key: "Q3-24", name: "Q3 2024", color: "#f59e0b" },
      { key: "Q4-24", name: "Q4 2024", color: "#34d399" },
      { key: "Q1-25", name: "Q1 2025", color: "#f472b6" },
    ],
    roll_rate_matrix: [
      { from: "Current", to: "1-30 DPD", rate: 8.2 },
      { from: "1-30 DPD", to: "31-60 DPD", rate: 15.8 },
      { from: "31-60 DPD", to: "61-90 DPD", rate: 22.5 },
      { from: "61-90 DPD", to: "90+ DPD", rate: 35.0 },
      { from: "1-30 DPD", to: "Current", rate: 35.2 },
    ],
    cohort_performance: [
      { cohort: "Q1-2024", disbursed: 3200000, default_rate: 3.0, recovery_rate: 42.0 },
      { cohort: "Q2-2024", disbursed: 3500000, default_rate: 3.5, recovery_rate: 38.0 },
      { cohort: "Q3-2024", disbursed: 3800000, default_rate: 4.2, recovery_rate: 35.0 },
      { cohort: "Q4-2024", disbursed: 4100000, default_rate: 2.8, recovery_rate: 45.0 },
    ],
  },

  "unit-economics": {
    customer_economics: { ltv: 525, cac: 125, ltv_cac_ratio: 4.2, payback_period: 4 },
    profitability: { nim: 28.5, cost_of_risk: 3.8, roa: 8.2, roe: 22.5 },
    reconciliation: [
      { item: "Interest Revenue", calculated: 2450000, reported: 2430000, variance: 0.82, status: "OK" },
      { item: "Fee Income", calculated: 185000, reported: 190000, variance: -2.63, status: "OK" },
      { item: "Provision Expense", calculated: 310000, reported: 295000, variance: 5.08, status: "WARNING" },
      { item: "Operating Costs", calculated: 580000, reported: 575000, variance: 0.87, status: "OK" },
    ],
    gross_margin_trend: [
      { month: "Aug", margin: 62.5 },
      { month: "Sep", margin: 63.2 },
      { month: "Oct", margin: 61.8 },
      { month: "Nov", margin: 64.0 },
      { month: "Dec", margin: 63.5 },
      { month: "Jan", margin: 64.2 },
    ],
    ticket_segmentation: [
      { band: "$0-500", count: 120, amount: 42000, default_rate: 4.5 },
      { band: "$500-1K", count: 95, amount: 71000, default_rate: 3.2 },
      { band: "$1K-2K", count: 68, amount: 102000, default_rate: 2.8 },
      { band: "$2K-5K", count: 42, amount: 145000, default_rate: 2.1 },
      { band: "$5K+", count: 17, amount: 125000, default_rate: 1.5 },
    ],
  },

  covenants: {
    metrics: { advance_rate: 78.0, dscr: 1.28, max_default: 5.7, collection_rate: 97.8 },
    compliance_status: "BREACH",
    repline_distribution: [
      { category: "Term Loans", amount: 4200000, limit: 5000000, utilization: 84, status: "OK" },
      { category: "Revolving", amount: 2100000, limit: 3000000, utilization: 70, status: "OK" },
      { category: "Micro-credit", amount: 1850000, limit: 2000000, utilization: 92.5, status: "WARNING" },
    ],
    collection_rate_trend: [
      { month: "Aug", rate: 95.5, threshold: 90 },
      { month: "Sep", rate: 95.2, threshold: 90 },
      { month: "Oct", rate: 94.8, threshold: 90 },
      { month: "Nov", rate: 94.5, threshold: 90 },
      { month: "Dec", rate: 94.0, threshold: 90 },
      { month: "Jan", rate: 94.2, threshold: 90 },
    ],
    covenants: [
      { name: "Advance Rate", current: 78.0, threshold: 80, status: "PASS", description: "Max advance rate on eligible receivables" },
      { name: "DSCR", current: 1.28, threshold: 1.25, status: "PASS", description: "Debt service coverage ratio minimum" },
      { name: "Max Default Rate", current: 5.7, threshold: 4.0, status: "BREACH", description: "Maximum portfolio PAR30/default covenant rate" },
      { name: "Collection Rate", current: 97.8, threshold: 98.5, status: "BREACH", description: "Minimum monthly collection covenant rate" },
      { name: "Concentration Limit", current: 19.2, threshold: 20, status: "WATCH", description: "Max exposure to top 10 borrowers" },
    ],
  },

  executive: {
    business_state: "HEALTHY",
    confidence: 0.87,
    kpis: { portfolio_health: 82, revenue_trend: "↑ +8.2%", risk_score: 28, liquidity_ratio: 1.8 },
    alerts: [
      { id: "e1", type: "risk", message: "PAR30 trending upward — monitor closely", severity: "warning", action: "View Risk" },
      { id: "e2", type: "growth", message: "Q1 origination pace ahead of target", severity: "info", action: "View Sales" },
    ],
    prioritized_actions: [
      { priority: 1, agent: "Risk Agent", action: "Analyze Q3-2024 vintage deterioration", routed_to: "Credit Team" },
      { priority: 2, agent: "Collections Agent", action: "Intensify contact for 31-60 DPD bucket", routed_to: "Collections Team" },
      { priority: 3, agent: "Treasury Agent", action: "Prepare monthly lender report", routed_to: "Finance Team" },
    ],
  },
  "investor-room": {
    covenant_monitoring: [
      { covenant: "PAR30 ≤ 4.0%", current: 5.7, threshold: 4.0, status: "BREACH", headroom: -1.7 },
      { covenant: "Collection Rate ≥ 98.5%", current: 97.8, threshold: 98.5, status: "BREACH", headroom: -0.7 },
      { covenant: "Advance Rate ≤ 80.0%", current: 78.0, threshold: 80.0, status: "PASS", headroom: 2.0 },
      { covenant: "DSCR ≥ 1.25x", current: 1.28, threshold: 1.25, status: "PASS", headroom: 0.03 },
    ],
    scenarios: [
      { name: "Base", weight: 0.5, irr: 18.2, expected_loss: 2.4, par30: 5.7 },
      { name: "Stress", weight: 0.3, irr: 14.1, expected_loss: 4.2, par30: 7.1 },
      { name: "Recovery", weight: 0.2, irr: 21.5, expected_loss: 1.8, par30: 4.9 },
    ],
    corrected_metrics: { ppc: 412.4, ppp: 379.8, ppc_ppp_gap: 32.6 },
    cohort_table: [
      { vintage: "2024-Q4", disbursed: 1820000, irr: 17.9, expected_loss: 2.2 },
      { vintage: "2025-Q1", disbursed: 1930000, irr: 18.4, expected_loss: 2.5 },
      { vintage: "2025-Q2", disbursed: 2010000, irr: 18.0, expected_loss: 2.8 },
    ],
  },
  marketing: {
    summary: { cac: 125.0, ltv: 2357.64, roi: 1786.11, avg_ticket: 4366.0 },
    channel_performance: [
      { channel: "Referidos", leads: 120, funded: 52, cac: 80, quality: "high" },
      { channel: "Digital", leads: 380, funded: 85, cac: 150, quality: "medium" },
      { channel: "KAM directo", leads: 95, funded: 48, cac: 95, quality: "high" },
      { channel: "Alianzas", leads: 65, funded: 22, cac: 180, quality: "medium" },
    ],
    segment_performance: [
      { segment: "transporte", count: 128, avg_ticket: 4800, default_rate: 1.2, ltv: 2592, roi: 2140.5 },
      { segment: "comercio", count: 184, avg_ticket: 4300, default_rate: 1.6, ltv: 2322, roi: 1894.8 },
      { segment: "servicios", count: 141, avg_ticket: 3950, default_rate: 2.3, ltv: 2133, roi: 1650.2 },
      { segment: "agro", count: 96, avg_ticket: 5100, default_rate: 2.9, ltv: 2754, roi: 1422.1 },
    ],
    invisible_primes: {
      count: 46,
      description: "Customers with low credit score but strong repayment behavior",
      avg_dpd: 5.2,
      avg_ticket: 3056.2,
    },
  },
  "ai-decision-center": {
    business_state: "WATCH",
    confidence: 0.86,
    agents: [
      { name: "Risk Agent", status: "Active", confidence: 0.91, task: "Reduce PAR30 and roll-rate migration" },
      { name: "Collections Agent", status: "Active", confidence: 0.88, task: "Lift 31-60 DPD cure rates" },
      { name: "Treasury Agent", status: "Standby", confidence: 0.79, task: "Preserve covenant liquidity buffers" },
      { name: "Growth Agent", status: "Active", confidence: 0.83, task: "Scale invisible-prime channels" },
      { name: "Compliance Agent", status: "Alert", confidence: 0.94, task: "Resolve 2 active covenant breaches" },
    ],
    ranked_actions: [
      { rank: 1, action: "Tighten approvals for high-risk micro-segments", confidence: 0.92, owner: "Credit Committee" },
      { rank: 2, action: "Deploy daily collections sprint for 31-60 DPD", confidence: 0.89, owner: "Collections Lead" },
      { rank: 3, action: "Rebalance acquisition budget toward referral", confidence: 0.84, owner: "Growth Lead" },
    ],
    opportunities: [
      { title: "Invisible-prime payroll products", estimated_uplift_pct: 11.2 },
      { title: "Dynamic repricing for repeat borrowers", estimated_uplift_pct: 7.5 },
    ],
  },
};

// ─── Seed helper ─────────────────────────────────────────────────
async function ensureSeeded() {
  try {
    const check = await kv.get("data:summary");
    if (!check) {
      const entries = Object.entries(DEFAULT_DATA).map(([section, value]) => ({
        key: `data:${section}`,
        value,
      }));
      await kv.mset(entries);
      console.log(`[KV] Seeded ${entries.length} default data sections.`);
    }
  } catch (err) {
    console.error("[KV] Failed to check/seed default data:", err);
  }
}

app.get("/data/:section", async (c) => {
  const section = c.req.param("section");
  try {
    await ensureSeeded();
    const data = await kv.get(`data:${section}`);
    
    // Check if data exists in KV (respecting falsy values like 0, false, "")
    if (data !== null && data !== undefined) {
      return c.json(data);
    }
  } catch (err) {
    console.error(`[KV] Error fetching section ${section}:`, err);
  }

  // Fallback to static data if KV fails or is empty
  if (Object.prototype.hasOwnProperty.call(DEFAULT_DATA, section)) {
    return c.json(DEFAULT_DATA[section]);
  }

  return c.json({ error: "Section not found" }, 404);
});

app.put("/data/:section", async (c) => {
  const section = c.req.param("section");
  const body = await c.req.json();
  await kv.set(`data:${section}`, body);
  return c.json({ ok: true });
});

app.post("/seed", async (c) => {
  const entries = Object.entries(DEFAULT_DATA).map(([section, value]) => ({
    key: `data:${section}`,
    value,
  }));
  await kv.mset(entries);
  return c.json({ ok: true, sections: Object.keys(DEFAULT_DATA) });
});

export default app;
