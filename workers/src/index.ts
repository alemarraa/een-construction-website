/**
 * EEN Construction — Unsubscribe Worker
 *
 * Handles POST /api/unsubscribe from the email unsubscribe link.
 * Verifies an HMAC-signed token and writes the suppression to Cloudflare KV.
 *
 * Required secrets (set via `wrangler secret put`):
 *   UNSUBSCRIBE_SECRET — must match the Python outreach system
 *
 * KV namespace bound as SUPPRESSION.
 */

interface Env {
  SUPPRESSION: KVNamespace;
  UNSUBSCRIBE_SECRET: string;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

async function verifyToken(token: string, secret: string): Promise<string | null> {
  if (!token || !secret) return null;
  const parts = token.split(".");
  if (parts.length !== 2) return null;

  try {
    const emailBytes = Uint8Array.from(atob(parts[0].replace(/-/g, "+").replace(/_/g, "/")), c => c.charCodeAt(0));
    const email = new TextDecoder().decode(emailBytes).toLowerCase().trim();

    const keyBytes = new TextEncoder().encode(secret);
    const msgBytes = new TextEncoder().encode(`unsub:${email}`);
    const cryptoKey = await crypto.subtle.importKey("raw", keyBytes, { name: "HMAC", hash: "SHA-256" }, false, ["verify"]);

    // Decode actual sig
    const sigB64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = sigB64 + "=".repeat((4 - sigB64.length % 4) % 4);
    const actualSig = Uint8Array.from(atob(padded), c => c.charCodeAt(0));

    const valid = await crypto.subtle.verify("HMAC", cryptoKey, actualSig, msgBytes);
    if (!valid) return null;
    return email;
  } catch {
    return null;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    // Health check
    if (url.pathname === "/api/health") {
      return Response.json({ ok: true, service: "een-construction-unsub" }, { headers: CORS });
    }

    // Unsubscribe page redirect — redirect to the main site
    if (request.method === "GET" && url.pathname === "/unsubscribe") {
      const token = url.searchParams.get("t") ?? "";
      return Response.redirect(`https://eenconstruction.com/unsubscribe?t=${encodeURIComponent(token)}`, 302);
    }

    // Unsubscribe API
    if (request.method === "POST" && url.pathname === "/api/unsubscribe") {
      let token: string;
      try {
        const body = await request.json() as { token?: string };
        token = (body?.token ?? "").toString().trim();
      } catch {
        return Response.json({ error: "Invalid request body" }, { status: 400, headers: CORS });
      }

      if (!token || token.length > 500 || !/^[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+$/.test(token)) {
        return Response.json({ error: "Invalid token format" }, { status: 400, headers: CORS });
      }

      const email = await verifyToken(token, env.UNSUBSCRIBE_SECRET);
      if (!email) {
        return Response.json({ error: "Token verification failed" }, { status: 400, headers: CORS });
      }

      // Write to KV
      const key = `suppression:${email}`;
      const existing = await env.SUPPRESSION.get(key);
      if (!existing) {
        await env.SUPPRESSION.put(key, JSON.stringify({
          email,
          reason: "unsubscribe",
          added_at: new Date().toISOString(),
          permanent: true,
        }));
      }

      console.log(`[Unsubscribe] Suppressed: ${email}`);
      return Response.json({ ok: true }, { headers: CORS });
    }

    return Response.json({ error: "Not found" }, { status: 404, headers: CORS });
  },
};
