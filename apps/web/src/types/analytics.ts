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

/**
 * Represents a date-time string in ISO 8601 format, typically used for serialized date values in APIs.
 *
 * Expected format: "YYYY-MM-DDTHH:mm:ss.sssZ" (e.g., "2025-03-15T00:00:00.000Z").
 * Timezone: The string should include timezone information, preferably as 'Z' (UTC) or an explicit offset.
 *
 * This is a branded type and must be constructed via {@link isISODateString}.
 * @example
 *   const date: ISODateString = isISODateString("2025-03-15T00:00:00.000Z") ? "2025-03-15T00:00:00.000Z" as ISODateString : throw new Error("Invalid date");
 */
export type ISODateString = string & { readonly __brand: 'ISODateString' }

/**
 * Validates whether a string is a valid ISO 8601 date-time string.
 * Returns true if valid, false otherwise.
 */
export function isISODateString(value: string): value is ISODateString {
  // Regex matches ISO 8601 date-time with optional milliseconds and timezone
  // Example: 2025-03-15T00:00:00.000Z
  const isoRegex = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2}))$/;
  if (!isoRegex.test(value)) return false;
  const date = new Date(value);
  // Check for Invalid Date
  return !isNaN(date.getTime());
}
export interface LoanDataset {
  loans: LoanRecord[]
  balances: LoanParBalanceRecord[]
  uploadedAt: ISODateString
  filename: string
}

export interface LoanRecord {
  loan_id: string
  maturity_date: ISODateString
  origination_date: ISODateString
  loan_amount: number
  customer_id: string
  customer_name: string
  kam_code?: string
  interest_rate?: number
  term_months?: number
}

export interface LoanParBalanceRecord {
  loan_id_raw: string
  reporting_date: ISODateString
  par_balance: number
  dpd: number
  customer_id: string
  customer_name: string
}

export interface PortfolioSnapshot {
  reportingDate: ISODateString
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
  month: ISODateString
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
    quality?: QualityStatus
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

export type AnalyticsExportConfig =
  | {
      format: 'png' | 'pdf' | 'html'
      resolution?: '1920x1080' | '3840x2160' | '5120x2880' | '7680x4320'
      includeData: boolean
      includeCharts: boolean
      includeNarrative: boolean
      sections: AnalyticsExportSection[]
    }
  | {
      format: 'csv' | 'json' | 'markdown'
      includeData: boolean
      includeCharts: boolean
      includeNarrative: boolean
      sections: AnalyticsExportSection[]
    }

export type AnalyticsExportSection =
  | KPIExportSection
  | ChartExportSection
  | TableExportSection
  | NarrativeExportSection
  | TreemapExportSection
  | MatrixExportSection

export interface KPIExportSection {
  id: string
  title: string
  type: 'kpi'
  data: AnalyticsKPI[] | KPIDashboardSection
  config?: {
    layout?: 'single' | 'grid'
    columns?: number
  }
}

export interface ChartSeries {
  label: string
  values: number[]
}

export interface ChartExportSection {
  id: string
  title: string
  type: 'chart'
  data: {
    chartType: 'line' | 'bar' | 'pie' | 'area' | 'scatter'
    labels: string[]
    series: ChartSeries[]
  }
  config?: {
    stacked?: boolean
    showLegend?: boolean
    valueFormat?: 'currency' | 'percentage' | 'number' | 'text'
  }
}

export interface TableExportSection {
  id: string
  title: string
  type: 'table'
  data: {
    columns: string[]
    rows: Record<string, string | number | null>[]
  }
  config?: {
    sortable?: boolean
    columnFormats?: Record<string, 'currency' | 'percentage' | 'number' | 'text'>
  }
}

export interface NarrativeExportSection {
  id: string
  title: string
  type: 'narrative'
  data: {
    content: string
    language?: 'en' | 'es'
    tone?: 'professional' | 'technical' | 'casual'
  }
  config?: {
    includeSummary?: boolean
  }
}

export interface TreemapExportSection {
  id: string
  title: string
  type: 'treemap'
  data: TreemapVisualizationData
  config?: {
    showLegend?: boolean
  }
}

export interface MatrixExportSection {
  id: string
  title: string
  type: 'matrix'
  data: RollRateMatrix
  config?: {
    highlightDiagonal?: boolean
  }
}

export interface AnalyticsFilters {
  dateRange: {
    start: ISODateString
    end: ISODateString
  }
  kamCodes?: string[]
  segments?: ('anchor' | 'midMarket' | 'small')[]
  qualityStatus?: QualityStatus[]
  minTicketSize?: number
  maxTicketSize?: number
  customers?: string[]
}

export type QualityStatus = 'performing' | 'late' | 'default'

export interface UploadValidationResult {
  isValid: boolean
  errors: UploadIssue[]
  warnings: UploadIssue[]
  summary: {
    totalRows: number
    validRows: number
    invalidRows: number
    missingFields: string[]
    duplicates: number
  }
}

export type UploadSeverity = 'error' | 'warning'

export interface UploadIssue {
  row: number
  field: string
  value: string | number | null
  message: string
  severity: UploadSeverity
}

export interface AnalyticsDashboardState {
  dataset: LoanDataset | null
  isLoading: boolean
  error: string | null
  filters: AnalyticsFilters
  activeView: 'overview' | 'quality' | 'concentration' | 'growth' | 'rollrate'
  selectedDate: ISODateString
  comparisonDate?: ISODateString
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
  timestamp: ISODateString
  dismissed: boolean
}
