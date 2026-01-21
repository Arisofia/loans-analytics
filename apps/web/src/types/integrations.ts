export interface Integration {
  id: string
  name: string
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
}

export interface BulkTokenItem {
  token: string
  platform: string
  accountId?: string
  status?: string
  message?: string
  attempts?: number
}

export interface BulkProcessResult {
  status: 'success' | 'error'
  detail?: string
  tokenId?: string
  item?: BulkTokenItem
}

export type TokenState = 'idle' | 'processing' | 'success' | 'error'
