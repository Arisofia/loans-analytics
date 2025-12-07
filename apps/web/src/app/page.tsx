<<<<<<< HEAD
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
>>>>>>> origin/main
import styles from './page.module.css'
import { supabase } from '../lib/supabaseClient'
import type { LandingPageData } from '../types/landingPage'
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'

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

  return parsed.data
}

type Stage = {
  name: string;
  volume: string;
  conversion: number;
  lift: string;
};

// Zod schemas for validation
const StageSchema = z.object({
  name: z.string(),
  volume: z.string(),
  conversion: z.number(),
  lift: z.string(),
});
const StagesSchema = z.array(StageSchema);

type RiskItem = {
  name: string;
  exposure: string;
  trend: string;
};

const RiskItemSchema = z.object({
  name: z.string(),
  exposure: z.string(),
  trend: z.string(),
});
const RiskHeatSchema = z.array(RiskItemSchema);

type Initiative = {
  name: string;
  owner: string;
  status: string;
};

const InitiativeSchema = z.object({
  name: z.string(),
  owner: z.string(),
  status: z.string(),
});
const InitiativesSchema = z.array(InitiativeSchema);

// Fallback data for each type
const fallbackStages: Stage[] = [
  { name: "Awareness", volume: "1000", conversion: 10, lift: "5%" },
  { name: "Consideration", volume: "500", conversion: 20, lift: "3%" },
];

const fallbackRiskHeat: RiskItem[] = [
  { name: "Compliance", exposure: "High", trend: "Up" },
  { name: "Security", exposure: "Medium", trend: "Stable" },
];

const fallbackInitiatives: Initiative[] = [
  { name: "Launch New Product", owner: "Alice", status: "In Progress" },
  { name: "Improve UX", owner: "Bob", status: "Planned" },
];

// Fetch data from Supabase with schema validation and fallback
async function getStages(): Promise<Stage[]> {
  const { data, error } = await supabase
    .from('stages')
    .select('name, volume, conversion, lift');
  if (error || !data) {
    console.error('Error fetching stages:', error);
    return fallbackStages;
  }
  const parseResult = StagesSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('Stage data validation failed:', parseResult.error);
    return fallbackStages;
  }
  return parseResult.data;
}

async function getRiskHeat(): Promise<RiskItem[]> {
  const { data, error } = await supabase
    .from('risk_heat')
    .select('name, exposure, trend');
  if (error || !data) {
    console.error('Error fetching riskHeat:', error);
    return fallbackRiskHeat;
  }
  const parseResult = RiskHeatSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('RiskHeat data validation failed:', parseResult.error);
    return fallbackRiskHeat;
  }
  return parseResult.data;
}

async function getInitiatives(): Promise<Initiative[]> {
  const { data, error } = await supabase
    .from('initiatives')
    .select('name, owner, status');
  if (error || !data) {
    console.error('Error fetching initiatives:', error);
    return fallbackInitiatives;
  }
  const parseResult = InitiativesSchema.safeParse(data);
  if (!parseResult.success) {
    console.error('Initiatives data validation failed:', parseResult.error);
    return fallbackInitiatives;
  }
  return parseResult.data;
}

export default async function Home() {
  const stages = await getStages();
  const riskHeat = await getRiskHeat();
  const initiatives = await getInitiatives();
  return (
    <div className={styles.page}>
      <header className={styles.hero}>
        <div className={styles.heroText}>
          <p className={styles.tag}>ABACO — Loan Intelligence</p>
          <h1 className={styles.heading}>Precision growth with auditable, real-time insights.</h1>
          <p className={styles.subtitle}>
            Operational control, embedded risk discipline, and revenue clarity for digital lending
            teams across credit, product, finance, and collections.
=======
  return (
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
          <Link href="/settings" className={styles.secondaryButton}>
            Open settings
          </Link>
        </div>
        <div className={styles.metrics}>
          {metrics.map((metric) => (
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
>>>>>>> origin/main
          </p>
          <div className={styles.pills}>
            <span>Predictive risk</span>
            <span>Unit economics</span>
            <span>Collections</span>
            <span>Funding</span>
          </div>
        </div>
<<<<<<< HEAD
        <div className={styles.heroCard}>
          <div className={styles.heroRow}>
            <div>
              <p className={styles.label}>Run-rate revenue</p>
              <p className={styles.primaryValue}>$6.8M</p>
            </div>
            <div className={styles.pillPositive}>+14.6% QoQ</div>
          </div>
          <p className={styles.helper}>Risk-adjusted yield net of impairments and servicing.</p>
          <div className={styles.divider} />
          <div className={styles.heroGrid}>
            <div>
              <p className={styles.label}>Cost of risk</p>
              <p className={styles.secondaryValue}>2.9%</p>
            </div>
            <div>
              <p className={styles.label}>NPL 90</p>
              <p className={styles.secondaryValue}>1.3%</p>
            </div>
            <div>
              <p className={styles.label}>Capital buffer</p>
              <p className={styles.secondaryValue}>11.4%</p>
            </div>
          </div>
        </div>
      </header>

      <section className={styles.metrics} aria-label="Portfolio performance metrics">
        <h2 className={styles.srOnly}>Portfolio performance metrics</h2>
        {metrics.map((metric) => (
          <article key={metric.title} className={styles.card}>
            <div className={styles.cardHeader}>
              <p className={styles.label}>{metric.title}</p>
              <span className={styles.delta}>{metric.delta}</span>
            </div>
            <p className={styles.cardValue}>{metric.value}</p>
            <p className={styles.helper}>{metric.detail}</p>
          </article>
        ))}
      </section>

      <section className={styles.grid}>
        <article className={styles.panel}>
          <header className={styles.panelHeader}>
            <div>
              <p className={styles.label}>Acquisition to book</p>
              <h2>Risk-calibrated funnel</h2>
            </div>
            <span className={styles.pillNeutral}>SLA monitored</span>
          </header>
          <div className={styles.stageList}>
            {stages.map((stage) => {
              // stage.conversion is normalized at the data fetching layer to be a percentage (0-100).
              const conversionWidth = Math.min(100, Math.max(0, stage.conversion));

              return (
                <div key={stage.name} className={styles.stageRow}>
                  <div>
                    <p className={styles.stageName}>{stage.name}</p>
                    <p className={styles.helper}>{stage.volume} customers</p>
                  </div>
                  <div className={styles.stageMeta}>
                    <div className={styles.stageBar}>
                      <span style={{ width: `${conversionWidth}%` }} />
                    </div>
                    <div className={styles.stageNumbers}>
                      <span>{stage.conversion.toFixed(1)}%</span>
                      <span className={styles.delta}>{stage.lift}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </article>

        <article className={styles.panel}>
          <header className={styles.panelHeader}>
            <div>
              <p className={styles.label}>Risk radar</p>
              <h2>Exposure and actions</h2>
            </div>
            <span className={styles.pillPositive}>Audit ready</span>
          </header>
          <div className={styles.riskList}>
            {riskHeat.map((item) => (
              <div key={item.name} className={styles.riskItem}>
                <div>
                  <p className={styles.stageName}>{item.name}</p>
                  <p className={styles.helper}>{item.exposure}</p>
                </div>
                <span className={styles.trend}>{item.trend}</span>
              </div>
            ))}
          </div>
          <div className={styles.divider} />
          <div className={styles.initiatives}>
            {initiatives.map((initiative) => (
              <div key={initiative.name} className={styles.initiative}>
                <div>
                  <p className={styles.stageName}>{initiative.name}</p>
                  <p className={styles.helper}>{initiative.owner} lead</p>
                </div>
                <span className={styles.pillNeutral}>{initiative.status}</span>
              </div>
            ))}
          </div>
        </article>
=======
        <div className={styles.cardGrid}>
          {products.map((product) => (
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
            {controls.map((item) => (
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
>>>>>>> origin/main
      </section>
    </div>
  )
}
