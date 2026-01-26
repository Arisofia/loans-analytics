import { createClient, type SupabaseClient } from '@supabase/supabase-js'
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
const assertSupabaseEnv = (): void => {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Supabase client missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.'
    )
  }
}
export const createSupabaseClient = (
  url: string,
  anonKey: string
): SupabaseClient => createClient(url, anonKey)
let cachedClient: SupabaseClient | null = null
export const getSupabaseClient = (): SupabaseClient => {
  if (cachedClient) {
    return cachedClient
  }
  assertSupabaseEnv()
  cachedClient = createSupabaseClient(
    supabaseUrl as string,
    supabaseAnonKey as string
  )
  return cachedClient
}
