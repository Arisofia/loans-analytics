<<<<<<< HEAD
import Link from 'next/link'
import { controls, metrics, products, steps } from './data'
import styles from './page.module.css'
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

<<<<<<< HEAD
type Metric = {
  label: string
  value: string
  helper?: string
}

type Product = {
  title: string
  detail: string
  kicker?: string
}

type Step = {
  label: string
  title: string
  copy: string
}

const navLinks = [
  { label: 'KPIs', href: '#kpis' },
  { label: 'Products', href: '#products' },
  { label: 'Dashboards', href: '#dashboards' },
  { label: 'Compliance', href: '#compliance' },
  { label: 'Playbook', href: '#demo' },
]

const metrics: Metric[] = [
  {
    label: 'Approval uplift with governed risk',
    value: '+18%',
    helper: 'Quarter-over-quarter across prime and near-prime',
  },
  {
    label: 'Reduction in manual reviews',
    value: '42%',
    helper: 'Workflow automation with auditability',
  },
  {
    label: 'Portfolio coverage with audit trails',
    value: '100%',
    helper: 'Evidence mapped to every decision',
  },
]

const scorecards: Metric[] = [
  {
    label: 'Application-to-cash velocity',
    value: '< 48 hours',
    helper: 'From lead to funded drawdown',
  },
  {
    label: 'Loss-forecast confidence',
    value: '97%',
    helper: 'Back-tested across six vintages with challenger policies',
  },
  {
    label: 'Straight-through processing',
    value: '70%',
    helper: 'Decisions cleared with controls and service-level guardrails',
  },
]

const products: Product[] = [
  {
    title: 'Portfolio Intelligence',
    detail: 'Daily performance lenses across cohorts, pricing, liquidity, and partner flows.',
    kicker: 'Capital efficiency, reserve discipline, and covenant readiness.',
  },
  {
    title: 'Risk Orchestration',
    detail:
      'Dynamic policy controls, challenger experiments, and guardrails to defend credit quality.',
    kicker: 'Segregation of duties with sign-offs and immutable change logs.',
  },
  {
    title: 'Growth Enablement',
    detail:
      'Pre-approved journeys, partner-ready APIs, and data rooms that accelerate funding decisions.',
    kicker: 'Unified evidence packs for investors, auditors, and strategic partners.',
  },
]

const dashboards: Product[] = [
  {
    title: 'Liquidity & funding cockpit',
    detail: 'Covenant monitoring, cash runway, and facility utilization in one governed console.',
    kicker: '99.4% SLA adherence with automated alerts and playbooks.',
  },
  {
    title: 'Collections intelligence',
    detail: 'Roll rate, cure, and recovery tracking with interventions ranked by ROI.',
    kicker: 'Targeted outreach cadences backed by performance data.',
  },
  {
    title: 'Product P&L lenses',
    detail: 'Unit economics by channel, geography, and risk appetite with drilldowns on variance.',
    kicker: 'Benchmark-ready narratives for executive and board reviews.',
  },
]

const controls = [
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
  'Continuous evidence packs for regulators, investors, and funding partners.',
]

const steps: Step[] = [
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

const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'Abaco Loans Analytics',
  url: 'https://abaco-loans-analytics.com',
  description:
    'Abaco Loans Analytics unifies lending KPIs, governance, and revenue acceleration in one compliant, investor-ready experience.',
  areaServed: 'Global',
  brand: {
    '@type': 'Brand',
    name: 'Abaco Loans Analytics',
  },
  offers: {
    '@type': 'Offer',
    category: 'Financial technology',
    availability: 'https://schema.org/InStock',
  },
  hasOfferCatalog: {
    '@type': 'OfferCatalog',
    name: 'Growth & Risk Intelligence Suite',
    itemListElement: products.map((product) => ({
      '@type': 'Offer',
      itemOffered: {
        '@type': 'Service',
        name: product.title,
        description: product.detail,
      },
    })),
  },
  makesOffer: scorecards.map((score) => ({
    '@type': 'Offer',
    itemOffered: {
      '@type': 'Service',
      name: score.label,
      description: score.helper,
    },
  })),
}

export default function Home() {
=======
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

>>>>>>> origin/main
  return (
    <main id="main-content" className={styles.page}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <nav className={styles.nav} aria-label="Primary">
        <div className={styles.brand}>Abaco Loans</div>
        <div className={styles.navLinks}>
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href} className={styles.navLink}>
              {link.label}
            </Link>
          ))}
        </div>
        <Link href="#demo" className={styles.navCta}>
          Book a session
        </Link>
      </nav>
      <header className={styles.hero}>
        <div className={styles.pillRow}>
          <div className={styles.pill}>Growth & Risk Intelligence</div>
          <div className={styles.subPill}>Bank-grade controls</div>
        </div>
        <h1>Abaco Loans Analytics</h1>
        <p>
          A fintech command center that blends underwriting precision, revenue acceleration, and
          regulatory confidence in one cohesive experience.
        </p>
        <div className={styles.actions}>
          <Link href="#demo" className={styles.primaryButton}>
            Schedule a demo
          </Link>
          <Link href="#products" className={styles.secondaryButton}>
            Explore products
          </Link>
<<<<<<< HEAD
          <Link href="#kpis" className={styles.linkGhost}>
            View KPI cockpit
=======
          <Link href="/settings" className={styles.secondaryButton}>
            Open settings
>>>>>>> origin/main
          </Link>
        </div>
        <div className={styles.metrics}>
          {metrics.map((metric) => (
            <dl key={metric.label} className={styles.metricCard}>
              <dt className={styles.metricLabel}>{metric.label}</dt>
              <dd className={styles.metricValue}>{metric.value}</dd>
              {metric.helper ? <dd className={styles.metricHelper}>{metric.helper}</dd> : null}
            </dl>
          ))}
        </div>
      </header>

<<<<<<< HEAD
      <section id="kpis" aria-labelledby="kpis-heading" className={styles.section}>
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Performance cockpit</p>
          <h2 id="kpis-heading">Operational KPIs engineered for lenders</h2>
          <p className={styles.sectionCopy}>
            Scorecards designed for treasury, risk, operations, and growth teams to make faster,
            audit-ready calls.
          </p>
        </div>
        <div className={styles.scoreGrid}>
          {scorecards.map((item) => (
            <div key={item.label} className={styles.scoreCard}>
              <p className={styles.scoreLabel}>{item.label}</p>
              <p className={styles.scoreValue}>{item.value}</p>
              <p className={styles.scoreHelper}>{item.helper}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="products" aria-labelledby="products-heading" className={styles.section}>
=======
      <section id="products" className={styles.section} aria-labelledby="products-heading">
>>>>>>> origin/main
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Customer-centric growth</p>
          <h2 id="products-heading">Build, fund, and protect every loan strategy</h2>
          <p className={styles.sectionCopy}>
            Abaco aligns acquisition, credit, collections, and treasury teams around shared KPIs
            with zero-friction visibility and auditable execution.
          </p>
        </div>
        <div className={styles.cardGrid}>
          {products.map((product) => (
            <div key={product.title} className={styles.card}>
              <div className={styles.cardHeader}>
                <h3>{product.title}</h3>
                {product.kicker ? (
                  <span className={styles.cardKicker}>{product.kicker}</span>
                ) : null}
              </div>
              <p>{product.detail}</p>
            </div>
          ))}
        </div>
      </section>

<<<<<<< HEAD
      <section id="dashboards" aria-labelledby="dashboards-heading" className={styles.section}>
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Signals and dashboards</p>
          <h2 id="dashboards-heading">Commercial and financial intelligence on demand</h2>
          <p className={styles.sectionCopy}>
            Live dashboards that measure profitability, liquidity, and risk posture with built-in
            governance for every audience.
          </p>
        </div>
        <div className={styles.dashboardGrid}>
          {dashboards.map((dashboard) => (
            <div key={dashboard.title} className={styles.dashboardCard}>
              <div className={styles.dashboardHeader}>
                <h3>{dashboard.title}</h3>
                {dashboard.kicker ? (
                  <span className={styles.dashboardKicker}>{dashboard.kicker}</span>
                ) : null}
              </div>
              <p>{dashboard.detail}</p>
            </div>
          ))}
        </div>
        <div className={styles.linkRow}>
          <Link href="#demo" className={styles.primaryGhost}>
            Launch a pilot
          </Link>
          <Link href="#demo" className={styles.linkGhost}>
            Download governance pack
          </Link>
        </div>
      </section>

      <section id="compliance" aria-labelledby="compliance-heading" className={styles.section}>
=======
      <section className={styles.section} aria-labelledby="excellence-heading">
>>>>>>> origin/main
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Operational excellence</p>
          <h2 id="compliance-heading">Compliance-first, automation-ready</h2>
          <p className={styles.sectionCopy}>
            Deploy with confidence using built-in governance, continuous monitoring, and clear
            accountabilities for every decision.
          </p>
        </div>
        <div className={styles.compliance}>
          <ul className={styles.complianceList}>
            {controls.map((item) => (
              <li key={item} className={styles.checkItem}>
                <span className={styles.checkBullet} aria-hidden="true" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
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

<<<<<<< HEAD
      <section id="demo" aria-labelledby="playbook-heading" className={styles.section}>
=======
      <section id="demo" className={styles.section} aria-labelledby="playbook-heading">
>>>>>>> origin/main
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Delivery playbook</p>
          <h2 id="playbook-heading">From data to decisions in weeks</h2>
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
<<<<<<< HEAD
    </main>
=======

      <section className={styles.section} id="analytics">
        <AnalyticsDashboard />
      </section>
    </div>
>>>>>>> origin/main
  )
}
