export interface Integration {
  id: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: string;
}

export interface BulkTokenItem {
  token: string;
  platform: string;
}

export interface BulkProcessResult {
  success: boolean;
  message: string;
}

export type TokenState = 'idle' | 'processing' | 'success' | 'error';
