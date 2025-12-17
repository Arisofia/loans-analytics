'use client'

import styles from './analytics.module.css'
import type { GrowthPoint } from '@/types/analytics'

type Props = {
  projection: GrowthPoint[]
}

export function GrowthPathChart({ projection }: Props) {
  const maxValue = Math.max(...projection.map((point) => point.loanVolume))
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Growth path</p>
        <p className={styles.sectionCopy}>
          Monthly interpolation of yield + loan volume with a Copilot-ready narrative.
        </p>
      </div>
      <div className={styles.grid}>
        {projection.map((point) => (
          <article key={point.label} className={styles.card}>
            <div className={styles.metricLabel}>{point.label}</div>
            <div className={styles.metricValue}>{point.yield}%</div>
            <div
              style={{
                height: 6,
                background: 'rgba(255,255,255,0.1)',
                borderRadius: 999,
                marginTop: 12,
                position: 'relative',
              }}
            >
              <span
                style={{
                  display: 'block',
                  height: 6,
                  width: `${(point.loanVolume / maxValue) * 100}%`,
                  borderRadius: 999,
                  background: 'linear-gradient(120deg, #22c55e, #2563eb)',
                }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
