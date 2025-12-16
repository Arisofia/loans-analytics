import { createServerSupabaseClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export function createClient() {
  // For Next.js App Router SSR use { cookies }.
  // If you use pages/older Next.js, pass { req, res } instead.
  return createServerSupabaseClient({
    cookies,
  });
}
