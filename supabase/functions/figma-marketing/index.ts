/* eslint-disable no-console */
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
const backendEnv = Deno.env.get("BACKEND_KPI_URL");
if (!backendEnv) {
  console.error("BACKEND_KPI_URL is not configured in environment");
  throw new Error("Missing BACKEND_KPI_URL configuration");
}
const BACKEND_KPI_URL = backendEnv;
const FETCH_TIMEOUT_MS = 5000;
serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
      },
    });
  }
  // Only allow GET
  if (req.method !== "GET") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }
  let kpiRawData: Record<string, any> = {};
  let usesDemoMode = false;
  try {
    // Fetch from backend with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    const kpiResponse = await fetch(BACKEND_KPI_URL, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (kpiResponse.ok) {
      kpiRawData = await kpiResponse.json();
      usesDemoMode =
        !kpiRawData.extended_kpis?.unit_economics ||
        !kpiRawData.extended_kpis?.customer_types ||
        !kpiRawData.extended_kpis?.intensity_segmentation;
    }
  } catch (error) {
    console.error(
      "Backend unavailable, returning empty dataset:",
      error instanceof Error ? error.message : "Unknown error",
    );
    usesDemoMode = true;
  }
  const timestamp = new Date().toISOString();
  const unitEconomicsHistorical =
    (kpiRawData.extended_kpis?.unit_economics as Array<
      Record<string, unknown>
    >) || [];
  const churnMetricsArray =
    (kpiRawData.extended_kpis?.churn_90d_metrics as Array<
      Record<string, unknown>
    >) || [];
  const latestChurn = churnMetricsArray?.[0] || {};
  const marketingDashboard = {
    version: "2.0",
    timestamp,
    last_updated: kpiRawData.timestamp || timestamp,
    unit_economics: {
      cac_usd: kpiRawData.cac_usd || 0,
      ltv_realized: kpiRawData.ltv_realized || 0,
      ltv_cac_ratio: kpiRawData.ltv_cac_ratio || 0,
      revenue_per_client_monthly:
        kpiRawData.revenue_per_active_client_monthly || 0,
      revenue_per_client_annual:
        kpiRawData.revenue_per_active_client_annual || 0,
      historical: unitEconomicsHistorical || [],
    },
    customer_acquisition: {
      new_clients_month:
        (
          (kpiRawData.extended_kpis as Record<string, unknown>)
            ?.executive_strip as Record<string, unknown>
        )?.new_clients || 0,
      recurrent_clients:
        (
          (kpiRawData.extended_kpis as Record<string, unknown>)
            ?.executive_strip as Record<string, unknown>
        )?.recurrent_clients || 0,
      recovered_clients:
        (
          (kpiRawData.extended_kpis as Record<string, unknown>)
            ?.executive_strip as Record<string, unknown>
        )?.recovered_clients || 0,
      total_active: kpiRawData.active_clients || 0,
      by_type:
        (kpiRawData.extended_kpis?.customer_types as Array<
          Record<string, unknown>
        >) || [],
      by_segment:
        (kpiRawData.extended_kpis?.customer_classification as Array<
          Record<string, unknown>
        >) || [],
    },
    customer_retention: {
      churn_90d_rate: (latestChurn?.churn90d_pct as number) || 0,
      active_90d: (latestChurn?.active_90d as number) || 0,
      inactive_90d: (latestChurn?.inactive_90d as number) || 0,
      churn_dollar: (latestChurn?.churn_dollar as number) || 0,
      historical: churnMetricsArray || [],
    },
    segmentation: {
      by_intensity:
        (kpiRawData.extended_kpis?.intensity_segmentation as Array<
          Record<string, unknown>
        >) || [],
      by_line_size:
        (kpiRawData.extended_kpis?.line_size_segmentation as Array<
          Record<string, unknown>
        >) || [],
      by_ticket_band:
        (kpiRawData.extended_kpis?.average_ticket as Array<
          Record<string, unknown>
        >) || [],
    },
    growth_metrics: {
      monthly_disbursements:
        (
          (kpiRawData.extended_kpis as Record<string, unknown>)
            ?.executive_strip as Record<string, unknown>
        )?.total_disbursements || 0,
      mom_growth_pct: kpiRawData.mom_growth_pct || 0,
      yoy_growth_pct: kpiRawData.yoy_growth_pct || 0.0,
      throughput_12m:
        (
          (kpiRawData.extended_kpis as Record<string, unknown>)
            ?.throughput_metrics as Array<Record<string, unknown>>
        )?.[0]?.outstanding || 0,
      rotation_rate: kpiRawData.rotation || 0,
      historical:
        (kpiRawData.extended_kpis?.figma_dashboard as Array<
          Record<string, unknown>
        >) || [],
    },
    revenue_analytics: {
      monthly_revenue_usd: kpiRawData.monthly_revenue_usd || 0,
      weighted_apr: kpiRawData.weighted_apr || 0,
      weighted_fee_rate: kpiRawData.weighted_fee_rate || 0,
      weighted_effective_rate:
        (kpiRawData.weighted_apr || 0) + (kpiRawData.weighted_fee_rate || 0),
      recurrence_pct:
        (
          (kpiRawData.extended_kpis as Record<string, unknown>)
            ?.monthly_pricing as Array<Record<string, unknown>>
        )?.[0]?.recurrence_pct || 0,
      historical_pricing:
        (kpiRawData.extended_kpis?.monthly_pricing as Array<
          Record<string, unknown>
        >) || [],
    },
    payment_behavior: {
      payment_timing:
        (kpiRawData.extended_kpis?.payment_timing as Array<
          Record<string, unknown>
        >) || [],
      collection_rates:
        (kpiRawData.extended_kpis?.collection_rate as Array<
          Record<string, unknown>
        >) || [],
      average_ticket_size: kpiRawData.average_ticket || 0,
    },
    concentration_risk: {
      historical:
        (kpiRawData.extended_kpis?.concentration as Array<
          Record<string, unknown>
        >) || [],
    },
    risk_trends: {
      monthly_historical:
        (kpiRawData.extended_kpis?.monthly_risk as Array<
          Record<string, unknown>
        >) || [],
    },
    agent_comments: {
      marketing: generateMarketingComments(kpiRawData),
      retention: generateRetentionComments(kpiRawData),
      growth: generateGrowthComments(kpiRawData),
      unit_economics: generateUnitEconomicsComments(kpiRawData),
    },
    metadata: {
      data_freshness_hours: usesDemoMode ? null : 0,
      total_metrics_available: 56,
      last_sync: timestamp,
      backend_url: BACKEND_KPI_URL,
      demo_mode: usesDemoMode,
      notes: usesDemoMode
        ? "Backend unavailable. Returning empty dataset."
        : "Using REAL data from backend - all fields populated",
    },
  };
  return new Response(JSON.stringify(marketingDashboard), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=3600",
      "X-Data-Type": "marketing",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "X-Demo-Mode": usesDemoMode ? "true" : "false",
    },
  });
});
function generateMarketingComments(
  data: Record<string, unknown>,
): Record<string, string> {
  const cac = (data.cac_usd as number) || 0;
  const ltv = (data.ltv_realized as number) || 0;
  const newClients =
    ((
      (data.extended_kpis as Record<string, unknown>)
        ?.executive_strip as Record<string, unknown>
    )?.new_clients as number) || 0;
  const comments: Record<string, string> = {};
  if (ltv > 0 && cac > 0) {
    const ratio = ltv / cac;
    if (ratio > 2) {
      comments.unit_economics =
        "✓ Excellent unit economics. LTV/CAC ratio above 2.0x. Acquisition profitability strong.";
    } else if (ratio > 1.5) {
      comments.unit_economics =
        "⚠ Healthy unit economics. LTV/CAC ratio 1.5-2.0x. Monitor for margin compression.";
    } else if (ratio > 1) {
      comments.unit_economics =
        "⚠ Unit economics under pressure. LTV/CAC <1.5x. Reassess CAC spend and pricing.";
    } else {
      comments.unit_economics =
        "✗ CRITICAL: Unit economics broken. LTV/CAC <1.0x. Acquisition loss-making.";
    }
  }
  if (newClients > 15) {
    comments.acquisition =
      "✓ Strong new client acquisition. Marketing efficiency high.";
  } else if (newClients > 10) {
    comments.acquisition =
      "⚠ Acquisition on track but decelerating. Monitor lead quality.";
  } else if (newClients > 5) {
    comments.acquisition =
      "⚠ New client acquisition below targets. Escalate marketing spend.";
  } else {
    comments.acquisition =
      "✗ CRITICAL: Acquisition stalled. Activate emergency acquisition programs.";
  }
  return comments;
}
function generateRetentionComments(
  data: Record<string, unknown>,
): Record<string, string> {
  const churnData = (
    (data.extended_kpis as Record<string, unknown>)?.churn_90d_metrics as Array<
      Record<string, unknown>
    >
  )?.[0];
  const churn90d = (churnData?.churn90d_pct as number) || 0;
  const revenuePer = (data.revenue_per_active_client_monthly as number) || 0;
  const comments: Record<string, string> = {};
  if (churn90d < 10) {
    comments.churn = "✓ Churn rate excellent. Customer retention strong.";
  } else if (churn90d < 15) {
    comments.churn = "⚠ Churn acceptable. Monitor for degradation trends.";
  } else if (churn90d < 20) {
    comments.churn = "⚠ Churn elevated. Activate retention initiatives.";
  } else {
    comments.churn =
      "✗ CRITICAL: Churn unsustainable. Emergency retention program required.";
  }
  if (revenuePer > 60) {
    comments.ltv =
      "✓ Revenue per client strong. Cross-sell and pricing optimized.";
  } else if (revenuePer > 50) {
    comments.ltv =
      "⚠ Revenue per client adequate. Identify upsell opportunities.";
  } else {
    comments.ltv = "⚠ Revenue per client low. Review pricing and product mix.";
  }
  return comments;
}
function generateGrowthComments(
  data: Record<string, unknown>,
): Record<string, string> {
  const mom = (data.mom_growth_pct as number) || 0;
  const yoy = (data.yoy_growth_pct as number) || 0;
  const rotation = (data.rotation as number) || 0;
  const comments: Record<string, string> = {};
  if (mom > 5) {
    comments.mom = "✓ Strong monthly growth. Portfolio expansion accelerating.";
  } else if (mom > 0) {
    comments.mom = "⚠ Growth positive but slowing. Monitor pipeline health.";
  } else if (mom > -5) {
    comments.mom =
      "⚠ Slight contraction. Investigate seasonal or market factors.";
  } else {
    comments.mom =
      "✗ CRITICAL: Significant contraction. Investigate structural issues.";
  }
  if (yoy > 20) {
    comments.yoy =
      "✓ Excellent year-over-year growth. Strategic initiatives succeeding.";
  } else if (yoy > 10) {
    comments.yoy = "⚠ YoY growth good. Review growth levers for acceleration.";
  } else if (yoy > 0) {
    comments.yoy = "⚠ Modest YoY growth. Competitive pressure detected.";
  } else {
    comments.yoy = "✗ CRITICAL: YoY contraction. Activate growth initiatives.";
  }
  if (rotation > 3.5) {
    comments.rotation = "✓ Portfolio turnover excellent. High loan velocity.";
  } else if (rotation > 2.5) {
    comments.rotation =
      "⚠ Portfolio rotation adequate. Origination execution solid.";
  } else {
    comments.rotation = "⚠ Rotation declining. Portfolio becoming stale.";
  }
  return comments;
}
function generateUnitEconomicsComments(
  data: Record<string, unknown>,
): Record<string, string> {
  const cac = (data.cac_usd as number) || 0;
  const ltv = (data.ltv_realized as number) || 0;
  const revenuePer = (data.revenue_per_active_client_monthly as number) || 0;
  const comments: Record<string, string> = {};
  if (cac < 300) {
    comments.cac = "✓ CAC efficient. Marketing spend optimized.";
  } else if (cac < 400) {
    comments.cac = "⚠ CAC acceptable. Monitor for creep.";
  } else if (cac < 500) {
    comments.cac = "⚠ CAC elevated. Review channel efficiency.";
  } else {
    comments.cac = "✗ CRITICAL: CAC unsustainable. Cost reduction needed.";
  }
  if (ltv > 800) {
    comments.ltv = "✓ LTV excellent. Customer value extraction optimized.";
  } else if (ltv > 600) {
    comments.ltv = "⚠ LTV solid. Cross-sell opportunities exist.";
  } else if (ltv > 400) {
    comments.ltv = "⚠ LTV low. Pricing or product mix issues.";
  } else {
    comments.ltv = "✗ LTV deteriorated. Unit economics at risk.";
  }
  if (revenuePer > 70) {
    comments.revenue_per_client = "✓ Excellent revenue extraction per client.";
  } else if (revenuePer > 60) {
    comments.revenue_per_client =
      "⚠ Revenue per client solid. Maintain current strategies.";
  } else if (revenuePer > 50) {
    comments.revenue_per_client =
      "⚠ Revenue per client adequate. Identify growth opportunities.";
  } else {
    comments.revenue_per_client =
      "⚠ Revenue per client declining. Pricing intervention needed.";
  }
  return comments;
}
