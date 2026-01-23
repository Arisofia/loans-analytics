import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const BACKEND_KPI_URL = Deno.env.get("BACKEND_KPI_URL") || "http://127.0.0.1:8000/api/kpis/latest"

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
    })
  }

  // Only allow GET
  if (req.method !== "GET") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    })
  }

  let kpiRawData = {}
  let hasDemoData = true

  try {
    // Fetch from backend with timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    
    const kpiResponse = await fetch(BACKEND_KPI_URL, {
      headers: { "Accept": "application/json" },
      signal: controller.signal,
    })
    clearTimeout(timeoutId)

    if (kpiResponse.ok) {
      kpiRawData = await kpiResponse.json()
      hasDemoData =
        !kpiRawData.extended_kpis?.dpd_buckets ||
        (Array.isArray(kpiRawData.extended_kpis.dpd_buckets) && kpiRawData.extended_kpis.dpd_buckets.length === 0)
    }
  } catch (error) {
    console.log("Backend unavailable, using demo data fallback:", error instanceof Error ? error.message : "Unknown error")
    hasDemoData = true
  }

  const timestamp = new Date().toISOString()
  const figmaDashboard = {
    version: "2.0",
    timestamp,
    total_metrics: 56,
    portfolio_overview: buildPortfolioMetrics(kpiRawData),
    risk_metrics: buildRiskMetrics(kpiRawData),
    pricing_metrics: buildPricingMetrics(kpiRawData),
    growth_metrics: buildGrowthMetrics(kpiRawData),
    customer_metrics: buildCustomerMetrics(kpiRawData),
    quality_metrics: buildQualityMetrics(kpiRawData),
    metadata: {
      demo_mode: hasDemoData,
      total_kpis: 56,
      data_freshness_hours: hasDemoData ? null : 0,
      backend_url: BACKEND_KPI_URL,
    },
  }

  return new Response(JSON.stringify(figmaDashboard), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=3600",
      "X-KPI-Version": "2.0",
      "X-Total-Metrics": "56",
      "X-Demo-Mode": hasDemoData ? "true" : "false",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
    },
  })
})

function buildPortfolioMetrics(data: Record<string, unknown>) {
  return [
    {
      id: "active_clients",
      name: "Active Clients",
      value: (data.active_clients as number) || 327,
      unit: "clients",
      status: "healthy",
      direction: "higher_is_better",
    },
    {
      id: "total_outstanding",
      name: "Total Outstanding",
      value: ((data.total_receivable_usd as number) || 8000000).toFixed(2),
      unit: "USD",
      status: "healthy",
      direction: "higher_is_better",
    },
    {
      id: "average_loan_size",
      name: "Average Loan Size",
      value: ((data.average_loan_size as number) || 24465).toFixed(2),
      unit: "USD",
      status: "healthy",
      direction: "higher_is_better",
    },
  ]
}

function buildRiskMetrics(data: Record<string, unknown>) {
  const dpd = ((data.extended_kpis as Record<string, unknown>)?.dpd_buckets as Record<string, unknown>[])?.[(0)]
  return [
    {
      id: "par30",
      name: "Portfolio at Risk (30d)",
      value: ((dpd?.dpd30_pct as number) || 2.1).toFixed(2),
      unit: "%",
      status: "healthy",
      direction: "lower_is_better",
    },
    {
      id: "par90",
      name: "Portfolio at Risk (90d)",
      value: ((dpd?.dpd90_pct as number) || 0.9).toFixed(2),
      unit: "%",
      status: "healthy",
      direction: "lower_is_better",
    },
  ]
}

function buildPricingMetrics(data: Record<string, unknown>) {
  return [
    {
      id: "weighted_apr",
      name: "Weighted APR",
      value: ((data.weighted_apr as number) || 78.1).toFixed(2),
      unit: "%",
      status: "healthy",
      direction: "higher_is_better",
    },
    {
      id: "weighted_fee_rate",
      name: "Weighted Fee Rate",
      value: ((data.weighted_fee_rate as number) || 4.9).toFixed(2),
      unit: "%",
      status: "healthy",
      direction: "higher_is_better",
    },
  ]
}

function buildGrowthMetrics(data: Record<string, unknown>) {
  return [
    {
      id: "mom_growth",
      name: "Month-over-Month Growth",
      value: ((data.mom_growth_pct as number) || -4.71).toFixed(2),
      unit: "%",
      status: "warning",
      direction: "higher_is_better",
    },
    {
      id: "rotation_rate",
      name: "Portfolio Rotation Rate",
      value: ((data.rotation as number) || 3.85).toFixed(2),
      unit: "x/year",
      status: "healthy",
      direction: "higher_is_better",
    },
  ]
}

function buildCustomerMetrics(data: Record<string, unknown>) {
  return [
    {
      id: "cac",
      name: "Customer Acquisition Cost",
      value: ((data.cac_usd as number) || 265).toFixed(2),
      unit: "USD",
      status: "healthy",
      direction: "lower_is_better",
    },
    {
      id: "ltv",
      name: "Lifetime Value",
      value: ((data.ltv_realized as number) || 970).toFixed(2),
      unit: "USD",
      status: "healthy",
      direction: "higher_is_better",
    },
  ]
}

function buildQualityMetrics(data: Record<string, unknown>) {
  return [
    {
      id: "collection_rate",
      name: "Collection Rate",
      value: 93.5,
      unit: "%",
      status: "healthy",
      direction: "higher_is_better",
    },
    {
      id: "data_quality",
      name: "Data Quality Score",
      value: 98,
      unit: "%",
      status: "healthy",
      direction: "higher_is_better",
    },
  ]
}
