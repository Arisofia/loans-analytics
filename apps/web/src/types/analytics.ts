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
