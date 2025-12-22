import Link from 'next/link'
<<<<<<< HEAD

import styles from './page.module.css'
import {
  heroStats,
  metrics,
  funnelStages,
  riskItems,
  initiatives,
  type HeroStat,
  type Metric,
  type FunnelStage,
  type RiskItem,
  type Initiative,
} from './dashboardData'
=======
import styles from './page.module.css'
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
  return parsed.data
}

export default async function Home() {
  const { metrics, products, controls, steps } = await getData()
>>>>>>> fix/ci-workflow-codecov

export default function Home() {
  return (
<<<<<<< HEAD
    <main className={styles.page} id="main-content" role="main" tabIndex={-1}>
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
          <div className={styles.heroCard}>
            <div className={styles.heroHeader}>
              <p className={styles.label}>Portfolio snapshot</p>
              <p className={styles.helper}>Live telemetry + automated exports</p>
            </div>
            <div className={styles.heroGrid}>
              {heroStats.map((stat: HeroStat) => (
                <div key={stat.label} className={styles.heroStat}>
                  <p className={styles.label}>{stat.label}</p>
                  <p className={styles.heroValue}>{stat.value}</p>
                  <p className={`${styles.helper} ${stat.tone ? styles[stat.tone] : ''}`}>{stat.helper}</p>
                </div>
              ))}
            </div>
            <div className={styles.divider} aria-hidden="true" />
            <div className={styles.heroFooter}>
              <div>
                <p className={styles.helper}>Data quality</p>
                <p className={styles.heroValue}>98.4%</p>
                <p className={styles.helper}>Schema coverage across loan + payment feeds</p>
=======
    <div className={styles.page}>
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
        </div>
        <div className={styles.metrics}>
          {metrics?.map((metric: Metric) => (
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
          {products?.map((product: Product) => (
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
            {controls?.map((item: string) => (
              <div key={item} className={styles.checkItem}>
                <span className={styles.checkBullet} aria-hidden="true" />
                <span>{item}</span>
>>>>>>> fix/ci-workflow-codecov
              </div>
              <div className={styles.trend}>Stable</div>
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
          <h3 className={styles.srOnly}>Key performance indicators</h3>
          <div className={styles.metrics}>
            {metrics.map((metric: Metric) => (
              <article key={metric.label} className={styles.card}>
                <div className={styles.cardHeader}>
                  <p className={styles.label}>{metric.label}</p>
                  <span className={`${styles.delta} ${metric.tone ? styles[metric.tone] : ''}`}>{metric.change}</span>
                </div>
                <p className={styles.cardValue}>{metric.value}</p>
                <p className={styles.helper}>{metric.helper}</p>
              </article>
            ))}
          </div>
        </section>

        <section className={`${styles.section} ${styles.grid}`} aria-labelledby="funnel-heading">
          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.eyebrow}>Conversion</p>
                <h2 id="funnel-heading">Acquisition funnel</h2>
              </div>
              <span className={`${styles.pill} ${styles.pillNeutral}`}>Guardrails on</span>
            </div>
            <p className={styles.helper}>
              Monitor automated decisioning, human-in-the-loop approvals, and downstream funding velocity.
            </p>
            <ol className={styles.stageList}>
              {funnelStages.map((stage: FunnelStage) => {
                const width = Math.max(0, Math.min(100, stage.conversion))

                return (
                  <li key={stage.name} className={styles.stageRow}>
                    <div className={styles.stageHeader}>
                      <div>
                        <p className={styles.label}>{stage.name}</p>
                        <p className={styles.helper}>{stage.volume} volume</p>
                      </div>
                      <span className={`${styles.delta} ${styles.positive}`}>{stage.delta}</span>
                    </div>
                    <div className={styles.stageBar}>
                      <span className={styles.stageFill} style={{ width: `${width}%` }} />
                    </div>
                    <div className={styles.stageNumbers}>
                      <span>{stage.conversion}% conversion</span>
                      <span>Target 60%+</span>
                    </div>
                  </li>
                )
              })}
            </ol>
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.eyebrow}>Exposure</p>
                <h2>Risk concentrations</h2>
              </div>
              <span className={`${styles.pill} ${styles.pillPositive}`}>Coverage 4.1x</span>
            </div>
            <p className={styles.helper}>
              Track top exposures by product with status tags aligned to credit policy and stress scenarios.
            </p>
            <ul className={styles.riskList}>
              {riskItems.map((risk: RiskItem) => (
                <li key={risk.name} className={styles.riskItem}>
                  <div>
                    <p className={styles.label}>{risk.name}</p>
                    <p className={styles.helper}>{risk.concentration} of book</p>
                  </div>
                  <div className={styles.riskMeta}>
                    <p className={styles.cardValue}>{risk.exposure}</p>
                    <span className={`${styles.badge} ${styles[risk.status]}`}>{risk.status}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className={styles.section} aria-labelledby="initiatives-heading">
          <div className={styles.sectionHeader}>
            <p className={styles.eyebrow}>Operating rhythm</p>
            <h2 id="initiatives-heading">Initiatives in flight</h2>
            <p className={styles.sectionCopy}>
              Keep stakeholders aligned with accountability, rollout status, and the KPIs each initiative moves.
            </p>
          </div>
          <div className={styles.initiatives}>
            {initiatives.map((item: Initiative) => (
              <article key={item.title} className={styles.card}>
                <div className={styles.cardHeader}>
                  <div>
                    <p className={styles.label}>{item.owner}</p>
                    <h3 className={styles.cardTitle}>{item.title}</h3>
                  </div>
                  <span className={styles.badge}>{item.status}</span>
                </div>
                <p className={styles.helper}>{item.summary}</p>
              </article>
            ))}
          </div>
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
<<<<<<< HEAD
        </section>
      </div>
    </main>
=======
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
          {steps?.map((step: Step) => (
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
    </div>
>>>>>>> fix/ci-workflow-codecov
  )
}
