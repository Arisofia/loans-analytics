'use client'

import type {
  AnalyticsExportPayload,
  AnalyticsSummary,
  LoanRecord,
} from '@/types/analytics'

import { AnalyticsExportControls } from './AnalyticsExportControls'

type AnalyticsExportPanelProps = {
  summary: AnalyticsSummary
  loans: LoanRecord[]
  onExport?: (payload: AnalyticsExportPayload) => Promise<void>
}

export const AnalyticsExportPanel = ({
  summary,
  loans,
  onExport,
}: AnalyticsExportPanelProps) => (
  <div className="flex flex-col gap-3">
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">Snapshot</p>
      <div className="mt-2 grid gap-2 text-sm text-slate-200">
        <div className="flex items-center justify-between">
          <span>Total loans</span>
          <span className="font-semibold">{summary.totalLoans}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Outstanding (USD)</span>
          <span className="font-semibold">
            {summary.totalOutstandingUsd.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Delinquency rate</span>
          <span className="font-semibold">
            {summary.delinquencyRatePct.toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
    <AnalyticsExportControls
      summary={summary}
      loans={loans}
      onExport={onExport}
    />
  </div>
)
