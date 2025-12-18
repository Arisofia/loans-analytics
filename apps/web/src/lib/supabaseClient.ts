import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import type { LandingPageData } from '../types/landingPage'

type Database = {
  public: {
    Tables: {
      landing_page_data: {
        Row: LandingPageData
        Insert: LandingPageData
        Update: Partial<LandingPageData>
      }
    }
  }
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim()
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim()

const hasValidSupabaseUrl = Boolean(supabaseUrl && /^https?:\/\//.test(supabaseUrl))
const hasSupabaseEnv = Boolean(hasValidSupabaseUrl && supabaseAnonKey)

export const supabase: SupabaseClient<Database> | null = hasSupabaseEnv
  ? createClient<Database>(supabaseUrl as string, supabaseAnonKey as string)
  : null

export const isSupabaseConfigured = hasSupabaseEnv
