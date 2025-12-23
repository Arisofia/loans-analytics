<<<<<<< HEAD
import { createClient } from '@/lib/supabase/server';
import { revalidatePath } from 'next/cache';
import { type NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (user) {
    await supabase.auth.signOut();
  }
  revalidatePath('/', 'layout');
  return NextResponse.redirect(new URL('/login', req.url), {
    status: 302,
  });
=======
import { type NextRequest, NextResponse } from 'next/server'
import { createClient } from '../../../src/lib/supabase/server'

export async function POST(request: NextRequest) {
  const supabase = await createClient()

  // Check if we have a session
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (session) {
    await supabase.auth.signOut()
  }

  return NextResponse.redirect(new URL('/', request.url), {
    status: 302,
  })
>>>>>>> origin/main
}
