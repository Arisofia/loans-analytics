import type { PostgrestSingleResponse } from '@supabase/supabase-js'
import Link from 'next/link'

import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'
import {
  controls as fallbackControls,
  metrics as fallbackMetrics,
  products as fallbackProducts,
  steps as fallbackSteps,
} from './data'
import styles from './page.module.css'
import { logLandingPageDiagnostic } from '../lib/landingPageDiagnostics'
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient'
import {
  landingPageDataSchema,
  type LandingPageData,
  type Metric,
  type Product,
} from '../types/landingPage'

const navLinks = [
  { label: 'KPIs', href: '#kpis' },
  { label: 'Products', href: '#products' },
  { label: 'Dashboards', href: '#dashboards' },
  { label: 'Compliance', href: '#compliance' },
  { label: 'Playbook', href: '#demo' },
]

const scorecards: ReadonlyArray<Metric> = [
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

const dashboards: ReadonlyArray<Product> = [
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

const baseFallbackData: LandingPageData = {
  metrics: fallbackMetrics,
  products: fallbackProducts,
  controls: fallbackControls,
  steps: fallbackSteps,
}

const buildStructuredData = (products: ReadonlyArray<Product>) => ({
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
})

function cloneLandingPageData(source: LandingPageData): LandingPageData {
  return {
    metrics: source.metrics.map((item) => ({ ...item })),
    products: source.products.map((item) => ({ ...item })),
    controls: [...source.controls],
    steps: source.steps.map((item) => ({ ...item })),
  }
}

async function getData(): Promise<LandingPageData> {
  const fallback = cloneLandingPageData(baseFallbackData)

  if (!supabase || !isSupabaseConfigured) {
    logLandingPageDiagnostic({
      status: 'missing-config',
      supabaseConfigured: false,
      payload: fallback,
    })
    console.warn('Supabase environment variables are missing; using fallback landing page data')
    return fallback
  }

  const { data, error }: PostgrestSingleResponse<LandingPageData> = await supabase
    .from('landing_page_data')
    .select('*')
    .single()

  if (error) {
    logLandingPageDiagnostic({
      status: 'fetch-error',
      supabaseConfigured: true,
      error,
      payload: fallback,
    })
    console.error('Error fetching landing page data:', error)
    return fallback
  }

  if (!data) {
    logLandingPageDiagnostic({
      status: 'no-data',
      supabaseConfigured: true,
      payload: fallback,
    })
    console.error('Landing page data is missing from Supabase response')
    return fallback
  }

  const parsed = landingPageDataSchema.safeParse(data)

  if (!parsed.success) {
    logLandingPageDiagnostic({
      status: 'invalid-shape',
      supabaseConfigured: true,
      error: parsed.error.flatten(),
      payload: fallback,
    })
    console.error('Invalid landing page data shape from Supabase:', parsed.error.flatten())
    return fallback
  }

  logLandingPageDiagnostic({
    status: 'ok',
    supabaseConfigured: true,
    payload: parsed.data,
  })

  return parsed.data
}

export default async function Home() {
  const { metrics, products, controls, steps } = await getData()
  const structuredData = buildStructuredData(products)

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
          <Link href="#kpis" className={styles.linkGhost}>
            View KPI cockpit
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

      <section id="products" className={styles.section} aria-labelledby="products-heading">
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

      <section id="demo" aria-labelledby="playbook-heading" className={styles.section}>
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

      <section className={styles.section} id="analytics">
        <AnalyticsDashboard />
      </section>
    </main>
  )
}
