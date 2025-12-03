'use client'

import { useEffect, useMemo, useState } from 'react'
import styles from './analytics.module.css'
import type { LoanRow } from '@/types/analytics'
import { processLoanRows } from '@/lib/analyticsProcessor'
import { LoanUploader } from './LoanUploader'
import { PortfolioHealthKPIs } from './PortfolioHealthKPIs'
import { TreemapVisualization } from './TreemapVisualization'
import { GrowthPathChart } from './GrowthPathChart'
import { RollRateMatrix } from './RollRateMatrix'
import { ExportControls } from './ExportControls'
import Link from 'next/link'

const DEFAULT_SAMPLE: LoanRow[] = [
  {
    loan_amount: 120000,
    appraised_value: 200000,
    borrower_income: 90000,
    monthly_debt: 1200,
    loan_status: 'current',
    interest_rate: 5.2,
    principal_balance: 115000,
    dpd_status: 'current',
  },
  {
    loan_amount: 250000,
    appraised_value: 320000,
    borrower_income: 140000,
    monthly_debt: 2500,
    loan_status: '30-59 days past due',
    interest_rate: 6.4,
    principal_balance: 230000,
    dpd_status: 'bucket_30',
  },
]

export function AnalyticsDashboard() {
  const [loanData, setLoanData] = useState<LoanRow[]>(DEFAULT_SAMPLE)
  const [drilldownStatuses, setDrilldownStatuses] = useState<
    Record<string, 'ok' | 'error' | 'unknown'>
  >({
    '/delinquency': 'unknown',
    '/roll-rate': 'unknown',
    '/collections': 'unknown',
    '/ingestion-errors': 'unknown',
  })

  const analytics = useMemo(() => processLoanRows(loanData), [loanData])
  const docBase = 'https://github.com/Abaco-Technol/abaco-loans-analytics/blob/main'
  const drilldownBase =
    process.env.NEXT_PUBLIC_DRILLDOWN_BASE_URL ??
    'https://github.com/Abaco-Technol/abaco-loans-analytics/tree/main/docs'
  const alertSlack = process.env.NEXT_PUBLIC_ALERT_SLACK_WEBHOOK
  const alertEmail = process.env.NEXT_PUBLIC_ALERT_EMAIL ?? 'alerts@abaco.loans'

  const runbookLinks = [
    {
      title: 'KPI catalog',
      href: `${docBase}/docs/analytics/KPIs.md`,
      description: 'Definitions, owners, thresholds, and drill-down/runbook mappings.',
    },
    {
      title: 'Dashboards guide',
      href: `${docBase}/docs/analytics/dashboards.md`,
      description: 'Layout, drill-down rules, alert routing, and next-best actions.',
    },
    {
      title: 'Runbook: KPI breach',
      href: `${docBase}/docs/analytics/runbooks/kpi-breach.md`,
      description: 'Actions when KPIs move to amber/red; includes next-best actions per owner.',
    },
    {
      title: 'Runbook: Schema drift',
      href: `${docBase}/docs/analytics/runbooks/schema-drift.md`,
      description: 'Freeze, map fields, update contracts, and restore dashboards.',
    },
    {
      title: 'Runbook: Ingestion failure',
      href: `${docBase}/docs/analytics/runbooks/ingestion-failure.md`,
      description: 'Containment, backfill, validation, and alert closure.',
    },
  ]

  useEffect(() => {
    async function fetchStatuses() {
      try {
        const res = await fetch('/api/drilldowns/status')
        if (!res.ok) throw new Error('status fetch failed')
        const json = (await res.json()) as unknown
        if (json && typeof json === 'object' && !Array.isArray(json)) {
          const parsed = Object.entries(json as Record<string, unknown>).reduce<
            Record<string, 'ok' | 'error'>
          >((acc, [key, value]) => {
            if (value === 'ok' || value === 'error') {
              acc[key] = value
            }
            return acc
          }, {})
          setDrilldownStatuses((prev) => ({ ...prev, ...parsed }))
        }
      } catch {
        // keep existing/unknown on failure
      }
    }
    void fetchStatuses()
  }, [])

  return (
    <div className={styles.container}>
      <LoanUploader onData={setLoanData} />
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <p className={styles.sectionTitle}>Alert routing & runbooks</p>
          <p className={styles.sectionCopy}>
            Every chart links to drill-down tables and owners. Alerts route with SLA and next-best
            action.
          </p>
        </div>
        <div className={styles.linkGrid}>
          <div className={styles.linkCard}>
            <div className={styles.pill}>Alert policy</div>
            <p className={styles.linkDescription}>
              Red = page owner + backup paged. Amber = owner notified. Messages include KPI,
              threshold, runbook link, and ETA.
            </p>
            <p className={styles.linkDescription}>
              Slack: {alertSlack ? 'configured' : 'not set (NEXT_PUBLIC_ALERT_SLACK_WEBHOOK)'} ·
              Email routing: {alertEmail}
            </p>
          </div>
          {runbookLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              target="_blank"
              rel="noreferrer"
              className={styles.linkCard}
            >
              <span className={styles.linkTitle}>{item.title}</span>
              <span className={styles.linkDescription}>{item.description}</span>
            </Link>
          ))}
        </div>
      </section>
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <p className={styles.sectionTitle}>Drill-down tables</p>
          <p className={styles.sectionCopy}>
            Link charts to real tables for investigation. Configure NEXT_PUBLIC_DRILLDOWN_BASE_URL
            to point at your data app/API.
          </p>
        </div>
        <div className={styles.linkGrid}>
          {[
            { label: 'Delinquency cohorts', path: '/delinquency' },
            { label: 'Roll-rate cell loans', path: '/roll-rate' },
            { label: 'Collections queue', path: '/collections' },
            { label: 'Ingestion errors', path: '/ingestion-errors' },
          ].map((item) => {
            const status = drilldownStatuses[item.path] ?? 'unknown'
            const statusText = status === 'ok' ? 'Ready' : status === 'error' ? 'Error' : 'Unknown'
            return (
              <Link
                key={item.path}
                href={`${drilldownBase}${item.path}`}
                target="_blank"
                rel="noreferrer"
                className={styles.linkCard}
              >
                <span className={styles.linkTitle}>{item.label}</span>
                <span className={styles.linkDescription}>
                  Opens drill-down table for this chart.
                </span>
                <span className={styles.pill}>{statusText}</span>
              </Link>
            )
          })}
        </div>
      </section>
      <PortfolioHealthKPIs kpis={analytics.kpis} />
      <TreemapVisualization entries={analytics.treemap} />
      <GrowthPathChart projection={analytics.growthProjection} />
      <RollRateMatrix rows={analytics.rollRates} />
      <ExportControls analytics={analytics} />
    </div>
  )
}
