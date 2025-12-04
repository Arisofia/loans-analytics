'use client'

import { ChangeEvent, useCallback } from 'react'
import styles from './analytics.module.css'
import { parseLoanCsv } from '@/lib/analyticsProcessor'
import type { LoanRow } from '@/types/analytics'

type Props = {
  onData: (rows: LoanRow[]) => void
}

export function LoanUploader({ onData }: Props) {
  const handleFile = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result
        const text =
          typeof result === 'string'
            ? result
            : result instanceof ArrayBuffer
              ? new TextDecoder().decode(result)
              : ''
        const parsed = parseLoanCsv(text)
        onData(parsed)
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
    </section>
  )
}
