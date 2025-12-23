import { transformCampaign, transformInsight } from './transform';

describe('transformCampaign', () => {
  it('should map campaign fields', () => {
    const raw = { id: '1', name: 'Test', status: 'ACTIVE', effective_status: 'ACTIVE' };
    expect(transformCampaign(raw)).toEqual({
      campaign_id: '1',
      campaign_name: 'Test',
      status: 'ACTIVE',
      effective_status: 'ACTIVE',
    });
  });
});

describe('transformInsight', () => {
  it('should map insight fields', () => {
    const raw = { impressions: '100', clicks: '10', spend: '5.5', actions: [{ action_type: 'like', value: '2' }] };
    expect(transformInsight(raw)).toEqual({
      impressions: 100,
      clicks: 10,
      spend: 5.5,
      actions: [{ action_type: 'like', value: '2' }],
    });
  });
});
