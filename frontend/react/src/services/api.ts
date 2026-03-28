import { projectId, publicAnonKey } from "@/lib/supabase";

const BASE_URL = `https://${projectId}.supabase.co/functions/v1/server/make-server-a903c193`;

const headers: Record<string, string> = {
  "Content-Type": "application/json",
  ...(publicAnonKey ? { Authorization: `Bearer ${publicAnonKey}` } : {}),
};

export async function fetchSection<T = unknown>(section: string): Promise<T> {
  const res = await fetch(`${BASE_URL}/data/${section}`, { headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`[${section}] HTTP ${res.status}: ${text}`);
  }
  const json = await res.json();
  return (json?.data ?? json) as T;
}
