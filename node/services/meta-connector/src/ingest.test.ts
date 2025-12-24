import { fetchCampaigns } from './ingest';
import { MetaGraphClient } from './index';

describe('fetchCampaigns', () => {
  it('should call client.get with correct params', async () => {
    const mockGet = jest.fn().mockResolvedValue({ data: [] });
    const client = { get: mockGet } as unknown as MetaGraphClient;
    await fetchCampaigns(client, 'act_123');
    expect(mockGet).toHaveBeenCalledWith('act_123/campaigns', expect.any(Object));
  });
});
