# Supabase Local (Docker Desktop)

Prereqs: Docker Desktop running; supabase CLI installed; .env with NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
Commands:
supabase login
supabase link --project-ref pljjgdtczxmrxydfuaep
supabase start
supabase status
Health: API http://127.0.0.1:54321, DB 127.0.0.1:54322, Studio http://127.0.0.1:54323.
Cleanup: supabase stop --no-backup
