import { createServerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';

export function createClient() {
  // You may need to pass { cookies } or { req, res } depending on your Next.js version and usage
  return createServerClient({
    cookies,
  });
}
import { createServerClient } from '@supabase/auth-helpers-nextjs';import { cookies } from 'next/headers';export function createClient() {  // You may need to pass { cookies } or { req, res } depending on your Next.js version and usage  return createServerClient({    cookies,  });}
