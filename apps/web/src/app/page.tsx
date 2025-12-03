import Link from 'next/link'

import { controls, metrics, products, steps } from './data'
import styles from './page.module.css'

export default function Home() {
  return (
    <main className={styles.page}>
      <header className={styles.nav}>
        <div className={styles.logo}>ABACO</div>
        <div className={styles.navLinks}>
          <Link href="#kpis">KPIs</Link>
          <Link href="#products">Products</Link>
          <Link href="#controls">Controls</Link>
          <Link href="#flow">Flow</Link>
        </div>
        <Link className={styles.cta} href="#demo">
          Request demo
        </Link>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>Lending intelligence</p>
          <h1>Executive-grade analytics and governance for fintech lenders.</h1>
          <p className={styles.lede}>
            Turn portfolio signals into confident growth: embedded risk controls, KPI lineage, and capital-ready
            dashboards.
          </p>
          <div className={styles.heroCtas}>
            <Link className={styles.ctaPrimary} href="#demo">
              Launch a KPI review
            </Link>
            <Link className={styles.ctaSecondary} href="#products">
              Explore platform
            </Link>
          </div>
        </div>
      </section>

      <section id="kpis" className={styles.metrics}>
        {metrics.map((metric) => (
          <div key={metric.label} className={styles.metricCard}>
            <p className={styles.metricLabel}>{metric.label}</p>
            <p className={styles.metricValue}>{metric.value}</p>
            {metric.helper && <p className={styles.metricHelper}>{metric.helper}</p>}
          </div>
        ))}
      </section>

      <section id="products" className={styles.products}>
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Products</p>
          <h2>Built for portfolio, risk, and growth leaders.</h2>
        </div>
        <div className={styles.productGrid}>
          {products.map((product) => (
            <div key={product.title} className={styles.card}>
              <p className={styles.cardKicker}>{product.kicker}</p>
              <h3>{product.title}</h3>
              <p className={styles.cardCopy}>{product.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="controls" className={styles.controls}>
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Controls</p>
          <h2>Audit-ready guardrails baked in.</h2>
        </div>
        <ul className={styles.controlList}>
          {controls.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section id="flow" className={styles.steps}>
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Flow</p>
          <h2>Golden path to launch.</h2>
        </div>
        <div className={styles.stepGrid}>
          {steps.map((step) => (
            <div key={step.label} className={styles.card}>
              <span className={styles.stepLabel}>{step.label}</span>
              <h3>{step.title}</h3>
              <p className={styles.cardCopy}>{step.copy}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}
