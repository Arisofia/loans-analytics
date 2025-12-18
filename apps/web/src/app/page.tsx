import Link from 'next/link'
import styles from './page.module.css'
import { metrics, products, controls, steps, type Metric, type Product, type Step } from './dashboardData'

return (
  <main className={styles.page}>
    <nav className={styles.nav} aria-label="Primary">
      <div className={styles.brand}>Abaco Loans Analytics</div>
      <div className={styles.navLinks}>
        <Link className={styles.navLink} href="#products">Products</Link>
        <Link className={styles.navLink} href="#controls">Controls</Link>
        <Link className={styles.navLink} href="#steps">Path</Link>
        <Link className={styles.navLink} href="#demo">Playbook</Link>
      </div>
      <Link className={styles.primaryButton} href="#demo">Schedule a demo</Link>
    </nav>

    <header className={styles.hero}>
      <div className={styles.pill}>Growth & Risk Intelligence</div>
      <h1>Abaco Loans Analytics</h1>
      <p>
        A fintech-grade command center that blends underwriting precision, revenue acceleration,
        and regulatory confidence in one cohesive experience.
      </p>
      <div className={styles.actions}>
        <Link href="#demo" className={styles.primaryButton}>Launch a pilot</Link>
        <Link href="#products" className={styles.secondaryButton}>Explore products</Link>
      </div>
      <div className={styles.metrics}>
        {metrics.map((metric: Metric) => (
          <div key={metric.label} className={styles.metricCard}>
            <span className={styles.metricValue}>{metric.value}</span>
            <span className={styles.metricLabel}>{metric.label}</span>
            {metric.helper && <span className={styles.metricHelper}>{metric.helper}</span>}
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
          <Link href="#demo" className={styles.primaryGhost}>Launch a pilot</Link>
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
        <Link href="mailto:hello@abaco.com" className={styles.primaryButton}>Book a session</Link>
        <Link href="/integrations" className={styles.secondaryButton}>View integrations</Link>
      </div>
    </section>
  </main>
)
}
        </div >
  <Link className={styles.cta} href="#demo">
    Request demo
  </Link>
      </header >

<<<<<<< HEAD
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
=======
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
>>>>>>> main
                </Link>
              </div>
            </div>
          </section>

<<<<<<< HEAD
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
=======
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
>>>>>>> main
                    </div>
                  ))}
                </div>
              </section>

<<<<<<< HEAD
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
=======
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
>>>>>>> main
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
