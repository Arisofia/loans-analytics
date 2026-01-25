import axios from 'axios';

interface Contact {
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  company?: string;
  dealStage?: string;
  kpiMetrics?: Record<string, number>;
}

interface Deal {
  dealname: string;
  dealstage: string;
  amount?: number;
  closedate?: string;
  customer_id?: string;
  kpi_impact?: string;
}

class HubSpotSyncService {
  private hubspotApiKey: string;
  private kpiServiceUrl: string;
  private baseUrl = 'https://api.hubapi.com';
  private lastSyncTime: Record<string, number> = {};

  constructor() {
    this.hubspotApiKey = process.env.HUBSPOT_API_KEY || '';
    this.kpiServiceUrl = process.env.KPI_SERVICE_URL || '';
  }

  async syncContactsWithKPIs(): Promise<void> {
    try {
      // Get all contacts from HubSpot
      const contactsResponse = await axios.get(`${this.baseUrl}/crm/v3/objects/contacts`, {
        headers: {
          'Authorization': `Bearer ${this.hubspotApiKey}`,
          'Content-Type': 'application/json',
        },
        params: {
          limit: 100,
          properties: ['firstname', 'lastname', 'email', 'phone', 'company'],
        },
      });

      const contacts = contactsResponse.data.results || [];

      // Fetch KPI data for each contact
      for (const contact of contacts) {
        const contactData: Contact = {
          email: contact.properties.email?.value || '',
          firstName: contact.properties.firstname?.value,
          lastName: contact.properties.lastname?.value,
          phone: contact.properties.phone?.value,
          company: contact.properties.company?.value,
        };

        // Fetch associated KPI metrics
        const kpiResponse = await axios.get(`${this.kpiServiceUrl}/customer/${contactData.email}`, {
          headers: { 'Authorization': `Bearer ${process.env.API_KEY}` },
        });

        if (kpiResponse.data) {
          contactData.kpiMetrics = kpiResponse.data.metrics;
        }

        // Update contact with KPI data
        await this.updateContactWithKPIs(contact.id, contactData);
      }

      this.lastSyncTime['contacts'] = Date.now();
      console.log('✅ Contacts synced with KPI data');
    } catch (error) {
      console.error('Failed to sync contacts:', error);
    }
  }

  async syncDealsWithKPIs(): Promise<void> {
    try {
      // Get all deals from HubSpot
      const dealsResponse = await axios.get(`${this.baseUrl}/crm/v3/objects/deals`, {
        headers: {
          'Authorization': `Bearer ${this.hubspotApiKey}`,
          'Content-Type': 'application/json',
        },
        params: {
          limit: 100,
          properties: ['dealname', 'dealstage', 'amount', 'closedate'],
        },
      });

      const deals = dealsResponse.data.results || [];

      // Enhance deals with KPI impact analysis
      for (const deal of deals) {
        const dealData: Deal = {
          dealname: deal.properties.dealname?.value || '',
          dealstage: deal.properties.dealstage?.value || '',
          amount: deal.properties.amount?.value,
          closedate: deal.properties.closedate?.value,
        };

        // Analyze KPI impact of deal
        const impactAnalysis = await axios.post(`${this.kpiServiceUrl}/analysis/deal-impact`, dealData, {
          headers: { 'Authorization': `Bearer ${process.env.API_KEY}` },
        });

        if (impactAnalysis.data?.impact_summary) {
          dealData.kpi_impact = impactAnalysis.data.impact_summary;
          await this.updateDealWithKPIImpact(deal.id, dealData);
        }
      }

      this.lastSyncTime['deals'] = Date.now();
      console.log('✅ Deals synced with KPI impact analysis');
    } catch (error) {
      console.error('Failed to sync deals:', error);
    }
  }

  private async updateContactWithKPIs(contactId: string, data: Contact): Promise<void> {
    try {
      await axios.patch(
        `${this.baseUrl}/crm/v3/objects/contacts/${contactId}`,
        {
          properties: {
            kpi_metrics: JSON.stringify(data.kpiMetrics || {}),
            deal_stage: data.dealStage,
          },
        },
        {
          headers: {
            'Authorization': `Bearer ${this.hubspotApiKey}`,
            'Content-Type': 'application/json',
          },
        }
      );
    } catch (error) {
      console.error(`Failed to update contact ${contactId}:`, error);
    }
  }

  private async updateDealWithKPIImpact(dealId: string, data: Deal): Promise<void> {
    try {
      await axios.patch(
        `${this.baseUrl}/crm/v3/objects/deals/${dealId}`,
        {
          properties: {
            kpi_impact: data.kpi_impact,
          },
        },
        {
          headers: {
            'Authorization': `Bearer ${this.hubspotApiKey}`,
            'Content-Type': 'application/json',
          },
        }
      );
    } catch (error) {
      console.error(`Failed to update deal ${dealId}:`, error);
    }
  }

  async start(syncIntervalMs: number = 3600000): Promise<void> {
    console.log('🔄 HubSpot Sync Service started');
    
    // Initial sync
    await this.syncContactsWithKPIs();
    await this.syncDealsWithKPIs();

    // Schedule recurring syncs
    setInterval(async () => {
      await this.syncContactsWithKPIs();
      await this.syncDealsWithKPIs();
    }, syncIntervalMs);
  }
}

const hubspotSync = new HubSpotSyncService();
hubspotSync.start().catch(console.error);

export default hubspotSync;
