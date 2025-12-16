import { createServerSupabaseClient } from '@supabase/auth-helpers-nextjs';
import { type NextRequest, NextResponse } from 'next/server';

export async function middleware(request: NextRequest) {
  // Example: create a Supabase client for SSR/Edge
  const supabase = createServerSupabaseClient({ cookies: request.cookies });
  // ...add your logic here (auth, redirects, etc.)
  return NextResponse.next();
}
