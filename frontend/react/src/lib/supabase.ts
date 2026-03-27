/**
 * Supabase project configuration.
 *
 * In production, set VITE_SUPABASE_PROJECT_ID and VITE_SUPABASE_ANON_KEY
 * in your environment or .env file.
 */
export const projectId: string =
  import.meta.env.VITE_SUPABASE_PROJECT_ID ?? "sddviizcgheusvwqpthm";

export const publicAnonKey: string =
  import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";
