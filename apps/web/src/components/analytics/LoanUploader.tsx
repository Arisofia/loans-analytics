'use client'

import { ChangeEvent, useCallback, useState } from 'react'
import styles from './analytics.module.css'
import { parseLoanCsv } from '@/lib/analyticsProcessor'
import { validateCsvInput } from '@/lib/validation'
import * as Sentry from '@sentry/react'
import type { LoanRow } from '@/types/analytics'

type Props = {
  onData: (rows: LoanRow[]) => void
}

export function LoanUploader({ onData }: Props) {
  const [error, setError] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)

  const handleFile = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setError(null)
      setWarning(null)
      const file = event.target.files?.[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const result = reader.result
          const text =
            typeof result === 'string'
              ? result
              : result instanceof ArrayBuffer
                ? new TextDecoder().decode(result)
                : ''
          // Validate CSV input (size, structure)
          const csvResult = validateCsvInput(text)
          if (!csvResult.success) {
            setError(csvResult.error)
            Sentry.captureException(new Error(csvResult.error), {
              contexts: { validation: csvResult.details },
            })
            return
          }
          if (csvResult.warnings.length > 0) {
            setWarning(csvResult.warnings.join('; '))
          }
          // Parse and pass data
          const parsed = parseLoanCsv(csvResult.data.lines.join('\n'))
          onData(parsed)
        } catch (err: any) {
          setError('Unexpected error during file processing')
          Sentry.captureException(err)
        }
      }
      reader.onerror = (e) => {
        setError('Failed to read file')
        Sentry.captureException(e)
      }
      reader.readAsText(file)
    },
    [onData]
  )

  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Loan uploader</p>
        <p className={styles.sectionCopy}>
          Drag in loans.csv or copy the production extract; we handle currency symbols.
        </p>
      </div>
      <input className={styles.uploadInput} type="file" accept=".csv" onChange={handleFile} />
      {error && (
        <div className={styles.errorBox} role="alert" style={{ color: 'red', marginTop: 8 }}>
          <strong>Error:</strong> {error}
        </div>
      )}
      {warning && !error && (
        <div className={styles.warningBox} role="status" style={{ color: 'orange', marginTop: 8 }}>
          <strong>Warning:</strong> {warning}
        </div>
      )}
    </section>
  )
}
