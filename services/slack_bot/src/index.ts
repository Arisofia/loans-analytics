import { App, Say, SlackEventMiddlewareArgs, Context } from '@slack/bolt';
import axios from 'axios';

interface KPIAlert {
  department: string;
  kpi_name: string;
  current_value: number;
  threshold: number;
  severity: 'critical' | 'warning' | 'info';
  run_id: string;
  timestamp: string;
}

class SlackBotService {
  private app: App;
  private kpiWebhookUrl: string;
  private alertQueue: KPIAlert[] = [];

  constructor() {
    this.app = new App({
      token: process.env.SLACK_BOT_TOKEN,
      signingSecret: process.env.SLACK_SIGNING_SECRET,
    });
    this.kpiWebhookUrl = process.env.KPI_WEBHOOK_URL || '';
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    // Listen for KPI alert events from data orchestration pipeline
    this.app.event('app_mention', async ({ event, say }: SlackEventMiddlewareArgs<'app_mention'> & { say: Say }) => {
      if (event.text.includes('kpi') || event.text.includes('alert')) {
        await this.handleKPIQuery(event, say);
      }
    });

    // Listen for message events in alert channels
    this.app.message(/:warn:/i, async ({ message, say }: any) => {
      await this.handleAlertMessage(message, say);
    });
  }

  async sendKPIAlert(alert: KPIAlert): Promise<void> {
    const channelMap: Record<string, string> = {
      'Risk': '#kpi-risk-alerts',
      'Growth': '#kpi-growth-alerts',
      'Finance': '#kpi-finance-alerts',
      'Compliance': '#kpi-compliance-alerts',
      'Technology': '#kpi-tech-alerts',
      'Marketing': '#kpi-marketing-alerts',
      'Sales': '#kpi-sales-alerts',
    };

    const channel = channelMap[alert.department] || '#kpi-alerts';
    const color = alert.severity === 'critical' ? '#DC3545' : alert.severity === 'warning' ? '#FFC107' : '#0DCAF0';

    try {
      await this.app.client.chat.postMessage({
        channel,
        blocks: [
          {
            type: 'header',
            text: {
              type: 'plain_text',
              text: `${alert.severity.toUpperCase()}: ${alert.kpi_name}`,
              emoji: true,
            },
          },
          {
            type: 'section',
            fields: [
              {
                type: 'mrkdwn',
                text: `*Department:*\n${alert.department}`,
              },
              {
                type: 'mrkdwn',
                text: `*Current Value:*\n${alert.current_value}`,
              },
              {
                type: 'mrkdwn',
                text: `*Threshold:*\n${alert.threshold}`,
              },
              {
                type: 'mrkdwn',
                text: `*Run ID:*\n${alert.run_id}`,
              },
            ],
          },
          {
            type: 'context',
            elements: [
              {
                type: 'mrkdwn',
                text: `_Timestamp: ${alert.timestamp}_`,
              },
            ],
          },
          {
            type: 'divider',
          },
        ],
      });
    } catch (error) {
      console.error(`Failed to send alert to ${channel}:`, error);
    }
  }

  private async handleKPIQuery(event: any, say: Say): Promise<void> {
    try {
      const response = await axios.get(`${this.kpiWebhookUrl}/latest`, {
        headers: { 'Authorization': `Bearer ${process.env.API_KEY}` },
      });

      const kpis = response.data;
      let blocks: any[] = [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: 'Latest KPI Dashboard',
            emoji: true,
          },
        },
      ];

      for (const kpi of kpis.slice(0, 5)) {
        blocks.push({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*${kpi.name}* (${kpi.department})\nValue: ${kpi.value} | Status: ${kpi.status}`,
          },
        });
      }

      await say({ blocks });
    } catch (error) {
      await say('Could not retrieve KPI data. Please try again later.');
    }
  }

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
  }

  async start(): Promise<void> {
    await this.app.start(Number(process.env.PORT) || 3000);
    console.log('⚡️ Slack Bot is running');
  }
}

const slackBot = new SlackBotService();
slackBot.start().catch(console.error);

export default slackBot;
