/**
 * Minimal placeholders for integration constants and types.
 * Extend/replace with full definitions used by your app.
 */
export const PLATFORMS = ['github', 'gitlab'] as const;
export type Platform = (typeof PLATFORMS)[number];
export const PLATFORM_LABELS: Record<Platform, string> = {
  github: 'GitHub',
  gitlab: 'GitLab',
};
export const PLATFORM_ICONS: Record<Platform, string> = {
  github: '🐙',
  gitlab: '🦊',
};
export const STATUS_COLORS: Record<string, string> = {
  valid: 'green',
  invalid: 'red',
  connected: 'green',
  disconnected: 'gray',
  syncing: 'blue',
  error: 'red',
};
export const SUPABASE_FN_BASE = '/api/fn';
export type TokenStatus = 'valid' | 'invalid' | 'connected' | 'disconnected' | 'syncing' | 'error';
