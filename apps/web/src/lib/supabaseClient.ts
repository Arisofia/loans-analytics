import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import type { LandingPageData } from '../types/landingPage'

type Database = {
  public: {
    Tables: {
      landing_page_data: {
        Row: LandingPageData
      }
    }
  }
}

<<<<<<< HEAD
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim()
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim()

const hasValidSupabaseUrl = Boolean(supabaseUrl && /^https?:\/\//.test(supabaseUrl))
const hasSupabaseEnv = Boolean(hasValidSupabaseUrl && supabaseAnonKey)

export const supabase: SupabaseClient<Database> | null = hasSupabaseEnv
  ? createClient<Database>(supabaseUrl as string, supabaseAnonKey as string)
  : null

export const isSupabaseConfigured = hasSupabaseEnv
=======
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

export const supabase: SupabaseClient<Database> | null =
  supabaseUrl && supabaseAnonKey ? createClient<Database>(supabaseUrl, supabaseAnonKey) : null
>>>>>>> origin/main
