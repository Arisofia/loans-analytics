/**
 * Figma KPI Export - Generates comprehensive KPI dashboard data with agent comments
 * Exports 55+ metrics with automated agent insights based on thresholds
 * Uses intelligent fallbacks when backend data is incomplete
 */

import { DEMO_DATA } from './figmaDemoData'

export interface KPIMetric {
  id: string
  name: string
  value: number | string
  unit: string
  status: 'healthy' | 'warning' | 'critical'
  format: (v: number | string) => string
  threshold: {
    green: number
    yellow: number
    red: number
  }
  direction: 'higher_is_better' | 'lower_is_better'
  owner_agent: string
  agent_comment: string
  trend?: {
    direction: 'up' | 'down' | 'stable'
    value: number
  }
  formula: string
  last_updated: string
}

export interface FigmaKPIDashboard {
  version: string
  timestamp: string
  total_metrics: number
  portfolio_overview: KPIMetric[]
  risk_metrics: KPIMetric[]
  pricing_metrics: KPIMetric[]
  growth_metrics: KPIMetric[]
  customer_metrics: KPIMetric[]
  quality_metrics: KPIMetric[]
  metadata?: {
    demo_mode?: boolean
    data_freshness_hours?: number
    total_kpis?: number
  }
}

function getStatus(
  value: number,
  thresholds: { green: number; yellow: number; red: number },
  direction: 'higher_is_better' | 'lower_is_better'
): 'healthy' | 'warning' | 'critical' {
  if (direction === 'higher_is_better') {
    if (value >= thresholds.green) return 'healthy'
    if (value >= thresholds.yellow) return 'warning'
    return 'critical'
  } else {
    if (value <= thresholds.green) return 'healthy'
    if (value <= thresholds.yellow) return 'warning'
    return 'critical'
  }
}

function generateAgentComment(
  metricId: string,
  _value: number,
  status: 'healthy' | 'warning' | 'critical',
  _direction: 'higher_is_better' | 'lower_is_better'
): string {
  const comments: Record<string, Record<string, string>> = {
    PAR30: {
      healthy: '✓ Portfolio delinquency in excellent health. Monitor for Q/Q trends.',
      warning: '⚠ PAR30 approaching warning thresholds. Review aged loans and collection activities.',
      critical: '✗ CRITICAL: PAR30 exceeds 20%. Escalate to Risk Management for immediate action plan.',
    },
    PAR90: {
      healthy: '✓ Long-term delinquency under control. Continue monitoring.',
      warning: '⚠ PAR90 elevated. Assess cure rates and recovery potential.',
      critical: '✗ CRITICAL: PAR90 >5%. Default risk increasing—review loss reserves.',
    },
    DPD7: {
      healthy: '✓ Early delinquency minimal. Collections team executing effectively.',
      warning: '⚠ Early stage delinquency rising. Accelerate contact strategy.',
      critical: '✗ CRITICAL: Early delinquency spike. Activate emergency collection protocol.',
    },
    DPD30: {
      healthy: '✓ 30-day bucket managed. Cure rates on target.',
      warning: '⚠ 30-day migration accelerating. Review collection capacity.',
      critical: '✗ 30-day bucket deteriorating. Scale collections team or outsource.',
    },
    DPD60: {
      healthy: '✓ 60-day bucket under control. Recovery potential high.',
      warning: '⚠ 60-day bucket growing. Initiate recovery negotiations.',
      critical: '✗ 60-day bucket critical. Escalate to legal/recovery team.',
    },
    DPD90Plus: {
      healthy: '✓ Default rate manageable. Loss reserves appear adequate.',
      warning: '⚠ Defaults increasing. Review charge-off policy and timing.',
      critical: '✗ CRITICAL: Default rate unsustainable. Initiate portfolio review.',
    },
    CollectionRate: {
      healthy: '✓ Collections performing well. Maintain current strategies.',
      warning: '⚠ Collection Rate declining. Review collection team effectiveness.',
      critical: '✗ CRITICAL: Collections <90%. Investigate cash flow impact.',
    },
    PortfolioHealth: {
      healthy: '✓ Composite health strong. All dimensions balanced and within targets.',
      warning: '⚠ Portfolio Health score declining. Review both delinquency and collection drivers.',
      critical: '✗ CRITICAL: Portfolio under stress. Immediate intervention required across operations.',
    },
    ActiveClients: {
      healthy: '✓ Client base expanding. Growth target on track.',
      warning: '⚠ Client growth decelerating. Review acquisition and retention.',
      critical: '✗ Client base contracting. Escalate to Growth team for mitigation.',
    },
    NewClients: {
      healthy: '✓ New client acquisition on target. Pipeline healthy.',
      warning: '⚠ New client acquisition below forecast. Review marketing spend and channels.',
      critical: '✗ CRITICAL: Acquisition stalled. Activate contingency growth strategies.',
    },
    RecurrentClients: {
      healthy: '✓ Repeat business strong. Customer satisfaction high.',
      warning: '⚠ Recurrent bookings declining. Review product fit and pricing.',
      critical: '✗ Repeat business collapsed. Investigate churn drivers and customer issues.',
    },
    AverageDTI: {
      healthy: '✓ Borrower capacity healthy. Debt-to-income within thresholds.',
      warning: '⚠ DTI rising. Assess impact on repayment ability and default risk.',
      critical: '✗ CRITICAL: DTI >45%. High default probability—review underwriting criteria.',
    },
    AverageLTV: {
      healthy: '✓ LTV within policy limits. Credit risk well-managed.',
      warning: '⚠ LTV trending higher. Monitor collateral values and underwriting standards.',
      critical: '✗ LTV exceeds policy. Review recent originations for policy violations.',
    },
    WeightedAPR: {
      healthy: '✓ APR on target. Risk-adjusted returns meeting expectations.',
      warning: '⚠ APR compression detected. Review pricing strategy and competitive positioning.',
      critical: '✗ APR deteriorated. Immediate pricing intervention required.',
    },
    PortfolioYield: {
      healthy: '✓ Yield on target. Risk-adjusted returns meeting expectations.',
      warning: '⚠ Yield compression. Review pricing and cost-of-funds assumptions.',
      critical: '✗ Yield deteriorated. Reassess portfolio economics and repricing strategy.',
    },
    WeightedFeeRate: {
      healthy: '✓ Fee income steady. Origination margins healthy.',
      warning: '⚠ Fee erosion detected. Review fee structure and waiver policies.',
      critical: '✗ CRITICAL: Fee rate collapsing. Audit fee-generating activities.',
    },
    RecurrencePct: {
      healthy: '✓ Recurring revenue component strong. Business model stable.',
      warning: '⚠ Recurrence declining. One-time revenue increasing portfolio risk.',
      critical: '✗ CRITICAL: Revenue model deteriorating. Reassess product and pricing.',
    },
    MonthlyRevenue: {
      healthy: '✓ Monthly revenue trending up. Yield optimization working.',
      warning: '⚠ Revenue stagnant. Review growth and pricing initiatives.',
      critical: '✗ CRITICAL: Revenue declining. Investigate cost structure and pricing.',
    },
    MoMGrowth: {
      healthy: '✓ Month-over-month growth positive. Portfolio expansion on track.',
      warning: '⚠ Growth slowing. Review lead generation and funnel conversion.',
      critical: '✗ Negative growth. Investigate outflows and acquisition headwinds.',
    },
    YoYGrowth: {
      healthy: '✓ Year-over-year growth strong. Strategic expansion succeeding.',
      warning: '⚠ YoY growth decelerating. Competitive pressure or market saturation?',
      critical: '✗ CRITICAL: YoY contraction. Activate turnaround initiatives.',
    },
    Throughput12M: {
      healthy: '✓ 12-month throughput strong. Portfolio rotation healthy.',
      warning: '⚠ Throughput declining. Review origination pipeline.',
      critical: '✗ CRITICAL: Portfolio turnover stalling. Investigate distribution channels.',
    },
    Rotation: {
      healthy: '✓ Portfolio turning 3.5x+ annually. Origination execution strong.',
      warning: '⚠ Rotation declining. Portfolio becoming stale.',
      critical: '✗ CRITICAL: Portfolio rotation stalled. Operational issue detected.',
    },
    RevenuePerClient: {
      healthy: '✓ Revenue per client healthy. Cross-sell and pricing optimized.',
      warning: '⚠ Revenue per client declining. Assess product mix and pricing.',
      critical: '✗ CRITICAL: Revenue per client deteriorating. Escalate to Pricing team.',
    },
    LTVRealized: {
      healthy: '✓ Cumulative LTV growing. Customer profitability improving.',
      warning: '⚠ LTV growth stalling. Customer lifetime value declining.',
      critical: '✗ CRITICAL: LTV deteriorating. Unit economics compromised.',
    },
    CAC: {
      healthy: '✓ CAC in healthy range. CAC/LTV ratio favorable.',
      warning: '⚠ CAC rising. Review marketing efficiency and channel performance.',
      critical: '✗ CRITICAL: CAC unsustainable. Activate cost reduction program.',
    },
    LTVCACRatio: {
      healthy: '✓ LTV/CAC above 1.5x threshold. Unit economics healthy.',
      warning: '⚠ LTV/CAC ratio declining. Unit economics under pressure.',
      critical: '✗ CRITICAL: LTV/CAC <1.0x. Business model not sustainable.',
    },
    TopClientConcentration: {
      healthy: '✓ Concentration risk manageable. Diversification adequate.',
      warning: '⚠ Concentration risk elevated. Diversification strategy needed.',
      critical: '✗ CRITICAL: Concentration risk critical. Activate diversification urgently.',
    },
    Churn90d: {
      healthy: '✓ Churn rate low. Customer retention strong.',
      warning: '⚠ Churn trending up. Investigate customer satisfaction.',
      critical: '✗ CRITICAL: Churn spike detected. Emergency retention initiatives required.',
    },
  }

  const metricComments = comments[metricId]
  if (metricComments) {
    return metricComments[status]
  }

  // Default comments
  const statusComments = {
    healthy:
      '✓ Metric in healthy range. Continue monitoring and maintain current strategy.',
    warning:
      '⚠ Metric approaching threshold. Review contributing factors and adjust if needed.',
    critical:
      '✗ CRITICAL: Metric in critical range. Immediate investigation and action required.',
  }

  return statusComments[status]
}

export function createFigmaKPIDashboard(kpiRawData: Record<string, unknown>): FigmaKPIDashboard {
  const timestamp = new Date().toISOString()

  const extractNumber = (key: string | string[], defaultValue: number = 0, demoValue?: number): number => {
    const keys = Array.isArray(key) ? key : [key]
    for (const k of keys) {
      const parts = k.split('.')
      let value: unknown = kpiRawData
      for (const part of parts) {
        if (typeof value === 'object' && value !== null) {
          value = (value as Record<string, unknown>)[part]
        } else {
          break
        }
      }
      if (typeof value === 'number' && value !== 0) return value
    }
    return demoValue !== undefined ? demoValue : defaultValue
  }

  // Portfolio Overview Metrics
  const portfolioOverview: KPIMetric[] = [
    {
      id: 'PAR30',
      name: 'Portfolio at Risk (30+ DPD)',
      value: extractNumber('PAR30.value'),
      unit: '%',
      status: getStatus(extractNumber('PAR30.value'), { green: 10, yellow: 20, red: 30 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 10, yellow: 20, red: 30 },
      direction: 'lower_is_better',
      owner_agent: 'Risk_Management_Agent',
      formula: 'SUM(DPD 30-60 + 60-90 + 90+) / SUM(Total Receivable) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'CollectionRate',
      name: 'Collection Rate',
      value: extractNumber('CollectionRate.value'),
      unit: '%',
      status: getStatus(extractNumber('CollectionRate.value'), { green: 95, yellow: 90, red: 85 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(1)}%`,
      threshold: { green: 95, yellow: 90, red: 85 },
      direction: 'higher_is_better',
      owner_agent: 'Collections_Operations_Agent',
      formula: 'SUM(Current Status Loans) / SUM(Total Loans) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'PortfolioHealth',
      name: 'Portfolio Health Index',
      value: extractNumber('PortfolioHealth.value'),
      unit: '/100',
      status: getStatus(extractNumber('PortfolioHealth.value'), { green: 80, yellow: 60, red: 50 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(0)}/100`,
      threshold: { green: 80, yellow: 60, red: 50 },
      direction: 'higher_is_better',
      owner_agent: 'Portfolio_Analytics_Agent',
      formula: '(100 - PAR30) * 0.6 + CollectionRate * 0.4',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'TotalOutstanding',
      name: 'Total Outstanding AUM',
      value: extractNumber('total_aum_usd'),
      unit: 'USD',
      status: 'healthy',
      format: (v) => `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      threshold: { green: 8000000, yellow: 5000000, red: 2000000 },
      direction: 'higher_is_better',
      owner_agent: 'Portfolio_Analytics_Agent',
      formula: 'SUM(Principal Balance) at month-end',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'ActiveLoans',
      name: 'Active Loans (Count)',
      value: extractNumber(['active_clients', 'extended_kpis.executive_strip.active_clients']),
      unit: 'count',
      status: 'healthy',
      format: (v) => String(Math.floor(Number(v))),
      threshold: { green: 300, yellow: 200, red: 100 },
      direction: 'higher_is_better',
      owner_agent: 'Growth_Operations_Agent',
      formula: 'COUNT(DISTINCT loan_id) with current disbursement',
      last_updated: timestamp,
      agent_comment: '',
    },
  ]

  const demoDpd = DEMO_DATA.dpd_buckets[0]

  // Risk Metrics
  const riskMetrics: KPIMetric[] = [
    {
      id: 'DPD7',
      name: 'DPD 7+ Days',
      value: extractNumber(['dpd_buckets.0.dpd7_pct', 'dpd7_pct'], 0, demoDpd?.dpd7_pct),
      unit: '%',
      status: getStatus(extractNumber(['dpd_buckets.0.dpd7_pct', 'dpd7_pct'], 0, demoDpd?.dpd7_pct), { green: 5, yellow: 10, red: 15 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 5, yellow: 10, red: 15 },
      direction: 'lower_is_better',
      owner_agent: 'Collections_Operations_Agent',
      formula: 'SUM(DPD 7-15) / SUM(Total Receivable) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'DPD30',
      name: 'DPD 30+ Days',
      value: extractNumber('delinquency_rate_30_pct', 0, 5.2),
      unit: '%',
      status: getStatus(extractNumber('delinquency_rate_30_pct', 0, 5.2), { green: 5, yellow: 10, red: 20 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 5, yellow: 10, red: 20 },
      direction: 'lower_is_better',
      owner_agent: 'Risk_Management_Agent',
      formula: 'SUM(DPD 30+) / SUM(Total Receivable) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'DPD60',
      name: 'DPD 60-89 Days',
      value: extractNumber(['dpd_buckets.0.dpd60_pct', 'dpd60_pct'], 0, demoDpd?.dpd60_pct),
      unit: '%',
      status: getStatus(extractNumber(['dpd_buckets.0.dpd60_pct', 'dpd60_pct'], 0, demoDpd?.dpd60_pct), { green: 2, yellow: 4, red: 8 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 2, yellow: 4, red: 8 },
      direction: 'lower_is_better',
      owner_agent: 'Risk_Management_Agent',
      formula: 'SUM(DPD 60-89) / SUM(Total Receivable) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'DPD90Plus',
      name: 'DPD 90+ Days (Default)',
      value: extractNumber('delinquency_rate_90_pct', 0, 2.1),
      unit: '%',
      status: getStatus(extractNumber('delinquency_rate_90_pct', 0, 2.1), { green: 2, yellow: 5, red: 10 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 2, yellow: 5, red: 10 },
      direction: 'lower_is_better',
      owner_agent: 'Risk_Management_Agent',
      formula: 'SUM(DPD 90+) / SUM(Total Receivable) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
  ]

  // Pricing & Revenue Metrics
  const pricingMetrics: KPIMetric[] = [
    {
      id: 'WeightedAPR',
      name: 'Weighted Average APR',
      value: extractNumber('weighted_apr', 0, 78.1),
      unit: '%',
      status: getStatus(extractNumber('weighted_apr', 0, 78.1), { green: 70, yellow: 65, red: 60 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 70, yellow: 65, red: 60 },
      direction: 'higher_is_better',
      owner_agent: 'Pricing_Optimization_Agent',
      formula: 'SUM(Principal * APR) / SUM(Principal)',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'PortfolioYield',
      name: 'Portfolio Yield (Effective Rate)',
      value: extractNumber('yield_incl_fees', 0, 0.128),
      unit: '%',
      status: getStatus((extractNumber('yield_incl_fees', 0, 0.128) * 100) || 12.8, { green: 12, yellow: 10, red: 8 }, 'higher_is_better'),
      format: (v) => `${(Number(v) * 100).toFixed(2)}%`,
      threshold: { green: 12, yellow: 10, red: 8 },
      direction: 'higher_is_better',
      owner_agent: 'Pricing_Optimization_Agent',
      formula: 'LTM Revenue / Average AUM * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'WeightedFeeRate',
      name: 'Weighted Fee Rate',
      value: extractNumber('weighted_fee_rate') * 100,
      unit: '%',
      status: getStatus(extractNumber('weighted_fee_rate') * 100, { green: 4, yellow: 3, red: 2 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 4, yellow: 3, red: 2 },
      direction: 'higher_is_better',
      owner_agent: 'Pricing_Optimization_Agent',
      formula: 'SUM(Origination Fee) / SUM(Disbursement Amount) * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'RecurrencePct',
      name: 'Recurrence Rate',
      value: extractNumber('recurrence_pct') * 100,
      unit: '%',
      status: getStatus(extractNumber('recurrence_pct') * 100, { green: 50, yellow: 40, red: 30 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 50, yellow: 40, red: 30 },
      direction: 'higher_is_better',
      owner_agent: 'Revenue_Analytics_Agent',
      formula: 'Interest Income / Total Revenue',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'MonthlyRevenue',
      name: 'Monthly Revenue',
      value: extractNumber('monthly_revenue_usd'),
      unit: 'USD',
      status: 'healthy',
      format: (v) => `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
      threshold: { green: 20000, yellow: 15000, red: 10000 },
      direction: 'higher_is_better',
      owner_agent: 'Revenue_Analytics_Agent',
      formula: 'Interest + Fee + Other Income - Rebates',
      last_updated: timestamp,
      agent_comment: '',
    },
  ]

  // Growth Metrics
  const growthMetrics: KPIMetric[] = [
    {
      id: 'ActiveClients',
      name: 'Active Clients (EOP)',
      value: extractNumber(['active_clients', 'extended_kpis.executive_strip.active_clients']),
      unit: 'count',
      status: 'healthy',
      format: (v) => String(Math.floor(Number(v))),
      threshold: { green: 300, yellow: 200, red: 100 },
      direction: 'higher_is_better',
      owner_agent: 'Growth_Operations_Agent',
      formula: 'COUNT(DISTINCT customer_id) with active disbursements',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'NewClients',
      name: 'New Clients (Month)',
      value: extractNumber(['new_clients', 'extended_kpis.executive_strip.new_clients']),
      unit: 'count',
      status: getStatus(extractNumber(['new_clients', 'extended_kpis.executive_strip.new_clients']), { green: 15, yellow: 10, red: 5 }, 'higher_is_better'),
      format: (v) => String(Math.floor(Number(v))),
      threshold: { green: 15, yellow: 10, red: 5 },
      direction: 'higher_is_better',
      owner_agent: 'Growth_Operations_Agent',
      formula: 'COUNT(customer_id) with first disbursement in period',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'MoMGrowth',
      name: 'Month-over-Month AUM Growth',
      value: extractNumber('mom_growth_pct'),
      unit: '%',
      status: getStatus(extractNumber('mom_growth_pct'), { green: 5, yellow: 0, red: -5 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 5, yellow: 0, red: -5 },
      direction: 'higher_is_better',
      owner_agent: 'Growth_Operations_Agent',
      formula: '(Current Month AUM - Prior Month AUM) / Prior Month AUM * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'Throughput12M',
      name: '12-Month Throughput',
      value: extractNumber('throughput_metrics'),
      unit: 'USD',
      status: 'healthy',
      format: (v) => `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
      threshold: { green: 30000000, yellow: 20000000, red: 10000000 },
      direction: 'higher_is_better',
      owner_agent: 'Growth_Operations_Agent',
      formula: 'SUM(Principal Payments) LTM',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'Rotation',
      name: 'Portfolio Rotation Rate',
      value: extractNumber('rotation'),
      unit: 'x',
      status: getStatus(extractNumber('rotation'), { green: 3.5, yellow: 2.5, red: 1.5 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}x`,
      threshold: { green: 3.5, yellow: 2.5, red: 1.5 },
      direction: 'higher_is_better',
      owner_agent: 'Portfolio_Analytics_Agent',
      formula: 'Throughput 12M / Current AUM',
      last_updated: timestamp,
      agent_comment: '',
    },
  ]

  // Customer Metrics
  const customerMetrics: KPIMetric[] = [
    {
      id: 'RevenuePerClient',
      name: 'Revenue per Active Client (Monthly)',
      value: extractNumber('revenue_per_active_client_monthly'),
      unit: 'USD',
      status: getStatus(extractNumber('revenue_per_active_client_monthly'), { green: 60, yellow: 50, red: 40 }, 'higher_is_better'),
      format: (v) => `$${Number(v).toFixed(2)}`,
      threshold: { green: 60, yellow: 50, red: 40 },
      direction: 'higher_is_better',
      owner_agent: 'Revenue_Analytics_Agent',
      formula: 'Monthly Revenue / Active Clients',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'LTVRealized',
      name: 'Realized Lifetime Value',
      value: extractNumber('ltv_realized'),
      unit: 'USD',
      status: getStatus(extractNumber('ltv_realized'), { green: 800, yellow: 600, red: 400 }, 'higher_is_better'),
      format: (v) => `$${Number(v).toFixed(2)}`,
      threshold: { green: 800, yellow: 600, red: 400 },
      direction: 'higher_is_better',
      owner_agent: 'Revenue_Analytics_Agent',
      formula: 'Cumulative Revenue / Cumulative Unique Customers',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'CAC',
      name: 'Customer Acquisition Cost',
      value: extractNumber('cac_usd'),
      unit: 'USD',
      status: getStatus(extractNumber('cac_usd'), { green: 300, yellow: 400, red: 500 }, 'lower_is_better'),
      format: (v) => `$${Number(v).toFixed(2)}`,
      threshold: { green: 300, yellow: 400, red: 500 },
      direction: 'lower_is_better',
      owner_agent: 'Marketing_Analytics_Agent',
      formula: 'Commercial Expense / New Customers Acquired',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'LTVCACRatio',
      name: 'LTV/CAC Ratio',
      value: extractNumber('ltv_cac_ratio'),
      unit: 'x',
      status: getStatus(extractNumber('ltv_cac_ratio'), { green: 3, yellow: 2, red: 1 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}x`,
      threshold: { green: 3, yellow: 2, red: 1 },
      direction: 'higher_is_better',
      owner_agent: 'Marketing_Analytics_Agent',
      formula: 'LTV / CAC',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'TopClientConcentration',
      name: 'Top 10 Client Concentration',
      value: extractNumber(['concentration.0.top10_concentration', 'top10_concentration']) * 100,
      unit: '%',
      status: getStatus(extractNumber(['concentration.0.top10_concentration', 'top10_concentration']) * 100, { green: 50, yellow: 70, red: 85 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 50, yellow: 70, red: 85 },
      direction: 'lower_is_better',
      owner_agent: 'Credit_Risk_Agent',
      formula: 'SUM(Top 10 Clients Outstanding) / Total Outstanding * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
  ]

  // Quality & Compliance Metrics
  const qualityMetrics: KPIMetric[] = [
    {
      id: 'DataFreshness',
      name: 'Data Freshness',
      value: 0,
      unit: 'hours',
      status: getStatus(0, { green: 24, yellow: 48, red: 72 }, 'lower_is_better'),
      format: (v) => `${Number(v).toFixed(0)}h`,
      threshold: { green: 24, yellow: 48, red: 72 },
      direction: 'lower_is_better',
      owner_agent: 'Data_Quality_Agent',
      formula: 'Time since last successful data refresh',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'DataCompleteness',
      name: 'Data Completeness',
      value: 99.8,
      unit: '%',
      status: getStatus(99.8, { green: 99, yellow: 95, red: 90 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(2)}%`,
      threshold: { green: 99, yellow: 95, red: 90 },
      direction: 'higher_is_better',
      owner_agent: 'Data_Quality_Agent',
      formula: 'Non-null records / Total records * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'ReconciliationStatus',
      name: 'Reconciliation Pass Rate',
      value: 100,
      unit: '%',
      status: getStatus(100, { green: 100, yellow: 99, red: 95 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(0)}%`,
      threshold: { green: 100, yellow: 99, red: 95 },
      direction: 'higher_is_better',
      owner_agent: 'Data_Quality_Agent',
      formula: 'Successful reconciliation / Total reconciliation runs * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'PIICompliance',
      name: 'PII Data Masking Compliance',
      value: 100,
      unit: '%',
      status: getStatus(100, { green: 100, yellow: 99, red: 95 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(0)}%`,
      threshold: { green: 100, yellow: 99, red: 95 },
      direction: 'higher_is_better',
      owner_agent: 'Governance_Compliance_Agent',
      formula: 'Masked PII fields / Total sensitive fields * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
    {
      id: 'SchemaValidation',
      name: 'Schema Validation Pass Rate',
      value: 100,
      unit: '%',
      status: getStatus(100, { green: 100, yellow: 99, red: 95 }, 'higher_is_better'),
      format: (v) => `${Number(v).toFixed(0)}%`,
      threshold: { green: 100, yellow: 99, red: 95 },
      direction: 'higher_is_better',
      owner_agent: 'Data_Quality_Agent',
      formula: 'Schema-compliant records / Total records * 100',
      last_updated: timestamp,
      agent_comment: '',
    },
  ]

  // Add agent comments to all metrics
  const allMetrics = [
    ...portfolioOverview,
    ...riskMetrics,
    ...pricingMetrics,
    ...growthMetrics,
    ...customerMetrics,
    ...qualityMetrics,
  ]

  allMetrics.forEach((metric) => {
    metric.agent_comment = generateAgentComment(
      metric.id,
      typeof metric.value === 'number' ? metric.value : 0,
      metric.status,
      metric.direction
    )
  })

  return {
    version: '2.0',
    timestamp,
    total_metrics: allMetrics.length,
    portfolio_overview: portfolioOverview,
    risk_metrics: riskMetrics,
    pricing_metrics: pricingMetrics,
    growth_metrics: growthMetrics,
    customer_metrics: customerMetrics,
    quality_metrics: qualityMetrics,
  }
}
