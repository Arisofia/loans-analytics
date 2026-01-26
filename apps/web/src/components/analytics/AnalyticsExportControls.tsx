'use client'

import { useState } from 'react'

import type {
  AnalyticsExportPayload,
  AnalyticsSummary,
  LoanRecord,
} from '@/types/analytics'

type AnalyticsExportControlsProps = {
  summary: AnalyticsSummary
  loans: LoanRecord[]
  onExport?: (payload: AnalyticsExportPayload) => Promise<void>
}

export const AnalyticsExportControls = ({
  summary,
  loans,
  onExport,
}: AnalyticsExportControlsProps) => {
  const [status, setStatus] = useState<
    'idle' | 'exporting' | 'success' | 'error'
  >('idle')
  const [errorMessage, setErrorMessage] = useState<string>('')
  const hasLoans = loans.length > 0

  const handleExport = async () => {
    if (!hasLoans) {
      setStatus('error')
      setErrorMessage('Export blocked. Confirm loan data is loaded.')
      return
    }

    if (!onExport) {
      setStatus('success')
      return
    }

    try {
      setStatus('exporting')
      setErrorMessage('')
      await onExport({ summary, loans })
      setStatus('success')
    } catch (error) {
      console.error('Analytics export failed', error)
      setStatus('error')
      setErrorMessage('Export failed. Please check your network connection.')
    }
  }

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-slate-200">
          Export analytics package
        </h3>
        <p className="text-xs text-slate-400">
          {hasLoans
            ? `Ready to export ${loans.length.toLocaleString()} loan rows.`
            : 'Upload or sync loan data before exporting.'}
        </p>
        <button
          className="w-fit rounded bg-indigo-500 px-3 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-700"
          disabled={!hasLoans || status === 'exporting'}
          onClick={() => void handleExport()}
          type="button"
        >
          {status === 'exporting' ? 'Exporting…' : 'Export analytics'}
        </button>
        {status === 'success' && (
          <span className="text-xs text-emerald-300">Export queued.</span>
        )}
        {status === 'error' && (
          <span className="text-xs text-rose-300">{errorMessage}</span>
        )}
      </div>
    </section>
  )
}
