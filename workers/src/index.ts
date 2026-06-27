/**
 * EEN Construction — Unsubscribe + Resend Webhook Worker
 *
 * Routes:
 *   GET  /api/health          → health check
 *   GET  /unsubscribe         → redirect to main site with ?t= token
 *   POST /api/unsubscribe     → verify HMAC token, write suppression to KV
 *   POST /api/resend-webhook  → verify Svix signature, handle Resend events
 *
 * Required secrets (set via `wrangler secret put`):
 *   UNSUBSCRIBE_SECRET    — must match the Python outreach system
 *   RESEND_WEBHOOK_SECRET — signing secret from Resend webhook dashboard (whsec_...)
 *
 * KV namespace bound as SUPPRESSION.
 */

interface Env {
  SUPPRESSION: KVNamespace;
  UNSUBSCRIBE_SECRET: string;
  RESEND_WEBHOOK_SECRET?: string;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// ── Unsubscribe HMAC token verification ───────────────────────────────────

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

    const sigB64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = sigB64 + "=".repeat((4 - sigB64.length % 4) % 4);
    const actualSig = Uint8Array.from(atob(padded), c => c.charCodeAt(0));

    const valid = await crypto.subtle.verify("HMAC", cryptoKey, actualSig, msgBytes);
    return valid ? email : null;
  } catch {
    return null;
  }
}

// ── Resend / Svix webhook signature verification ──────────────────────────
// Spec: https://docs.svix.com/receiving/verifying-payloads/how

async function verifyResendSignature(
  rawBody: string,
  msgId: string,
  msgTimestamp: string,
  svixSig: string,
  secret: string,
): Promise<boolean> {
  // Reject replays older than 5 minutes
  const ts = parseInt(msgTimestamp, 10);
  if (isNaN(ts) || Math.abs(Math.floor(Date.now() / 1000) - ts) > 300) return false;

  // Decode the Svix secret (format: "whsec_<base64>")
  let secretBytes: Uint8Array;
  try {
    const b64 = secret.startsWith("whsec_") ? secret.slice(6) : secret;
    secretBytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  } catch {
    return false;
  }

  const signedContent = `${msgId}.${msgTimestamp}.${rawBody}`;
  const key = await crypto.subtle.importKey(
    "raw", secretBytes, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sigBytes = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(signedContent));
  const expectedSig = btoa(String.fromCharCode(...new Uint8Array(sigBytes)));

  // svix-signature may contain multiple "v1,<base64>" entries separated by spaces
  for (const part of svixSig.split(" ")) {
    if (part.startsWith("v1,") && part.slice(3) === expectedSig) return true;
  }
  return false;
}

// ── KV suppression helpers ────────────────────────────────────────────────

async function writeSuppression(
  kv: KVNamespace,
  email: string,
  reason: string,
  permanent: boolean,
): Promise<void> {
  const key = `suppression:${email.toLowerCase().trim()}`;
  const existing = await kv.get(key);
  if (existing) return; // idempotent
  await kv.put(key, JSON.stringify({
    email: email.toLowerCase().trim(),
    reason,
    added_at: new Date().toISOString(),
    permanent,
  }));
}

// ── Main fetch handler ────────────────────────────────────────────────────

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    // Health check
    if (url.pathname === "/api/health") {
      return Response.json(
        { ok: true, service: "een-construction-unsub", webhook: !!env.RESEND_WEBHOOK_SECRET },
        { headers: CORS }
      );
    }

    // Unsubscribe page redirect
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

      await writeSuppression(env.SUPPRESSION, email, "unsubscribe", true);
      console.log(`[Unsubscribe] Suppressed: ${email}`);
      return Response.json({ ok: true }, { headers: CORS });
    }

    // Resend webhook receiver
    if (request.method === "POST" && url.pathname === "/api/resend-webhook") {
      const rawBody = await request.text();

      // Signature verification
      const msgId = request.headers.get("svix-id") ?? "";
      const msgTimestamp = request.headers.get("svix-timestamp") ?? "";
      const svixSig = request.headers.get("svix-signature") ?? "";
      const webhookSecret = env.RESEND_WEBHOOK_SECRET ?? "";

      if (!webhookSecret) {
        console.error("[Webhook] RESEND_WEBHOOK_SECRET not set — rejecting");
        return Response.json({ error: "Webhook not configured" }, { status: 500, headers: CORS });
      }

      const valid = await verifyResendSignature(rawBody, msgId, msgTimestamp, svixSig, webhookSecret);
      if (!valid) {
        console.warn("[Webhook] Invalid signature");
        return Response.json({ error: "Invalid signature" }, { status: 401, headers: CORS });
      }

      let event: { type: string; data: { to?: string[]; email_id?: string } };
      try {
        event = JSON.parse(rawBody);
      } catch {
        return Response.json({ error: "Invalid JSON" }, { status: 400, headers: CORS });
      }

      const { type, data } = event;
      const recipient = (data?.to ?? [])[0] ?? "";
      console.log(`[Webhook] ${type} → ${recipient}`);

      switch (type) {
        case "email.bounced":
          // All bounces from Resend are hard bounces (soft bounces appear as delivery_delayed)
          if (recipient) await writeSuppression(env.SUPPRESSION, recipient, "bounce", true);
          break;

        case "email.complained":
          if (recipient) await writeSuppression(env.SUPPRESSION, recipient, "complaint", true);
          break;

        case "email.delivered":
        case "email.opened":
        case "email.clicked":
        case "email.sent":
        case "email.delivery_delayed":
          // Log only — no suppression action needed
          console.log(`[Webhook] ${type} for ${recipient} (${data?.email_id ?? ""})`);
          break;

        default:
          console.log(`[Webhook] Unhandled event type: ${type}`);
      }

      return Response.json({ ok: true }, { headers: CORS });
    }

    return Response.json({ error: "Not found" }, { status: 404, headers: CORS });
  },
};
