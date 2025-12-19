import Link from 'next/link'

import styles from './page.module.css'
import {
  metrics,
  products,
  controls,
  steps,
  type Metric,
  type Product,
  type Step,
} from './dashboardData'

export const metadata = {
  title: 'Abaco Loans Analytics Dashboard',
  description: 'Financial intelligence dashboard highlighting revenue, risk, liquidity, and compliance insights.',
}

export default function Home() {
  return (
    <main className={styles.page} id="main-content">
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
        <Link className={styles.navCta} href="#demo">
          Schedule a demo
        </Link>
      </nav>

      <header className={styles.hero}>
        <div className={styles.pill}>Growth &amp; Risk Intelligence</div>
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
            <dl key={metric.label} className={styles.metricCard}>
              <dt className={styles.metricLabel}>{metric.label}</dt>
              <dd className={styles.metricValue}>{metric.value}</dd>
              {metric.helper && <dd className={styles.metricHelper}>{metric.helper}</dd>}
            </dl>
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
              <div className={styles.cardHeader}>
                <p className={styles.cardKicker}>Capability</p>
                <h3>{product.title}</h3>
              </div>
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
              <p className={styles.cardKicker}>{item.title}</p>
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
    </main>
  )
}
