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
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient'
import { landingPageDataSchema, type LandingPageData } from '../types/landingPage'

const navLinks = [
  { label: 'KPIs', href: '#kpis' },
  { label: 'Products', href: '#products' },
  { label: 'Dashboards', href: '#dashboards' },
  { label: 'Compliance', href: '#compliance' },
  { label: 'Playbook', href: '#demo' },
]

async function fetchLandingPageData(): Promise<LandingPageData> {
  if (!supabase || !isSupabaseConfigured) {
    return {
      metrics: fallbackMetrics,
      products: fallbackProducts,
      controls: fallbackControls,
      steps: fallbackSteps,
    }
  }

  const response: PostgrestSingleResponse<LandingPageData> = await supabase
    .from('landing_page_data')
    .select('*')
    .single()

  if (response.error || !response.data) {
    return {
      metrics: fallbackMetrics,
      products: fallbackProducts,
      controls: fallbackControls,
      steps: fallbackSteps,
    }
  }

  const parsed = landingPageDataSchema.safeParse(response.data)
  if (!parsed.success) {
    return {
      metrics: fallbackMetrics,
      products: fallbackProducts,
      controls: fallbackControls,
      steps: fallbackSteps,
    }
  }

  return parsed.data
}

export default async function Home() {
  const landingPageData = await fetchLandingPageData()

  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <div className={styles.logo}>ABACO</div>
        <ul className={styles.navLinks}>
          {navLinks.map((link) => (
            <li key={link.href}>
              <Link href={link.href}>{link.label}</Link>
            </li>
          ))}
        </ul>
        <Link className={styles.primaryCta} href="#demo">
          Request demo
        </Link>
      </nav>

      <header className={styles.hero} id="main-content">
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>Executive-grade intelligence for lending teams</p>
          <h1 className={styles.title}>
            Build governed growth with transparent{' '}
            <span className={styles.highlight}>credit analytics</span>
          </h1>
          <p className={styles.subtitle}>
            Abaco pairs portfolio intelligence with risk orchestration so finance leaders can scale
            funding confidently.
          </p>
          <div className={styles.heroActions}>
            <Link className={styles.primaryCta} href="#kpis">
              Explore metrics
            </Link>
            <Link className={styles.secondaryCta} href="#dashboards">
              View dashboards
            </Link>
          </div>
        </div>
        <div className={styles.heroBadge}>
          <span className={styles.badgeLabel}>Reliability</span>
          <strong>99.4% SLA</strong>
          <p>Guarded by automated playbooks and transparent audit trails.</p>
        </div>
      </header>

      <section className={styles.section} id="kpis">
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.eyebrow}>Portfolio KPIs</p>
            <h2 className={styles.sectionTitle}>Risk-aware growth signals</h2>
          </div>
          <p className={styles.sectionSubhead}>
            Metrics calibrated for underwriting rigor, investor readiness, and day-to-day operating
            cadence.
          </p>
        </div>
        <div className={styles.metricsGrid}>
          {landingPageData.metrics.map((metric) => (
            <article key={metric.label} className={styles.metricCard}>
              <p className={styles.metricLabel}>{metric.label}</p>
              <p className={styles.metricValue}>{metric.value}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section} id="products">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Products</p>
          <h2 className={styles.sectionTitle}>Designed for resilient lending</h2>
        </div>
        <div className={styles.productGrid}>
          {landingPageData.products.map((product) => (
            <article key={product.title} className={styles.productCard}>
              <p className={styles.eyebrow}>Capability</p>
              <h3>{product.title}</h3>
              <p className={styles.body}>{product.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section} id="dashboards">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Dashboards</p>
          <h2 className={styles.sectionTitle}>Operational intelligence in one view</h2>
        </div>
        <div className={styles.dashboardShell}>
          <AnalyticsDashboard />
        </div>
      </section>

      <section className={styles.section} id="compliance">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Governance</p>
          <h2 className={styles.sectionTitle}>Controls that keep auditors confident</h2>
        </div>
        <ul className={styles.controlList}>
          {landingPageData.controls.map((control) => (
            <li key={control}>{control}</li>
          ))}
        </ul>
      </section>

      <section className={styles.section} id="demo">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Go-live playbook</p>
          <h2 className={styles.sectionTitle}>Three steps to production</h2>
        </div>
        <ol className={styles.stepList}>
          {landingPageData.steps.map((step) => (
            <li key={step.label} className={styles.stepCard}>
              <span className={styles.stepLabel}>{step.label}</span>
              <div>
                <h3>{step.title}</h3>
                <p className={styles.body}>{step.copy}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
