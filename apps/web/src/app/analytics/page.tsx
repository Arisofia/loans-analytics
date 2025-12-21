'use client'

import Link from 'next/link'
import styles from './page.module.css'
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'

export default function AnalyticsPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div className={styles.copy}>
          <p className={styles.eyebrow}>Analytics workspace</p>
          <h1>Portfolio performance dashboard</h1>
          <p className={styles.subtitle}>
            Upload portfolio CSVs, review KPIs, and export governed reports without leaving the
            browser.
          </p>
        </div>
        <div className={styles.actions}>
          <Link href="/" className={styles.secondaryButton}>
            Back to homepage
          </Link>
          <a href="#dashboard" className={styles.primaryButton}>
            Jump to dashboard
          </a>
        </div>
      </header>

      <section id="dashboard" className={styles.dashboardSection} aria-label="Analytics dashboard">
        <AnalyticsDashboard />
      </section>
    </main>
  )
}
