
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

function validateEnv() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new Error('Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL and/or NEXT_PUBLIC_SUPABASE_ANON_KEY');
  }
  return { url, anonKey };
}

export async function createClient() {
  const cookieStore = await cookies();
  const { url, anonKey } = validateEnv();

  return createServerClient(
    url,
    anonKey,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          // Merge: update only changed cookies, preserve others
          const existing = new Map(cookieStore.getAll().map(c => [c.name, c]));
          cookiesToSet.forEach(({ name, value }) => {
            existing.set(name, { name, value });
            cookieStore.set(name, value);
          });
        },
      },
    }
  );
}
