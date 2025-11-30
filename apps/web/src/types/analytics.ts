/**
 * Analytics Dashboard Types
 * Types for loan analytics, visualizations, and data processing
 */

// ============================================
// LEGACY ANALYTICS TYPES (USED BY CURRENT DASHBOARD)
// ============================================

export type LoanRow = Readonly<{
  id?: string
  loan_amount: number
  appraised_value: number
  borrower_income: number
  monthly_debt: number
  loan_status: string
  interest_rate: number
  principal_balance: number
  dpd_status?: string
}>

export type KPIStats = Readonly<{
  delinquencyRate: number
  portfolioYield: number
  averageLTV: number
  averageDTI: number
  loanCount: number
}>

export type TreemapEntry = Readonly<{
  label: string
  value: number
  color: string
}>

export type RollRateEntry = Readonly<{
  from: string
  to: string
  percent: number
}>

export type GrowthPoint = Readonly<{
  label: string
  yield: number
  loanVolume: number
}>

export type ProcessedAnalytics = Readonly<{
  kpis: KPIStats
  treemap: TreemapEntry[]
  rollRates: RollRateEntry[]
  growthProjection: GrowthPoint[]
  loans: LoanRow[]
}>

// ============================================
// EXTENDED ANALYTICS DOMAIN TYPES
// ============================================

export interface LoanDataset {
  loans: LoanRecord[]
  balances: LoanParBalanceRecord[]
  uploadedAt: Date
  filename: string
}

export interface LoanRecord {
  loan_id: string
  maturity_date: string
  origination_date: string
  loan_amount: number
  customer_id: string
  customer_name: string
  kam_code?: string
  interest_rate?: number
  term_months?: number
}

export interface LoanParBalanceRecord {
  loan_id_raw: string
  reporting_date: string
  par_balance: number
  dpd: number
  customer_id: string
  customer_name: string
}

export interface PortfolioSnapshot {
  reportingDate: string
  totalAUM: number
  totalLoans: number
  activeCustomers: number
  avgTicketSize: number
  qualityBreakdown: QualityBreakdown
  segmentBreakdown: SegmentBreakdown
  concentrationMetrics: ConcentrationMetrics
}

export interface QualityBreakdown {
  performing: {
    amount: number
    count: number
    percentage: number
  }
  late: {
    amount: number
    count: number
    percentage: number
  }
  default: {
    amount: number
    count: number
    percentage: number
  }
}

export interface SegmentBreakdown {
  anchor: {
    amount: number
    count: number
    percentage: number
    threshold: number
  }
  midMarket: {
    amount: number
    count: number
    percentage: number
    threshold: [number, number]
  }
  small: {
    amount: number
    count: number
    percentage: number
    threshold: number
  }
}

export interface ConcentrationMetrics {
  top5Clients: ClientConcentration[]
  top10Clients: ClientConcentration[]
  top5Debtors: DebtorConcentration[]
  top10Debtors: DebtorConcentration[]
  herfindahlIndex: number
  giniCoefficient: number
}

export interface ClientConcentration {
  customerId: string
  customerName: string
  kamCode?: string
  totalExposure: number
  percentageOfAUM: number
  numberOfLoans: number
  avgDPD: number
  riskRating: 'Low' | 'Medium' | 'High'
}

export interface DebtorConcentration {
  debtorName: string
  totalOutstanding: number
  percentageOfAUM: number
  numberOfInvoices: number
  avgDPD: number
}

export interface RollRateMatrix {
  period: string
  matrix: RollRateCell[][]
  summary: RollRateSummary
}

export interface RollRateCell {
  fromBucket: string
  toBucket: string
  amount: number
  count: number
  percentage: number
}

export interface RollRateSummary {
  totalRolled: number
  deteriorationRate: number
  improvementRate: number
  stableRate: number
  netFlowToNPL: number
}

export interface GrowthPathPoint {
  month: string
  label: string
  actualAUM: number
  projectedAUM?: number
  targetAUM?: number
  variance?: number
  variancePercent?: number
  growthRate?: number
}

export interface GrowthScenario {
  name: string
  color: string
  assumptions: {
    monthlyGrowthRate: number
    churnRate: number
    newClientAcquisition: number
    avgTicketGrowth: number
  }
  projections: GrowthPathPoint[]
}

export interface TreemapNode {
  name: string
  value: number
  percentage: number
  color?: string
  children?: TreemapNode[]
  metadata?: {
    count?: number
    avgTicket?: number
    kamCode?: string
    segment?: string
    quality?: 'Performing' | 'Late' | 'Default'
  }
}

export interface TreemapVisualizationData {
  title: string
  subtitle?: string
  totalValue: number
  data: TreemapNode[]
  colorScheme: 'quality' | 'segment' | 'kam' | 'custom'
}

export interface AnalyticsKPI {
  id: string
  label: string
  value: number | string
  format: 'currency' | 'percentage' | 'number' | 'text'
  trend?: {
    direction: 'up' | 'down' | 'stable'
    value: number
    period: string
  }
  status: 'excellent' | 'good' | 'warning' | 'critical'
  benchmark?: number
  target?: number
}

export interface KPIDashboardSection {
  title: string
  kpis: AnalyticsKPI[]
}

export interface AnalyticsExportConfig {
  format: 'png' | 'pdf' | 'html' | 'csv' | 'json' | 'markdown'
  resolution?: '1080p' | '4k' | '5k' | '8k'
  includeData: boolean
  includeCharts: boolean
  includeNarrative: boolean
  sections: AnalyticsExportSection[]
}

export interface AnalyticsExportSection {
  id: string
  title: string
  type: 'kpi' | 'chart' | 'table' | 'narrative' | 'treemap' | 'matrix'
  data: any
  config?: any
}

export interface AnalyticsFilters {
  dateRange: {
    start: string
    end: string
  }
  kamCodes?: string[]
  segments?: ('anchor' | 'midMarket' | 'small')[]
  qualityStatus?: ('performing' | 'late' | 'default')[]
  minTicketSize?: number
  maxTicketSize?: number
  customers?: string[]
}

export interface UploadValidationResult {
  isValid: boolean
  errors: UploadError[]
  warnings: UploadWarning[]
  summary: {
    totalRows: number
    validRows: number
    invalidRows: number
    missingFields: string[]
    duplicates: number
  }
}

export interface UploadError {
  row: number
  field: string
  value: any
  message: string
  severity: 'error'
}

export interface UploadWarning {
  row: number
  field: string
  value: any
  message: string
  severity: 'warning'
}

export interface AnalyticsDashboardState {
  dataset: LoanDataset | null
  isLoading: boolean
  error: string | null
  filters: AnalyticsFilters
  activeView: 'overview' | 'quality' | 'concentration' | 'growth' | 'rollrate'
  selectedDate: string
  comparisonDate?: string
}

export interface AnalyticsAlert {
  id: string
  type: 'risk' | 'opportunity' | 'anomaly' | 'milestone'
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  title: string
  message: string
  metric?: string
  value?: number
  threshold?: number
  timestamp: Date
  dismissed: boolean
}
