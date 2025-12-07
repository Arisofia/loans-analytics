<<<<<<< HEAD
import type { Metadata } from 'next'

import styles from './page.module.css'
import { alerts, funding, kpis, liquidityTracks, pipeline } from './dashboardData'

export const metadata: Metadata = {
  title: 'Abaco Loans Analytics Dashboard',
  description: 'Financial intelligence dashboard highlighting revenue, risk, liquidity, and compliance insights.',
}
=======
import type { PostgrestSingleResponse } from '@supabase/supabase-js'
import Link from 'next/link'
import { z } from 'zod'
import {
  controls as fallbackControls,
  metrics as fallbackMetrics,
  products as fallbackProducts,
  steps as fallbackSteps,
} from './data'
import styles from './page.module.css'
import { supabase } from '../lib/supabaseClient'
import type { LandingPageData } from '../types/landingPage'
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'

const landingPageSchema = z.object({
  metrics: z.array(
    z.object({
      label: z.string().min(1),
      value: z.string().min(1),
    })
  ),
  products: z.array(
    z.object({
      title: z.string().min(1),
      detail: z.string().min(1),
    })
  ),
  controls: z.array(z.string().min(1)),
  steps: z.array(
    z.object({
      label: z.string().min(1),
      title: z.string().min(1),
      copy: z.string().min(1),
    })
  ),
})

const fallbackData: LandingPageData = {
  metrics: fallbackMetrics,
  products: fallbackProducts,
  controls: fallbackControls,
  steps: fallbackSteps,
}

function cloneFallback(): LandingPageData {
  return {
    metrics: fallbackData.metrics.map((item) => ({ ...item })),
    products: fallbackData.products.map((item) => ({ ...item })),
    controls: [...fallbackData.controls],
    steps: fallbackData.steps.map((item) => ({ ...item })),
  }
}

async function getData(): Promise<LandingPageData> {
  if (!supabase) {
    return cloneFallback()
  }

  const { data, error }: PostgrestSingleResponse<LandingPageData> = await supabase
    .from('landing_page_data')
    .select()
    .single()

  if (error || !data) {
    console.error('Error fetching landing page data:', error)
    return cloneFallback()
  }

  const parsed = landingPageSchema.safeParse(data)
  if (!parsed.success) {
    console.error('Invalid landing page payload received:', parsed.error.flatten())
    return cloneFallback()
  }

  return parsed.data
}

export default async function Home() {
  const { metrics, products, controls, steps } = await getData()
>>>>>>> origin/main

  return (
    <div className={styles.page}>
<<<<<<< HEAD
      <div className={styles.shell}>
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Abaco Loans Analytics</p>
            <h1>Financial intelligence engineered for growth.</h1>
            <p className={styles.lede}>
              Precision dashboards for revenue, risk, and liquidity. Built for boardroom velocity, investor readiness,
              and customer-centric execution.
            </p>
          </div>
          <div className={styles.statusBadges}>
            <span className={styles.pill}>Audit trail active</span>
            <span className={`${styles.pill} ${styles.pillStrong}`}>Real-time telemetry</span>
          </div>
        </header>

        <section className={`${styles.grid} ${styles.kpiGrid}`}>
          {kpis.map((kpi) => (
            <div key={kpi.label} className={`${styles.card} ${styles.kpi} ${styles[kpi.tone]}`}>
              <p className={styles.label}>{kpi.label}</p>
              <div className={styles.kpiValue}>{kpi.value}</div>
              <p className={styles.meta}>{kpi.detail}</p>
            </div>
          ))}
        </section>

        <section className={`${styles.grid} ${styles.split}`}>
          <div className={`${styles.card} ${styles.chart}`}>
            <div className={styles.cardHead}>
              <div>
                <p className={styles.label}>Funding trajectory</p>
                <h2>Capital efficiency with transparent guardrails</h2>
              </div>
              <span className={styles.pill}>Traceable</span>
            </div>
            <div className={styles.bars}>
              {funding.map((item) => (
                <div key={item.label} className={styles.barRow}>
                  <div className={styles.barMeta}>
                    <p className={styles.label}>{item.label}</p>
                    <p className={styles.meta}>{item.value}% goal attainment</p>
                  </div>
                  <div className={styles.barTrack}>
                    <span className={`${styles.fill} ${styles[item.accent]}`} style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={`${styles.card} ${styles.table}`}>
            <div className={styles.cardHead}>
              <div>
                <p className={styles.label}>Revenue pipeline</p>
                <h2>Commercial momentum</h2>
              </div>
              <span className={styles.pill}>All stages</span>
            </div>
            <div className={styles.tableHead}>
              <span>Initiative</span>
              <span>Stage</span>
              <span>Volume</span>
              <span>Risk band</span>
            </div>
            {pipeline.map((deal) => (
              <div key={deal.name} className={styles.tableRow}>
                <span>{deal.name}</span>
                <span>{deal.stage}</span>
                <span>{deal.volume}</span>
                <span className={styles.badge}>{deal.risk}</span>
              </div>
            ))}
          </div>
        </section>

        <section className={`${styles.grid} ${styles.split}`}>
          <div className={`${styles.card} ${styles.liquidity}`}>
            <div className={styles.cardHead}>
              <div>
                <p className={styles.label}>Liquidity stack</p>
                <h2>Coverage and diversification</h2>
              </div>
              <span className={styles.pill}>Updated hourly</span>
            </div>
            <div className={styles.liquidityGrid}>
              {liquidityTracks.map((track) => (
                <div key={track.label} className={styles.liquidityCard}>
                  <div className={styles.liquidityTop}>
                    <p className={styles.label}>{track.label}</p>
                    <p className={styles.strong}>{track.value}%</p>
                  </div>
                  <div className={styles.spark}>
                    <span className={styles.sparkFill} style={{ width: `${track.value}%` }} />
                  </div>
                  <p className={styles.meta}>Guardrail: 30% minimum per stream</p>
                </div>
              ))}
            </div>
          </div>

          <div className={`${styles.card} ${styles.alerts}`}>
            <div className={styles.cardHead}>
              <div>
                <p className={styles.label}>Controls & compliance</p>
                <h2>Signals with accountability</h2>
              </div>
              <span className={styles.pill}>Auditable</span>
            </div>
            <div className={styles.alertList}>
              {alerts.map((item) => (
                <div key={item.title} className={styles.alert}>
                  <p className={styles.alertTitle}>{item.title}</p>
                  <p className={styles.meta}>{item.description}</p>
                </div>
              ))}
            </div>
            <div className={styles.footer}>
              <p className={styles.label}>Next actions</p>
              <div className={styles.footerActions}>
                <span className={`${styles.pill} ${styles.pillStrong}`}>Send investment memo</span>
                <span className={styles.pill}>Export audit pack</span>
              </div>
            </div>
          </div>
        </section>
      </div>
=======
      <header className={styles.hero}>
        <div className={styles.pill}>Growth & Risk Intelligence</div>
        <h1>Abaco Loans Analytics</h1>
        <p>
          A fintech-grade command center that blends underwriting precision, revenue acceleration,
          and regulatory confidence in one cohesive experience.
        </p>
        <div className={styles.actions}>
          <Link href="#demo" className={styles.primaryButton}>
            Schedule a demo
          </Link>
          <Link href="#products" className={styles.secondaryButton}>
            Explore products
          </Link>
          <Link href="/settings" className={styles.secondaryButton}>
            Open settings
          </Link>
        </div>
        <div className={styles.metrics}>
          {metrics.map((metric) => (
            <div key={metric.label} className={styles.metricCard}>
              <span className={styles.metricValue}>{metric.value}</span>
              <span className={styles.metricLabel}>{metric.label}</span>
            </div>
          ))}
        </div>
      </header>

      <section id="products" className={styles.section} aria-labelledby="products-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Customer-centric growth</p>
          <h2>Build, fund, and protect every loan strategy</h2>
          <p className={styles.sectionCopy}>
            Abaco aligns acquisition, credit, collections, and treasury teams around shared KPIs
            with zero-friction visibility and auditable execution.
          </p>
        </div>
        <div className={styles.cardGrid}>
          {products.map((product) => (
            <div key={product.title} className={styles.card}>
              <h3>{product.title}</h3>
              <p>{product.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section} aria-labelledby="excellence-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Operational excellence</p>
          <h2>Compliance-first, automation-ready</h2>
          <p className={styles.sectionCopy}>
            Deploy with confidence using built-in governance, continuous monitoring, and clear
            accountabilities for every decision.
          </p>
        </div>
        <div className={styles.compliance}>
          <div className={styles.complianceList}>
            {controls.map((item) => (
              <div key={item} className={styles.checkItem}>
                <span className={styles.checkBullet} aria-hidden="true" />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <div className={styles.auditBox}>
            <p className={styles.auditTitle}>Audit-ready by design</p>
            <ul>
              <li>Unified evidence across decisions, payments, and servicing.</li>
              <li>Exportable traces for regulators, investors, and partners.</li>
              <li>Service-level alerts with automated escalations.</li>
            </ul>
            <Link href="#demo" className={styles.primaryGhost}>
              Launch a pilot
            </Link>
          </div>
        </div>
      </section>

      <section id="demo" className={styles.section} aria-labelledby="playbook-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Delivery playbook</p>
          <h2>From data to decisions in weeks</h2>
          <p className={styles.sectionCopy}>
            Guided onboarding, industrialized documentation, and observability to keep every sprint
            on budget and on time.
          </p>
        </div>
        <div className={styles.timeline}>
          {steps.map((step) => (
            <div key={step.label} className={styles.timelineStep}>
              <span className={styles.stepBadge}>{step.label}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.copy}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section} id="analytics">
        <AnalyticsDashboard />
      </section>
    </div>
  )
}
