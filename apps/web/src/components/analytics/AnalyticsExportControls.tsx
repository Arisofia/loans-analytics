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
    'idle' | 'exporting' | 'success' | 'error' | 'empty'
  >('idle')
  const [message, setMessage] = useState<string>('')
  const hasLoans = loans.length > 0
  const handleExport = async () => {
    if (!hasLoans) {
      setStatus('empty')
      setMessage('Upload or sync loan data before exporting.')
      return
    }
    if (!onExport) {
      setStatus('success')
      setMessage('Export queued.')
      return
    }
    try {
      setStatus('exporting')
      setMessage('')
      await onExport({ summary, loans })
      setStatus('success')
      setMessage('Export queued.')
    } catch (error) {
      console.error('Analytics export failed', error)
      setStatus('error')
      setMessage('Export failed. Please retry or contact support.')
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
        {message && (
          <span
            className={
              status === 'error' || status === 'empty'
                ? 'text-xs text-rose-300'
                : 'text-xs text-emerald-300'
            }
          >
            {message}
          </span>
        )}
      </div>
    </section>
  )
}
