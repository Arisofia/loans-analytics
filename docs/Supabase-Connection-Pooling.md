# Supabase Connection Pooling Guidance
Using Supabase's connection pooler (PgBouncer) is required for serverless deployments (e.g., Vercel). Direct connections from serverless functions create many short-lived Postgres sessions and quickly exhaust database connection limits.
## Why use the connection pooler

- Reuses a small set of Postgres connections and hands them out per request, preventing connection storms.
- Works over IPv4-only networks and is the recommended production configuration for Vercel deployments.
## Steps to configure

1. **Retrieve the database password** from **Settings → Database → Connection info** in your Supabase project (reset if needed).
2. **Copy the pooler connection string** from **Connection strings → Connection pooling**. It follows the pattern:
   ```
   postgresql://postgres.<project-ref>:<PASSWORD>@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
3. **Store the URI in an environment file** (never hardcode secrets):
   - Create a `.env.local` file at the project root.
   - Add `DATABASE_URL="postgresql://postgres.<project-ref>:<PASSWORD>@aws-0-us-east-1.pooler.supabase.com:5432/postgres"`.
4. **Point your ORM or database client to the environment variable.** For example, in Prisma:
   ```prisma
   datasource db {
     provider = "postgresql"
     url      = env("DATABASE_URL")
   }
   ```
5. **Set the `DATABASE_URL` environment variable in Vercel** (Settings → Environment Variables) for Production (and optionally Preview/Development) using the same pooler URI.
## Git hygiene

Ensure `.gitignore` excludes local env files so secrets are not committed. Add `.env*.local` to the ignore list if it is not already present.
