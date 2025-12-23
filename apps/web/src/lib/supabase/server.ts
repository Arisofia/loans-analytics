<<<<<<< HEAD
import { createServerClient } from '@supabase/ssr';
export async function createClient() {
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
=======
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'

function resolveSupabaseConfig() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!url || !anonKey) {
    throw new Error('Supabase environment variables are not configured')
  }

  return { url, anonKey }
}

const { url: supabaseUrl, anonKey: supabaseAnonKey } = resolveSupabaseConfig()

type ServerCookie = {
  name: string
  value: string
  options: CookieOptions
}

export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll().map(({ name, value }) => ({ name, value }))
      },
      setAll(cookiesToSet: ServerCookie[]) {
        try {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        } catch {
          // Ignored in Server Components
        }
      },
    },
  })
>>>>>>> origin/main
}
