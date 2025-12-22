// Ingest jobs to fetch campaigns, adsets, insights, audiences
import { MetaGraphClient } from './index';

export async function fetchCampaigns(client: MetaGraphClient, adAccountId: string) {
  return client.get(`${adAccountId}/campaigns`, {
    fields: 'id,name,status,effective_status',
    limit: 50,
  });
}

export async function fetchAdsets(client: MetaGraphClient, campaignId: string) {
  return client.get(`${campaignId}/adsets`, {
    fields: 'id,name,status',
    limit: 50,
  });
}

export async function fetchInsights(client: MetaGraphClient, adAccountId: string, since: string, until: string) {
  return client.get(`${adAccountId}/insights`, {
    fields: 'impressions,clicks,spend,actions',
    time_range: JSON.stringify({ since, until }),
    limit: 100,
  });
}
