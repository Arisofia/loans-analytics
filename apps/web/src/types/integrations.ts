// Represents a third-party integration connection.
export interface Integration {
  id: string
  name: string
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
}

// Represents a token item for bulk integration operations.
export interface BulkTokenItem {
  token: string
  platform: string
  accountId?: string
  status?: string
  message?: string
  attempts?: number
  tokenId?: string
  resultId?: string
}

// Represents the result of a bulk integration process.
export interface BulkProcessResult {
  status: 'success' | 'error'
  detail?: string
  tokenId?: string
  item?: BulkTokenItem
}

export interface TokenState {
  status: 'idle' | 'processing' | 'success' | 'error' | 'syncing'
  message?: string
  token?: string
  accountId?: string
  tokenId?: string
}
