// Map Meta fields to canonical warehouse schema
export function transformCampaign(raw: { id: string; name: string; status: string; effective_status: string; }) {
  return {
    campaign_id: raw.id,
    campaign_name: raw.name,
    status: raw.status,
    effective_status: raw.effective_status,
  };
}

export function transformInsight(raw: any) {
  return {
    impressions: Number(raw.impressions) || 0,
    clicks: Number(raw.clicks) || 0,
    spend: Number(raw.spend) || 0,
    actions: raw.actions || [],
  };
}
