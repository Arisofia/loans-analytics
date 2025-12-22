import type { Platform, TokenStatus } from '@/lib/integrations/constants'

export type TokenState = {
  token?: string
  accountId?: string
  status: TokenStatus
  lastSync?: string
  message?: string
  tokenId?: string
}

export type BulkTokenItem = {
  platform: Platform
  token: string
  accountId?: string
  status?: TokenStatus | 'pending' | 'success' | 'retrying' | 'error'
  attempts?: number
  message?: string
  resultId?: string
}

export type BulkProcessResult = {
  item: BulkTokenItem
  status: 'success' | 'error'
  detail?: string
  tokenId?: string
}
