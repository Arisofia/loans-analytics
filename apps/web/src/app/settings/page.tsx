import Link from 'next/link'
import styles from './page.module.css'

const integrations = [
  {
    name: 'Meta Platform',
    icon: '📱',
    description: 'Instagram & Facebook performance with governed token handling.',
    status: 'Connected',
    lastSync: '5 minutes ago',
    cta: 'Sync now',
    secondary: 'Disconnect',
    tone: 'success',
  },
  {
    name: 'LinkedIn',
    icon: '💼',
    description: 'Company page analytics, follower growth, and engagement KPIs.',
    status: 'Not connected',
    lastSync: null,
    cta: 'Connect LinkedIn',
    secondary: 'Learn more',
    tone: 'neutral',
  },
  {
    name: 'Custom Integration',
    icon: '🔑',
    description: 'Bring your own API (Codex or internal) with secure token storage.',
    status: 'Not connected',
    lastSync: null,
    cta: 'Configure',
    secondary: 'View docs',
    tone: 'neutral',
  },
]

const guardrails = [
  'Tokens are encrypted and never exposed to the client-side app.',
  'Manual sync keeps existing decks predictable while you pilot new channels.',
  'Each connector has explicit scopes for only the metrics we display.',
  'Disconnect immediately revokes stored credentials in Supabase.',
]

export default function SettingsPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.pill}>Integration Control</div>
        <div className={styles.heroCopy}>
          <p className={styles.eyebrow}>Settings</p>
          <h1>Manage social and custom analytics connectors</h1>
          <p>
            Connect Meta, LinkedIn, or a custom Codex endpoint. Validate tokens, trigger manual
            syncs, and keep your portfolio analytics in step with marketing performance.
          </p>
          <div className={styles.actions}>
            <Link href="/" className={styles.secondaryButton}>
              Back to home
            </Link>
            <Link href="/#analytics" className={styles.primaryGhost}>
              View analytics
            </Link>
          </div>
        </div>
      </header>

      <section className={styles.section} aria-labelledby="integration-cards">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Connections</p>
          <h2 id="integration-cards">Channel status</h2>
          <p className={styles.sectionCopy}>
            Use the cards below to validate tokens, trigger manual refreshes, or disconnect
            channels. Status badges and last-sync timestamps keep teams aligned on freshness.
          </p>
        </div>

        <div className={styles.cardGrid}>
          {integrations.map((integration) => (
            <article key={integration.name} className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon} aria-hidden>
                  {integration.icon}
                </span>
                <div>
                  <div className={styles.cardTitleRow}>
                    <h3>{integration.name}</h3>
                    <span
                      className={
                        integration.tone === 'success' ? styles.statusSuccess : styles.statusNeutral
                      }
                    >
                      {integration.status}
                    </span>
                  </div>
                  <p className={styles.cardCopy}>{integration.description}</p>
                  {integration.lastSync ? (
                    <p className={styles.subtleText}>Last sync: {integration.lastSync}</p>
                  ) : (
                    <p className={styles.subtleText}>Not synced yet</p>
                  )}
                </div>
              </div>
              <div className={styles.cardActions}>
                <button type="button" className={styles.primaryButton}>
                  {integration.cta}
                </button>
                <button type="button" className={styles.secondaryAction}>
                  {integration.secondary}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section} aria-labelledby="guardrails-heading">
        <div className={styles.sectionHeader}>
          <p className={styles.eyebrow}>Governance</p>
          <h2 id="guardrails-heading">Operational guardrails</h2>
          <p className={styles.sectionCopy}>
            A quick reference you can share with marketing, analytics, and compliance teams while
            the Meta and LinkedIn pilots are underway.
          </p>
        </div>
        <div className={styles.guardrailBox}>
          <ul>
            {guardrails.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className={styles.infoBox}>
            <p className={styles.infoTitle}>Need Codex details?</p>
            <p className={styles.subtleText}>
              Capture the API host, token flow, and event payloads you expect to push so we can wire
              the connector without blocking other teams.
            </p>
            <Link href="/docs" className={styles.primaryGhost}>
              Open documentation
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
