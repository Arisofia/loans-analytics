import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'
import styles from './analytics-page.module.css'
import Link from 'next/link'

export const metadata = {
  title: 'Portfolio Analytics | Abaco Loans',
  description: 'Detailed portfolio performance dashboard and risk metrics.',
}

export default function AnalyticsPage() {
  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <Link href="/" className={styles.backLink}>
            &larr; Back to homepage
          </Link>
          <h1>Portfolio performance dashboard</h1>
        </div>
      </header>
      
      <div className={styles.content}>
        <AnalyticsDashboard />
      </div>
    </main>
  )
}
