import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { corsHeadersFor } from "../_shared/cors.ts";

Deno.serve((req) => {
  const headers = {
    ...corsHeadersFor(req.headers.get("origin")),
    "Content-Type": "application/json",
  };

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers });
  }

  return new Response(
    JSON.stringify({
      error:
        "This function is disabled by default. Enable it explicitly in supabase/config.toml if required.",
    }),
    { status: 410, headers },
  );
});
