// Export Meta data to Azure Blob Storage
import { MetaGraphClient } from './index';
import { fetchCampaigns, fetchInsights } from './ingest';
import { transformCampaign, transformInsight } from './transform';
import { BlobServiceClient } from '@azure/storage-blob';

const AZURE_STORAGE_CONNECTION_STRING = process.env.AZURE_STORAGE_CONNECTION_STRING || '';
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';
const META_AD_ACCOUNT_ID = process.env.META_AD_ACCOUNT_ID || '';
const AZURE_CONTAINER = process.env.AZURE_CONTAINER || 'meta-data';

async function exportMetaDataToAzure() {
  if (!AZURE_STORAGE_CONNECTION_STRING || !META_ACCESS_TOKEN || !META_AD_ACCOUNT_ID) {
    throw new Error('Missing required environment variables.');
  }

  const client = new MetaGraphClient(META_ACCESS_TOKEN);
  const campaignsRaw = await fetchCampaigns(client, META_AD_ACCOUNT_ID);
  const campaigns = (campaignsRaw.data || []).map(transformCampaign);

  const today = new Date().toISOString().slice(0, 10);
  const insightsRaw = await fetchInsights(client, META_AD_ACCOUNT_ID, today, today);
  const insights = (insightsRaw.data || []).map(transformInsight);

  const blobServiceClient = BlobServiceClient.fromConnectionString(AZURE_STORAGE_CONNECTION_STRING);
  const containerClient = blobServiceClient.getContainerClient(AZURE_CONTAINER);
  await containerClient.createIfNotExists();

  // Upload campaigns
  const campaignsBlob = containerClient.getBlockBlobClient(`campaigns_${today}.json`);
  await campaignsBlob.upload(JSON.stringify(campaigns, null, 2), Buffer.byteLength(JSON.stringify(campaigns)));

  // Upload insights
  const insightsBlob = containerClient.getBlockBlobClient(`insights_${today}.json`);
  await insightsBlob.upload(JSON.stringify(insights, null, 2), Buffer.byteLength(JSON.stringify(insights)));

  console.log('Meta data exported to Azure Blob Storage successfully.');
}

exportMetaDataToAzure().catch((err) => {
  console.error('Export failed:', err);
  process.exit(1);
});
