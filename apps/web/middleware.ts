import { type NextRequest, NextResponse } from 'next/server';
/**
 * Temporary no-op middleware to unblock builds.
 * Replace with real Supabase middleware logic when @supabase/ssr is available.
 */
export async function middleware(_request: NextRequest) {
  return NextResponse.next();
}
// Optional matcher to limit middleware to specific routes. Uncomment and adjust as needed.
// export const config = {
//   matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
// };
