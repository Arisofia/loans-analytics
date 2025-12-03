'use client'

import styles from './analytics.module.css'
import type { KPIStats } from '@/types/analytics'

type Props = {
  kpis: KPIStats
}

export function PortfolioHealthKPIs({ kpis }: Props) {
  const metricSet = [
    { label: 'Delinquency rate', value: `${kpis.delinquencyRate}%` },
    { label: 'Portfolio yield', value: `${kpis.portfolioYield}%` },
    { label: 'Average LTV', value: `${kpis.averageLTV}%` },
    { label: 'Average DTI', value: `${kpis.averageDTI}%` },
    { label: 'Active loans', value: kpis.loanCount.toString() },
  ]

  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionTitle}>Portfolio health</p>
        <p className={styles.sectionCopy}>
          KPIs rendered in real time with ABACO typography and gradients.
        </p>
      </div>
      <div className={styles.grid}>
        {metricSet.map((metric) => (
          <article key={metric.label} className={styles.card}>
            <div className={styles.metricValue}>{metric.value}</div>
            <div className={styles.metricLabel}>{metric.label}</div>
          </article>
        ))}
      </div>
    </section>
  )
}
