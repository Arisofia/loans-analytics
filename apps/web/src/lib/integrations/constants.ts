export type Platform = 'stripe' | 'plaid' | 'codat' | 'xero';
export type TokenStatus = 'active' | 'expired' | 'pending';
export const PLATFORMS: Platform[] = ['stripe', 'plaid', 'codat', 'xero'];
export const PLATFORM_LABELS: Record<Platform, string> = { stripe: 'Stripe', plaid: 'Plaid', codat: 'Codat', xero: 'Xero' };
export const SUPABASE_FN_BASE = process.env.NEXT_PUBLIC_SUPABASE_FUNCTION_URL || '';
export const INTEGRATION_CONSTANTS = { MAX_RETRIES: 3, TIMEOUT_MS: 10000 };
