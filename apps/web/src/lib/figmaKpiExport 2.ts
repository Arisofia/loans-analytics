/**
 * Figma KPI Dashboard Export Utilities
 * Transforms backend KPI data into a format suitable for Figma dashboards
 */

interface KPIRawData {
  timestamp?: string
  active_clients?: number
  outstanding_balance?: number
  total_portfolio?: number
  monthly_revenue_usd?: number
  weighted_apr?: number
  weighted_fee_rate?: number
  rotation?: number
  average_ticket?: number
  cac_usd?: number
  ltv_realized?: number
  ltv_cac_ratio?: number
  revenue_per_active_client_monthly?: number
  revenue_per_active_client_annual?: number
  mom_growth_pct?: number
  yoy_growth_pct?: number
  extended_kpis?: {
    dpd_buckets?: Array<{ bucket: string; count: number; amount: number; pct: number }>
    portfolio_metrics?: Array<Record<string, unknown>>
    executive_strip?: {
      total_disbursements?: number
      new_clients?: number
      recurrent_clients?: number
      recovered_clients?: number
    }
    throughput_metrics?: Array<{ outstanding?: number }>
    [key: string]: unknown
  }
  [key: string]: unknown
}

interface FigmaDashboard {
  version: string
  timestamp: string
  total_metrics: number
  portfolio: {
    active_clients: number
    outstanding_balance: number
    total_portfolio: number
    average_ticket: number
    rotation_rate: number
  }
  revenue: {
    monthly_usd: number
    weighted_apr: number
    weighted_fee_rate: number
    effective_rate: number
  }
  unit_economics: {
    cac_usd: number
    ltv_realized: number
    ltv_cac_ratio: number
    revenue_per_client_monthly: number
    revenue_per_client_annual: number
  }
  growth: {
    mom_pct: number
    yoy_pct: number
    monthly_disbursements: number
    throughput_12m: number
  }
  risk: {
    dpd_buckets: Array<{ bucket: string; count: number; amount: number; pct: number }>
    total_delinquent_pct: number
    total_delinquent_amount: number
  }
  executive_strip: {
    total_disbursements: number
    new_clients: number
    recurrent_clients: number
    recovered_clients: number
  }
  metadata?: {
    demo_mode?: boolean
    total_kpis?: number
  }
}

// Demo DPD bucket data for when backend data is unavailable
const DEMO_DPD_BUCKETS = [
  { bucket: 'Current', count: 280, amount: 2800000, pct: 85.6 },
  { bucket: '1-30 DPD', count: 32, amount: 320000, pct: 9.8 },
  { bucket: '31-60 DPD', count: 10, amount: 100000, pct: 3.1 },
  { bucket: '61-90 DPD', count: 3, amount: 30000, pct: 0.9 },
  { bucket: '90+ DPD', count: 2, amount: 20000, pct: 0.6 },
]

/**
 * Creates a Figma-compatible KPI dashboard from raw backend data
 * @param rawData - Raw KPI data from the backend
 * @returns Formatted dashboard data for Figma exports
 */
export function createFigmaKPIDashboard(rawData: KPIRawData): FigmaDashboard {
  const timestamp = new Date().toISOString()

  // Extract DPD buckets with fallback to demo data
  const dpdBuckets =
    rawData.extended_kpis?.dpd_buckets && rawData.extended_kpis.dpd_buckets.length > 0
      ? rawData.extended_kpis.dpd_buckets
      : DEMO_DPD_BUCKETS

  // Calculate total delinquent metrics (excluding 'Current' bucket)
  const delinquentBuckets = dpdBuckets.filter((b) => b.bucket !== 'Current')
  const totalDelinquentPct = delinquentBuckets.reduce((sum, b) => sum + b.pct, 0)
  const totalDelinquentAmount = delinquentBuckets.reduce((sum, b) => sum + b.amount, 0)

  // Extract executive strip data
  const execStrip = rawData.extended_kpis?.executive_strip || {}

  // Extract throughput
  const throughput =
    (rawData.extended_kpis?.throughput_metrics as Array<{ outstanding?: number }>)?.[0]?.outstanding ||
    32097323.35

  const dashboard: FigmaDashboard = {
    version: '2.0',
    timestamp,
    total_metrics: 28,

    portfolio: {
      active_clients: rawData.active_clients || 327,
      outstanding_balance: rawData.outstanding_balance || 8500000,
      total_portfolio: rawData.total_portfolio || 9200000,
      average_ticket: rawData.average_ticket || 2850,
      rotation_rate: rawData.rotation || 3.85,
    },

    revenue: {
      monthly_usd: rawData.monthly_revenue_usd || 20653.03,
      weighted_apr: rawData.weighted_apr || 78.1,
      weighted_fee_rate: rawData.weighted_fee_rate || 4.9,
      effective_rate: (rawData.weighted_apr || 78.1) + (rawData.weighted_fee_rate || 4.9),
    },

    unit_economics: {
      cac_usd: rawData.cac_usd || 265,
      ltv_realized: rawData.ltv_realized || 970,
      ltv_cac_ratio: rawData.ltv_cac_ratio || 3.64,
      revenue_per_client_monthly: rawData.revenue_per_active_client_monthly || 88,
      revenue_per_client_annual: rawData.revenue_per_active_client_annual || 1056,
    },

    growth: {
      mom_pct: rawData.mom_growth_pct || -4.71,
      yoy_pct: rawData.yoy_growth_pct || 0.0,
      monthly_disbursements: execStrip.total_disbursements || 3974478.04,
      throughput_12m: throughput,
    },

    risk: {
      dpd_buckets: dpdBuckets,
      total_delinquent_pct: Math.round(totalDelinquentPct * 100) / 100,
      total_delinquent_amount: totalDelinquentAmount,
    },

    executive_strip: {
      total_disbursements: execStrip.total_disbursements || 3974478.04,
      new_clients: execStrip.new_clients || 8,
      recurrent_clients: execStrip.recurrent_clients || 75,
      recovered_clients: execStrip.recovered_clients || 0,
    },
  }

  return dashboard
}

/**
 * Formats a number as currency (USD)
 * @param value - The number to format
 * @returns Formatted currency string
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Formats a number as a percentage
 * @param value - The number to format
 * @param decimals - Number of decimal places
 * @returns Formatted percentage string
 */
export function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`
}
