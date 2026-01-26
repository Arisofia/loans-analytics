import { projectId, publicAnonKey } from '@/utils/supabase/info'

export { supabaseConfigAvailable } from '@/utils/supabase/info'

export type IntegrationPlatform = 'meta' | 'linkedin' | 'custom'

const functionSlug = process.env.NEXT_PUBLIC_SUPABASE_FUNCTION_SLUG || 'make-server-a7c39296'
const integrationBaseUrl = `https://${projectId}.supabase.co/functions/v1/${functionSlug}/integrations`

export const integrationEndpoints = {
  connect: `${integrationBaseUrl}/connect`,
  disconnect: `${integrationBaseUrl}/disconnect`,
  status: `${integrationBaseUrl}/status`,
  sync: `${integrationBaseUrl}/sync`,
} as const

export const integrationHeaders = {
  Authorization: `Bearer ${publicAnonKey}`,
  'Content-Type': 'application/json',
}

export const parseErrorMessage = async (
  response: Response,
  fallbackMessage: string
): Promise<string> => {
  try {
    const error = (await response.json()) as { message?: string }
    if (error?.message) {
      return error.message
    }
  } catch {
    // ignore JSON parse failures and fall back to text
  }

  try {
    const text = await response.text()
    if (text) return text
  } catch {
    // ignore text parse failures and fall back to the provided default message
  }

  return fallbackMessage
}
