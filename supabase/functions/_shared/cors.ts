const allowList = (Deno.env.get("CORS_ALLOWED_ORIGINS") ?? "")
  .split(",")
  .map((origin) => origin.trim())
  .filter((origin) => origin.length > 0);

function resolveOrigin(origin: string | null): string {
  if (!origin || allowList.length === 0) {
    return "null";
  }

  return allowList.includes(origin) ? origin : "null";
}

export function corsHeadersFor(origin: string | null) {
  return {
    "Access-Control-Allow-Origin": resolveOrigin(origin),
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
  };
}
