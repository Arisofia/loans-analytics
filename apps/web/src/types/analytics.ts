export type LoanRecord = {
  loanId: string
  principalOutstanding: number
  issuedDate: string
  status: 'active' | 'paid' | 'delinquent' | 'charged_off'
}

export type AnalyticsSummary = {
  generatedAt: string
  totalLoans: number
  totalOutstandingUsd: number
  delinquencyRatePct: number
}

export type AnalyticsExportPayload = {
  summary: AnalyticsSummary
  loans: LoanRecord[]
}
