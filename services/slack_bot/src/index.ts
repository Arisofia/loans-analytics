import { App, SayFn, SlackEventMiddlewareArgs } from '@slack/bolt'
import axios from 'axios'

interface KPIAlert {
  department: string
  kpi_name: string
  current_value: number
  threshold: number
  severity: 'critical' | 'warning' | 'info'
  run_id: string
  timestamp: string
}

const CHANNEL_MAP: Record<string, string> = {
  Risk: '#kpi-risk-alerts',
  Growth: '#kpi-growth-alerts',
  Finance: '#kpi-finance-alerts',
  Compliance: '#kpi-compliance-alerts',
  Technology: '#kpi-tech-alerts',
  Marketing: '#kpi-marketing-alerts',
  Sales: '#kpi-sales-alerts',
}

class SlackBotService {
  private app: App | null = null
  private kpiWebhookUrl: string | null = null
  private isConfigured = false

  constructor() {
    const token = process.env.SLACK_BOT_TOKEN?.trim()
    const signingSecret = process.env.SLACK_SIGNING_SECRET?.trim()
    const webhookUrl = process.env.KPI_WEBHOOK_URL?.trim()
    this.kpiWebhookUrl = webhookUrl ? webhookUrl.replace(/\/$/, '') : null

    if (!token || !signingSecret) {
      console.warn(
        'SlackBotService: missing SLACK_BOT_TOKEN or SLACK_SIGNING_SECRET; bot not started.'
      )
      return
    }

    this.app = new App({ token, signingSecret })
    this.isConfigured = true
    this.setupEventHandlers()
  }

  private requireApp(): App {
    if (!this.app) {
      throw new Error('Slack app is not configured.')
    }
    return this.app
  }

  private setupEventHandlers(): void {
    if (!this.app) return

    // Mention-based KPI summary lookup
    this.app.event(
      'app_mention',
      async ({
        event,
        say,
      }: SlackEventMiddlewareArgs<'app_mention'> & { say: SayFn }) => {
        const text = event.text?.toLowerCase() || ''
        if (text.includes('kpi') || text.includes('alert')) {
          await this.handleKPIQuery(say)
        }
      }
    )

    // Warning cue messages
    // Using 'any' for message to prevent strict union type errors in Bolt
    this.app.message(
      /:warn:/i,
      async ({ message, say }: { message: any; say: SayFn }) => {
        await this.handleAlertMessage(message, say)
      }
    )
  }

  async sendKPIAlert(alert: KPIAlert): Promise<void> {
    const app = this.requireApp()
    const channel = CHANNEL_MAP[alert.department] || '#kpi-alerts'
    const severity = alert.severity.toUpperCase()

    try {
      await app.client.chat.postMessage({
        channel,
        blocks: [
          {
            type: 'header',
            text: {
              type: 'plain_text',
              text: `${severity}: ${alert.kpi_name}`,
              emoji: true,
            },
          },
          {
            type: 'section',
            fields: [
              { type: 'mrkdwn', text: `*Department:*\n${alert.department}` },
              {
                type: 'mrkdwn',
                text: `*Current Value:*\n${alert.current_value}`,
              },
              { type: 'mrkdwn', text: `*Threshold:*\n${alert.threshold}` },
              { type: 'mrkdwn', text: `*Run ID:*\n${alert.run_id}` },
            ],
          },
          {
            type: 'context',
            elements: [
              { type: 'mrkdwn', text: `_Timestamp: ${alert.timestamp}_` },
            ],
          },
          { type: 'divider' },
        ],
      })
    } catch (error) {
      console.error(`Failed to send alert to ${channel}:`, error)
    }
  }

  private async handleKPIQuery(say: SayFn): Promise<void> {
    if (!this.kpiWebhookUrl) {
      await say({
        text: 'KPI service URL is not configured. Set KPI_WEBHOOK_URL to enable KPI lookups.',
      })
      return
    }

    try {
      const response = await axios.get(`${this.kpiWebhookUrl}/latest`, {
        headers: { Authorization: `Bearer ${process.env.API_KEY}` },
      })

      const kpis = Array.isArray(response.data) ? response.data : []
      const topKpis = kpis.slice(0, 5)

      if (!topKpis.length) {
        await say({ text: 'No KPI data available right now.' })
        return
      }

      const blocks = [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: 'Latest KPI Dashboard',
            emoji: true,
          },
        },
        ...topKpis.map((kpi: any) => ({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*${kpi.name}* (${kpi.department})\nValue: ${kpi.value} | Status: ${kpi.status}`,
          },
        })),
      ]

      await say({ blocks })
    } catch (error) {
      console.error('KPI lookup failed:', error)
      await say({
        text: 'Could not retrieve KPI data. Please try again later.',
      })
    }
  }

  private async handleAlertMessage(message: any, say: SayFn): Promise<void> {
    const text = message.text?.trim()
    if (!text) return
    await say({ text: `Alert noted: "${text}". Forwarding to monitoring.` })
  }

  async start(): Promise<void> {
    if (!this.isConfigured || !this.app) {
      console.warn(
        'SlackBotService: start skipped because configuration is missing.'
      )
      return
    }
    await this.app.start(Number(process.env.PORT) || 3000)
    console.log('⚡️ Slack Bot is running')
  }
}

const slackBot = new SlackBotService()

if (process.env.SLACK_BOT_AUTOSTART !== 'false') {
  slackBot.start().catch(console.error)
}

export default slackBot
