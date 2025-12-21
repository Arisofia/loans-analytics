import Link from 'next/link'
import { createClient } from '../lib/supabase/server'
import { landingPageDataSchema, LandingPageData, EMPTY_LANDING_PAGE_DATA } from '../types/landingPage'
import styles from './page.module.css'

async function getData(): Promise<LandingPageData> {
  try {
    const supabase = await createClient()
    const { data, error } = await supabase
      .from('landing_page_content')
      .select('*')
      .single()

    if (error || !data) {
      // console.warn('Falling back to default data due to Supabase error:', error)
      return EMPTY_LANDING_PAGE_DATA
    }

    return landingPageDataSchema.parse(data)
  } catch (error) {
    console.error('Failed to fetch landing page data:', error)
    return EMPTY_LANDING_PAGE_DATA
  }
}

export default async function Home() {
  const data = await getData()
  const { metrics, products, steps, controls } = data

  return (
    <main className={styles.page} id="main-content">
      <div className={styles.shell}>
        <header className={styles.hero}>
          <div>
            <div className={styles.tag}>ABACO Loan Intelligence</div>
            <h1>Fintech-grade analytics for lending teams</h1>
            <p className={styles.subtitle}>
              Unify underwriting, collections, treasury, and compliance with live KPIs, funnel visibility,
              and auditable decision trails built for growth-ready lenders.
            </p>
            <div className={styles.pills}>
              <span className={`${styles.pill} ${styles.pillPositive}`}>Audit-ready evidence</span>
              <span className={`${styles.pill} ${styles.pillNeutral}`}>Treasury + credit aligned</span>
              <span className={`${styles.pill} ${styles.pillNeutral}`}>Investor-grade reporting</span>
            </div>
            <div className={styles.actions}>
              <Link href="/analytics" className={styles.primaryButton}>
                Open analytics workspace
              </Link>
              <Link href="#demo" className={styles.secondaryButton}>
                Schedule a pilot
              </Link>
            </div>
          </div>
        </header>

        <section className={styles.section} aria-labelledby="metrics-heading">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Performance</p>
            <h2 id="metrics-heading">Portfolio KPIs</h2>
            <p className={styles.sectionCopy}>
              Resilient growth metrics that blend credit health, margin, and operational leverage with ready-to-export evidence.
            </p>
          </div>
          <div className={styles.metrics}>
            {metrics.map((metric) => (
              <article key={metric.label} className={styles.card}>
                <div className={styles.cardHeader}>
                  <p className={styles.label}>{metric.label}</p>
                </div>
                <p className={styles.cardValue}>{metric.value}</p>
                {metric.helper && <p className={styles.helper}>{metric.helper}</p>}
              </article>
            ))}
          </div>
        </section>

        <section className={`${styles.section} ${styles.grid}`} aria-labelledby="products-heading">
           <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.eyebrow}>Products</p>
                <h2 id="products-heading">Core Capabilities</h2>
              </div>
            </div>
            <div className={styles.grid}>
                {products.map(product => (
                    <div key={product.title} className={styles.card}>
                        <h3 className={styles.cardTitle}>{product.title}</h3>
                        <p className={styles.helper}>{product.detail}</p>
                        {product.kicker && <span className={styles.badge}>{product.kicker}</span>}
                    </div>
                ))}
            </div>
          </div>
        </section>

        <section className={styles.section} aria-labelledby="steps-heading">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Workflow</p>
            <h2 id="steps-heading">How it works</h2>
          </div>
          <div className={styles.metrics}>
            {steps.map(step => (
                <article key={step.title} className={styles.card}>
                    <p className={styles.label}>{step.label}</p>
                    <h3 className={styles.cardTitle}>{step.title}</h3>
                    <p className={styles.helper}>{step.copy}</p>
                </article>
            ))}
          </div>
        </section>

        <section className={styles.section} aria-labelledby="controls-heading">
             <div className={styles.sectionHeader}>
                <p className={styles.eyebrow}>Compliance</p>
                <h2 id="controls-heading">Active Controls</h2>
            </div>
            <ul className={styles.complianceList}>
                {controls.map((item) => (
                  <li key={item} className={styles.checkItem}>
                    <span className={styles.checkBullet} aria-hidden="true" />
                    <span>{item}</span>
                  </li>
                ))}
            </ul>
        </section>

        <section id="demo" className={`${styles.section} ${styles.panel}`} aria-labelledby="demo-heading">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>Deployment</p>
              <h2 id="demo-heading">Pilot the lending OS</h2>
            </div>
            <span className={`${styles.pill} ${styles.pillPositive}`}>SOC2 + GDPR ready</span>
          </div>
          <p className={styles.sectionCopy}>
            Secure data ingestion, KPI dashboards, governance workflows, and investor-ready exports packaged into a
            fast-start pilot.
          </p>
          <div className={styles.demoActions}>
            <Link href="mailto:hello@abaco.com" className={styles.primaryButton}>
              Book a session
            </Link>
            <Link href="/integrations" className={styles.secondaryButton}>
              View integrations
            </Link>
          </div>
        </section>
      </div>
    </main>
  )
}
