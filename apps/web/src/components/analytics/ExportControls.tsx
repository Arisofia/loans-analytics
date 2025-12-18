'use client'

import { useState } from 'react'
import {
  processedAnalyticsToCSV,
  processedAnalyticsToJSON,
  processedAnalyticsToMarkdown,
} from '@/lib/exportHelpers'
import styles from './analytics.module.css'
import type { ProcessedAnalytics } from '@/types/analytics'
import * as Sentry from '@sentry/react'

type Props = {
  analytics: ProcessedAnalytics
}

function download(name: string, data: string, mime: string) {
  const blob = new Blob([data], { type: mime })
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = name
  document.body.appendChild(link)

  try {
    link.click()
  } finally {
    link.remove()
    URL.revokeObjectURL(objectUrl)
  }
}

export function ExportControls({ analytics }: Props) {
  const [error, setError] = useState<string | null>(null)
  const hasLoans = analytics.loans.length > 0

  const handleExport = (format: 'csv' | 'json' | 'markdown') => {
    setError(null)
    try {
      let content = ''
      let filename = ''
      let mime = ''

      switch (format) {
        case 'csv':
          content = processedAnalyticsToCSV(analytics)
          filename = 'analytics.csv'
          mime = 'text/csv'
          break
        case 'json':
          content = processedAnalyticsToJSON(analytics)
          filename = 'analytics.json'
          mime = 'application/json'
          break
        case 'markdown':
          content = processedAnalyticsToMarkdown(analytics)
          filename = 'analytics.md'
          mime = 'text/markdown'
          break
      }

      if (!content || content.length === 0) {
        throw new Error(`Export generated empty ${format} file`)
      }

      download(filename, content, mime)
    } catch (err: any) {
      const msg = `Export failed: ${err.message || 'Unknown error'}`
      setError(msg)
      Sentry.captureException(err, {
        contexts: { export: { format, loanCount: analytics.loans.length } },
      })
    }
  }

  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Export controls</p>
        <p className={styles.sectionCopy}>
          Download CSV, JSON, or markdown so slides and docs stay synced with Copilot.
        </p>
      </div>
      {error && (
        <div className={styles.errorBox} role="alert" style={{ color: 'red', marginBottom: 16 }}>
          <strong>Error:</strong> {error}
        </div>
      )}
      <div className={styles.exportButtons}>
        <button
          className={styles.primaryButton}
          type="button"
          onClick={() => handleExport('csv')}
          disabled={!hasLoans}
        >
          Download CSV
        </button>
        <button
          className={styles.secondaryButton}
          type="button"
          onClick={() => handleExport('json')}
          disabled={!hasLoans}
        >
          Download JSON
        </button>
        <button
          className={styles.secondaryButton}
          type="button"
          onClick={() => handleExport('markdown')}
          disabled={!hasLoans}
        >
          Download Markdown
        </button>
      </div>
    </section>
  )
}
