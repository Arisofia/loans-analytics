// Map Meta fields to canonical warehouse schema
export function transformCampaign(raw: any) {
  return {
    campaign_id: raw.id,
    campaign_name: raw.name,
    status: raw.status,
    effective_status: raw.effective_status,
  };
}

export function transformInsight(raw: any) {
  return {
    impressions: Number(raw.impressions),
    clicks: Number(raw.clicks),
    spend: Number(raw.spend),
    actions: raw.actions || [],
  };
}
