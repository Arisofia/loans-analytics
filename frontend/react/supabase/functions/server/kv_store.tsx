/**
 * Supabase Edge Function — KV Store interface
 * Backs the Figma Make data store using the `kv_store_a903c193` table.
 *
 * Table schema:
 *   CREATE TABLE kv_store_a903c193 (
 *     key TEXT PRIMARY KEY,
 *     value JSONB NOT NULL,
 *     updated_at TIMESTAMPTZ DEFAULT now()
 *   );
 *
 * This file is kept as a deployment reference.
 * To deploy: `supabase functions deploy server`
 */

import { createClient } from "jsr:@supabase/supabase-js@2";

const TABLE = "kv_store_a903c193";

function getClient() {
  return createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );
}

export async function set(key: string, value: unknown): Promise<void> {
  const client = getClient();
  await client
    .from(TABLE)
    .upsert({ key, value, updated_at: new Date().toISOString() });
}

export async function get<T = unknown>(key: string): Promise<T | null> {
  const client = getClient();
  const { data } = await client
    .from(TABLE)
    .select("value")
    .eq("key", key)
    .single();
  return (data?.value as T) ?? null;
}

export async function del(key: string): Promise<void> {
  const client = getClient();
  await client.from(TABLE).delete().eq("key", key);
}

export async function mset(
  entries: Array<{ key: string; value: unknown }>
): Promise<void> {
  const client = getClient();
  await client.from(TABLE).upsert(
    entries.map((e) => ({
      key: e.key,
      value: e.value,
      updated_at: new Date().toISOString(),
    }))
  );
}

export async function mget<T = unknown>(
  keys: string[]
): Promise<Array<T | null>> {
  const client = getClient();
  const { data } = await client
    .from(TABLE)
    .select("key, value")
    .in("key", keys);
  const map = new Map((data ?? []).map((r: { key: string; value: unknown }) => [r.key, r.value]));
  return keys.map((k) => (map.get(k) as T) ?? null);
}

export async function mdel(keys: string[]): Promise<void> {
  const client = getClient();
  await client.from(TABLE).delete().in("key", keys);
}

export async function getByPrefix<T = unknown>(
  prefix: string
): Promise<Array<{ key: string; value: T }>> {
  const client = getClient();
  const { data } = await client
    .from(TABLE)
    .select("key, value")
    .like("key", `${prefix}%`);
  return (data ?? []).map((r: { key: string; value: unknown }) => ({
    key: r.key,
    value: r.value as T,
  }));
}
