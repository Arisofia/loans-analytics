import Link from 'next/link'
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient'
import { logLandingPageDiagnostic } from '../lib/landingPageDiagnostics'
import {
  landingPageDataSchema,
  type LandingPageData,
  type Metric,
  type Product,
  type Step,
} from '../types/landingPage'
import styles from './page.module.css'
import {
  controls as fallbackControls,
  metrics as fallbackMetrics,
  products as fallbackProducts,
  steps as fallbackSteps,
} from './data'

const FALLBACK_DATA: LandingPageData = {
  metrics: fallbackMetrics as Metric[],
  products: fallbackProducts as Product[],
  controls: fallbackControls as string[],
  steps: fallbackSteps as Step[],
}

const mergeWithFallback = (payload: LandingPageData): LandingPageData => ({
  metrics: payload.metrics.length ? payload.metrics : FALLBACK_DATA.metrics,
  products: payload.products.length ? payload.products : FALLBACK_DATA.products,
  controls: payload.controls.length ? payload.controls : FALLBACK_DATA.controls,
  steps: payload.steps.length ? payload.steps : FALLBACK_DATA.steps,
})

async function getData(): Promise<LandingPageData> {
  if (!supabase || !isSupabaseConfigured) {
    logLandingPageDiagnostic({
      status: 'missing-config',
      supabaseConfigured: false,
      payload: FALLBACK_DATA,
    })
    return FALLBACK_DATA
  }

  const { data, error } = await supabase.from('landing_page_data').select('*').single()

  if (error) {
    logLandingPageDiagnostic({
      status: 'fetch-error',
      supabaseConfigured: true,
      error,
      payload: FALLBACK_DATA,
    })
    return FALLBACK_DATA
  }

  if (!data) {
    logLandingPageDiagnostic({
      status: 'no-data',
      supabaseConfigured: true,
      payload: FALLBACK_DATA,
    })
    return FALLBACK_DATA
  }

  const parsed = landingPageDataSchema.safeParse(data)

  if (!parsed.success) {
    logLandingPageDiagnostic({
      status: 'invalid-shape',
      supabaseConfigured: true,
      error: parsed.error.flatten(),
      payload: FALLBACK_DATA,
    })
    return FALLBACK_DATA
  }

  const payload = mergeWithFallback(parsed.data)
  logLandingPageDiagnostic({
    status: 'ok',
    supabaseConfigured: true,
    payload,
  })
  return payload
}

export default async function Home() {
  const { metrics, products, controls, steps } = await getData()

  return (
    <div className={styles.page} id="main-content">
      <nav className={styles.nav} aria-label="Primary">
        <div className={styles.brand}>Abaco Loans Analytics</div>
        <div className={styles.navLinks}>
          <Link className={styles.navLink} href="#products">
            Products
          </Link>
          <Link className={styles.navLink} href="#controls">
            Controls
          </Link>
          <Link className={styles.navLink} href="#steps">
            Path
          </Link>
          <Link className={styles.navLink} href="#demo">
            Playbook
          </Link>
        </div>
        <Link className={styles.primaryButton} href="#demo">
          Schedule a demo
        </Link>
      </nav>

      <header className={styles.hero}>
        <div className={styles.pill}>Growth & Risk Intelligence</div>
        <h1>Abaco Loans Analytics</h1>
        <p>
          A fintech-grade command center that blends underwriting precision, revenue acceleration,
          and regulatory confidence in one cohesive experience.
        </p>
        <div className={styles.actions}>
          <Link href="#demo" className={styles.primaryButton}>
            Launch a pilot
          </Link>
          <Link href="#products" className={styles.secondaryButton}>
            Explore products
          </Link>
        </div>
        <div className={styles.metrics}>
          {metrics.map((metric: Metric) => (
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
          <h2 id="products-heading">Build, fund, and protect every loan strategy</h2>
          <p className={styles.sectionCopy}>
            Abaco aligns acquisition, credit, collections, and treasury teams around shared KPIs
            with zero-friction visibility and auditable execution.
          </p>
        </div>
        <div className={styles.cardGrid}>
          {products.map((product: Product) => (
            <div key={product.title} className={styles.card}>
              <h3>{product.title}</h3>
              <p>{product.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="controls" className={styles.section} aria-labelledby="controls-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Operational excellence</p>
          <h2 id="controls-heading">Compliance-first, automation-ready</h2>
          <p className={styles.sectionCopy}>
            Deploy with confidence using built-in governance, continuous monitoring, and clear
            accountabilities for every decision.
          </p>
        </div>
        <div className={styles.compliance}>
          <div className={styles.complianceList}>
            {controls.map((item: string) => (
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

      <section id="steps" className={styles.section} aria-labelledby="steps-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>From ingestion to insights</p>
          <h2 id="steps-heading">Path to production</h2>
          <p className={styles.sectionCopy}>
            Governed data flows, risk policies, and commercial controls connect strategy to
            delivery.
          </p>
        </div>
        <div className={styles.grid}>
          {steps.map((item: Step) => (
            <div key={item.label} className={styles.card}>
              <p className={styles.label}>{item.label}</p>
              <p className={styles.title}>{item.title}</p>
              <p>{item.copy}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="demo" className={styles.section} aria-labelledby="demo-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Demo playbook</p>
          <h2 id="demo-heading">Pilot the lending OS</h2>
          <p className={styles.sectionCopy}>
            Data ingestion, KPI dashboards, and governance workflows ready for investors, auditors,
            and frontline teams.
          </p>
        </div>
        <div className={styles.demoCta}>
          <Link href="mailto:hello@abaco.com" className={styles.primaryButton}>
            Book a session
          </Link>
          <Link href="/integrations" className={styles.secondaryButton}>
            View integrations
          </Link>
        </div>
      </section>
    </div>
  )
}
