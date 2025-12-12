<<<<<<< HEAD
import { App, SlackEventMiddlewareArgs } from '@slack/bolt';
=======
<<<<<<< Updated upstream
import { App, Say, SlackEventMiddlewareArgs, Context } from '@slack/bolt';
=======
import { App, SayFn, SlackEventMiddlewareArgs } from '@slack/bolt';
>>>>>>> Stashed changes
>>>>>>> feature/golden-path-documentation
import axios from 'axios';

type Say = (message: { text?: string; blocks?: any[] }) => Promise<void>;

interface KPIAlert {
  department: string;
  kpi_name: string;
  current_value: number;
  threshold: number;
  severity: 'critical' | 'warning' | 'info';
  run_id: string;
  timestamp: string;
}

const CHANNEL_MAP: Record<string, string> = {
  Risk: '#kpi-risk-alerts',
  Growth: '#kpi-growth-alerts',
  Finance: '#kpi-finance-alerts',
  Compliance: '#kpi-compliance-alerts',
  Technology: '#kpi-tech-alerts',
  Marketing: '#kpi-marketing-alerts',
  Sales: '#kpi-sales-alerts',
};

class SlackBotService {
  private app: App | null = null;
  private kpiWebhookUrl: string | null = null;
  private isConfigured = false;

  constructor() {
    const token = process.env.SLACK_BOT_TOKEN?.trim();
    const signingSecret = process.env.SLACK_SIGNING_SECRET?.trim();
    const webhookUrl = process.env.KPI_WEBHOOK_URL?.trim();
    this.kpiWebhookUrl = webhookUrl ? webhookUrl.replace(/\/$/, '') : null;

    if (!token || !signingSecret) {
      console.warn('SlackBotService: missing SLACK_BOT_TOKEN or SLACK_SIGNING_SECRET; bot not started.');
      return;
    }

    this.app = new App({
      token,
      signingSecret,
    });
    this.isConfigured = true;
    this.setupEventHandlers();
  }

  private requireApp(): App {
    if (!this.app) {
      throw new Error('Slack app is not configured.');
    }
    return this.app;
  }

<<<<<<< HEAD
  private setupEventHandlers(): void {
    if (!this.app) return;

    // Mention-based KPI summary lookup
    this.app.event(
      'app_mention',
      async ({ event, say }: SlackEventMiddlewareArgs<'app_mention'> & { say: Say }) => {
=======
<<<<<<< Updated upstream
    // Listen for message events in alert channels
    this.app.message(/:warn:/i, async ({ message, say }: any) => {
=======
    // Mention-based KPI summary lookup
    this.app.event(
      'app_mention',
      async ({ event, say }: SlackEventMiddlewareArgs<'app_mention'>) => {
>>>>>>> feature/golden-path-documentation
        const text = event.text?.toLowerCase() || '';
        if (text.includes('kpi') || text.includes('alert')) {
          await this.handleKPIQuery(say);
        }
      },
    );

    // Message reaction for warning cues
<<<<<<< HEAD
    this.app.message(/:warn:/i, async ({ message, say }: { message: { text?: string }; say: Say }) => {
=======
    this.app.message(/:warn:/i, async ({ message, say }: { message: any; say: SayFn }) => {
>>>>>>> Stashed changes
>>>>>>> feature/golden-path-documentation
      await this.handleAlertMessage(message, say);
    });
  }

  async sendKPIAlert(alert: KPIAlert): Promise<void> {
    const app = this.requireApp();
    const channel = CHANNEL_MAP[alert.department] || '#kpi-alerts';
    const severity = alert.severity.toUpperCase();

    try {
      await app.client.chat.postMessage({
        channel,
        blocks: [
          {
            type: 'header',
            text: { type: 'plain_text', text: `${severity}: ${alert.kpi_name}`, emoji: true },
          },
          {
            type: 'section',
            fields: [
              { type: 'mrkdwn', text: `*Department:*\n${alert.department}` },
              { type: 'mrkdwn', text: `*Current Value:*\n${alert.current_value}` },
              { type: 'mrkdwn', text: `*Threshold:*\n${alert.threshold}` },
              { type: 'mrkdwn', text: `*Run ID:*\n${alert.run_id}` },
            ],
          },
          {
            type: 'context',
            elements: [{ type: 'mrkdwn', text: `_Timestamp: ${alert.timestamp}_` }],
          },
          { type: 'divider' },
        ],
      });
    } catch (error) {
      console.error(`Failed to send alert to ${channel}:`, error);
    }
  }

<<<<<<< HEAD
  private async handleKPIQuery(say: Say): Promise<void> {
=======
<<<<<<< Updated upstream
  private async handleKPIQuery(event: any, say: Say): Promise<void> {
=======
  private async handleKPIQuery(say: SayFn): Promise<void> {
>>>>>>> feature/golden-path-documentation
    if (!this.kpiWebhookUrl) {
      await say({
        text: 'KPI service URL is not configured. Set KPI_WEBHOOK_URL to enable KPI lookups.',
      });
      return;
    }

<<<<<<< HEAD
=======
>>>>>>> Stashed changes
>>>>>>> feature/golden-path-documentation
    try {
      const response = await axios.get(`${this.kpiWebhookUrl}/latest`, {
        headers: { Authorization: `Bearer ${process.env.API_KEY}` },
      });

      const kpis = Array.isArray(response.data) ? response.data : [];
      const topKpis = kpis.slice(0, 5);

      if (!topKpis.length) {
        await say({ text: 'No KPI data available right now.' });
        return;
      }

      const blocks = [
        {
          type: 'header',
          text: { type: 'plain_text', text: 'Latest KPI Dashboard', emoji: true },
        },
        ...topKpis.map((kpi) => ({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*${kpi.name}* (${kpi.department})\nValue: ${kpi.value} | Status: ${kpi.status}`,
          },
        })),
      ];

      await say({ blocks });
    } catch (error) {
<<<<<<< HEAD
      console.error('KPI lookup failed:', error);
=======
<<<<<<< Updated upstream
>>>>>>> feature/golden-path-documentation
      await say('Could not retrieve KPI data. Please try again later.');
    }
  }

<<<<<<< HEAD
  private async handleAlertMessage(message: { text?: string }, say: Say): Promise<void> {
=======
  private async handleAlertMessage(message: any, say: Say): Promise<void> {
    // Process alert messages and aggregate for reporting
    this.alertQueue.push({
      department: 'Unknown',
      kpi_name: message.text,
      current_value: 0,
      threshold: 0,
      severity: 'info',
      run_id: 'manual',
      timestamp: new Date().toISOString(),
    });
=======
      console.error('KPI lookup failed:', error);
      await say({ text: 'Could not retrieve KPI data. Please try again later.' });
    }
  }

  private async handleAlertMessage(message: any, say: SayFn): Promise<void> {
>>>>>>> feature/golden-path-documentation
    const text = message.text?.trim();
    if (!text) {
      return;
    }
    await say({ text: `Alert noted: "${text}". Forwarding to monitoring.` });
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
>>>>>>> feature/golden-path-documentation
  }

  async start(): Promise<void> {
    if (!this.isConfigured || !this.app) {
      console.warn('SlackBotService: start skipped because configuration is missing.');
      return;
    }
    await this.app.start(Number(process.env.PORT) || 3000);
    console.log('⚡️ Slack Bot is running');
  }
}

const slackBot = new SlackBotService();

if (process.env.SLACK_BOT_AUTOSTART !== 'false') {
  slackBot.start().catch(console.error);
}

export default slackBot;
