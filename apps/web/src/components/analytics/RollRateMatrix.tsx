'use client'

import styles from './analytics.module.css'
import type { RollRateEntry } from '@/types/analytics'

type Props = {
  rows: RollRateEntry[]
}

export function RollRateMatrix({ rows }: Props) {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Roll-rate cascade</p>
        <p className={styles.sectionCopy}>
          Monitor DPD transitions with structured tiers and alert probabilities.
        </p>
      </div>
      <div className={styles.card}>
        <table className={styles.rollTable}>
          <thead>
            <tr>
              <th>From (DPD)</th>
              <th>To (Status)</th>
              <th>Share (%)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${row.from}-${row.to}-${index}`}>
                <td>{row.from}</td>
                <td>{row.to}</td>
                <td>{row.percent.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
