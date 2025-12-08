/**
 * Minimal placeholder supabaseClient for builds.
 * Replace with your real client initialization.
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? '';
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export function isSupabaseConfigured() {
  return !!SUPABASE_URL && !!SUPABASE_ANON_KEY;
}
