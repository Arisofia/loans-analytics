import Link from 'next/link'
import styles from './page.module.css'
import { controls, metrics, products, steps } from './data'

export default function Home() {
  return (
    <main className={styles.main} id="main-content">
      <section className={styles.hero}>
        <p className={styles.kicker}>Fintech intelligence</p>
        <h1>Abaco Loans Analytics</h1>
        <p className={styles.lead}>
          Governed growth, portfolio confidence, and customer-first lending decisions with full
          auditability.
        </p>
        <div className={styles.actions}>
          <Link className={styles.primary} href="#kpis">
            View KPIs
          </Link>
          <Link className={styles.secondary} href="#products">
            Explore products
          </Link>
        </div>
      </section>

      <section id="kpis" className={styles.grid}>
        {metrics.map((item) => (
          <div key={item.label} className={styles.card}>
            <p className={styles.label}>{item.label}</p>
            <p className={styles.value}>{item.value}</p>
          </div>
        ))}
      </section>

      <section id="products" className={styles.grid}>
        {products.map((item) => (
          <div key={item.title} className={styles.card}>
            <p className={styles.label}>{item.title}</p>
            <p>{item.detail}</p>
          </div>
        ))}
      </section>

      <section id="controls" className={styles.list}>
        <h2>Controls & compliance</h2>
        <ul>
          {controls.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section id="steps" className={styles.steps}>
        <h2>Path to production</h2>
        <div className={styles.grid}>
          {steps.map((item) => (
            <div key={item.label} className={styles.card}>
              <p className={styles.label}>{item.label}</p>
              <p className={styles.title}>{item.title}</p>
              <p>{item.copy}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}
