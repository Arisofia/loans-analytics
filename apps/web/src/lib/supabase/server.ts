import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export async function createClient() {
  const cookieStore = cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: async (entries) => {
          entries.forEach(({ name, value, options }) => {
            if (value) {
              cookieStore.set(name, value, options);
            } else {
              cookieStore.delete(name);
            }
          });
        },
      },
    },
  );
}
