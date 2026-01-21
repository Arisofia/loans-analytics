export const PLATFORMS = ['meta', 'linkedin', 'custom'] as const

export type Platform = (typeof PLATFORMS)[number]

export const SUPABASE_FN_BASE = process.env.NEXT_PUBLIC_SUPABASE_FN_BASE?.replace(/\/\/$/, '') || ''

export const PLATFORM_LABELS: Record<Platform, string> = {
  meta: 'Meta',
  linkedin: 'LinkedIn',
  custom: 'Custom API',
}

export const PLATFORM_ICONS: Record<Platform, string> = {
  meta: 'ℱ',
  linkedin: '🔗',
  custom: '🔌',
}

export type TokenStatus = 'connected' | 'disconnected' | 'syncing' | 'error'

export const STATUS_COLORS: Record<TokenStatus, string> = {
  connected: '#01766e',
  disconnected: '#9e9e9e',
  syncing: '#ff9800',
  error: '#f44336',
}
