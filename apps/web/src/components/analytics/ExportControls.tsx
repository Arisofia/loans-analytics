'use client'

import {
  processedAnalyticsToCSV,
  processedAnalyticsToJSON,
  processedAnalyticsToMarkdown,
} from '@/lib/exportHelpers'
import styles from './analytics.module.css'
import type { ProcessedAnalytics } from '@/types/analytics'

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
  const hasLoans = analytics.loans.length > 0

  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Export controls</p>
        <p className={styles.sectionCopy}>
          Download CSV, JSON, or markdown so slides and docs stay synced with Copilot.
        </p>
      </div>
      <div className={styles.exportButtons}>
        <button
          className={styles.primaryButton}
          type="button"
          onClick={() => download('analytics.csv', processedAnalyticsToCSV(analytics), 'text/csv')}
          disabled={!hasLoans}
        >
          Download CSV
        </button>
        <button
          className={styles.secondaryButton}
          type="button"
          onClick={() =>
            download('analytics.json', processedAnalyticsToJSON(analytics), 'application/json')
          }
          disabled={!hasLoans}
        >
          Download JSON
        </button>
        <button
          className={styles.secondaryButton}
          type="button"
          onClick={() =>
            download('analytics.md', processedAnalyticsToMarkdown(analytics), 'text/markdown')
          }
          disabled={!hasLoans}
        >
          Download Markdown
        </button>
      </div>
    </section>
  )
}
