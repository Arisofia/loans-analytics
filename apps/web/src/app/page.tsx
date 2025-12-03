<<<<<<< HEAD
<<<<<<< HEAD
'use client'

import Link from 'next/link'
import { useCallback, useRef } from 'react'
import type { MouseEvent } from 'react'
=======
import Link from 'next/link'
import { controls, metrics, products, steps } from './data'
import styles from './page.module.css'
>>>>>>> upstream/main
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
>>>>>>> origin/main
import styles from './page.module.css'
<<<<<<< HEAD
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient'
import { logLandingPageDiagnostic } from '../lib/landingPageDiagnostics'
import {
  EMPTY_LANDING_PAGE_DATA,
  landingPageDataSchema,
  type LandingPageData,
  type Metric,
  type Product,
  type Step,
} from '../types/landingPage'

async function getData(): Promise<LandingPageData> {
  if (!supabase || !isSupabaseConfigured) {
    logLandingPageDiagnostic({
      status: 'missing-config',
      supabaseConfigured: false,
      payload: EMPTY_LANDING_PAGE_DATA,
    })
    console.warn('Supabase environment variables are missing; using fallback landing page data')
    return EMPTY_LANDING_PAGE_DATA
  }

  const { data, error } = await supabase.from('landing_page_data').select('*').single()

  if (error) {
    logLandingPageDiagnostic({
      status: 'fetch-error',
      supabaseConfigured: true,
      error,
      payload: EMPTY_LANDING_PAGE_DATA,
    })
    console.error('Error fetching landing page data:', error)
    return EMPTY_LANDING_PAGE_DATA
  }

  if (!data) {
    logLandingPageDiagnostic({
      status: 'no-data',
      supabaseConfigured: true,
      payload: EMPTY_LANDING_PAGE_DATA,
    })
    console.error('Landing page data is missing from Supabase response')
    return EMPTY_LANDING_PAGE_DATA
  }

  const parsed = landingPageDataSchema.safeParse(data)

  if (!parsed.success) {
    logLandingPageDiagnostic({
      status: 'invalid-shape',
      supabaseConfigured: true,
      error: parsed.error.flatten(),
      payload: EMPTY_LANDING_PAGE_DATA,
    })
    console.error('Invalid landing page data shape from Supabase:', parsed.error.flatten())
    return EMPTY_LANDING_PAGE_DATA
  }

  logLandingPageDiagnostic({
    status: 'ok',
    supabaseConfigured: true,
    payload: parsed.data,
  })
=======
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

>>>>>>> origin/main
  return parsed.data
}

export default async function Home() {
  const { metrics, products, controls, steps } = await getData()
>>>>>>> origin/main

<<<<<<< HEAD
const metrics = [
  { label: 'Approval uplift with governed risk', value: '+18%' },
  { label: 'Reduction in manual reviews', value: '42%' },
  { label: 'Portfolio coverage with audit trails', value: '100%' },
]

const products = [
  {
    title: 'Portfolio Intelligence',
    detail:
      'Daily performance lenses across cohorts, pricing, and liquidity to unlock resilient margins.',
  },
  {
    title: 'Risk Orchestration',
    detail:
      'Dynamic policy controls, challenger experiments, and guardrails to defend credit quality.',
  },
  {
    title: 'Growth Enablement',
    detail:
      'Pre-approved journeys, partner-ready APIs, and data rooms that accelerate funding decisions.',
  },
]

const controls = [
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
]

const steps = [
  {
    label: '01',
    title: 'Unify data signals',
    copy: 'Blend credit bureau, behavioral, and operational streams to build a trusted lending graph.',
  },
  {
    label: '02',
    title: 'Model & decide',
    copy: 'Score applicants with explainable risk layers and adaptive policies aligned to appetite.',
  },
  {
    label: '03',
    title: 'Measure & learn',
    copy: 'Track outcomes against revenue and risk KPIs, iterating with governed experiment loops.',
  },
]

const kpis = [
  {
    name: 'Portfolio yield uplift',
    value: '+210 bps',
    context: 'Blended improvement across revolving and installment books.',
  },
  {
    name: 'Time-to-decision',
    value: '320 ms',
    context: 'P99 latency with governed fallbacks and SLA monitoring.',
  },
  {
    name: 'Collections promise kept',
    value: '96%',
    context: 'Promise-to-pay adherence with automated outreach sequencing.',
  },
]

const dashboards = [
  {
    title: 'Executive cockpit',
    summary: 'Forward-looking risk, liquidity, and growth KPIs with scenario alerts.',
  },
  {
    title: 'Pricing lab',
    summary: 'Dynamic APR, fee, and limit strategies with challenger routing and guardrails.',
  },
  {
    title: 'Servicing oversight',
    summary: 'Operational workload, promise management, and QA observability in one console.',
  },
]

export default function Home() {
  const mainRef = useRef<HTMLElement | null>(null)

  const handleSkipToMain = useCallback((event: MouseEvent<HTMLAnchorElement>) => {
    if (!mainRef.current) return

    event.preventDefault()
    mainRef.current.focus({ preventScroll: true })
    mainRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  return (
    <div className={styles.page}>
      <a href="#main" className={styles.skipLink} onClick={handleSkipToMain}>
        Skip to main content
      </a>
=======
  return (
    <div className={styles.page}>
>>>>>>> origin/main
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
<<<<<<< HEAD
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

      <main id="main" className={styles.main} role="main" tabIndex={-1} ref={mainRef}>
        <section id="products" className={styles.section}>
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

        <section className={styles.section} aria-label="Key performance indicators">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Portfolio clarity</p>
            <h2>Operational KPIs with real-time accountability</h2>
            <p className={styles.sectionCopy}>
              Govern every decision with measurable outcomes, automated alerts, and unified evidence
              for stakeholders.
            </p>
          </div>
          <div className={styles.kpiGrid}>
            {kpis.map((kpi) => (
              <div key={kpi.name} className={styles.kpiCard}>
                <div className={styles.kpiHeader}>
                  <span className={styles.kpiValue}>{kpi.value}</span>
                  <span className={styles.kpiName}>{kpi.name}</span>
                </div>
                <p className={styles.kpiContext}>{kpi.context}</p>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.section}>
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

        <section id="demo" className={styles.section}>
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Delivery playbook</p>
            <h2>From data to decisions in weeks</h2>
            <p className={styles.sectionCopy}>
              Guided onboarding, industrialized documentation, and observability to keep every
              sprint on budget and on time.
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

        <section className={styles.section} aria-label="Dashboards and controls">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Command center</p>
            <h2>Dashboards built for auditability and growth</h2>
            <p className={styles.sectionCopy}>
              Standardized insights keep executives, risk owners, and servicing teams aligned on the
              same source of truth.
            </p>
          </div>
          <div className={styles.dashboardGrid}>
            {dashboards.map((item) => (
              <div key={item.title} className={styles.dashboardCard}>
                <div className={styles.dashboardTop}>
                  <span className={styles.badge}>Live</span>
                  <span className={styles.dot} aria-hidden="true" />
                </div>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <Link href="#demo" className={styles.textLink}>
                  View workflow
                </Link>
              </div>
            ))}
          </div>
        </section>
      </main>
=======
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
>>>>>>> origin/main
    </div>
  )
}
