import crypto from "crypto";
import express from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";
import Database from "better-sqlite3";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Verify an HMAC-signed unsubscribe token and return the email, or null if invalid.
// Token format: base64url(email) + "." + base64url(hmac_sha256(secret, "unsub:" + email))
function verifyUnsubToken(token: string, secret: string): string | null {
  if (!token || !secret) return null;
  const parts = token.split(".");
  if (parts.length !== 2) return null;
  try {
    const emailBytes = Buffer.from(parts[0], "base64url");
    const email = emailBytes.toString("utf8").toLowerCase().trim();
    const expectedSig = crypto.createHmac("sha256", secret)
      .update(`unsub:${email}`)
      .digest();
    const actualSig = Buffer.from(parts[1], "base64url");
    if (expectedSig.length !== actualSig.length) return null;
    if (!crypto.timingSafeEqual(expectedSig, actualSig)) return null;
    return email;
  } catch {
    return null;
  }
}

async function startServer() {
  const app = express();
  const server = createServer(app);

  const staticPath =
    process.env.NODE_ENV === "production"
      ? path.resolve(__dirname, "public")
      : path.resolve(__dirname, "..", "dist", "public");

  app.use(express.json());
  app.use(express.static(staticPath));

  // Health check
  app.get("/api/health", (_req, res) => {
    res.json({ ok: true, service: "een-construction-api", ts: new Date().toISOString() });
  });

  // Contact form endpoint
  app.post("/api/contact", (req, res) => {
    const { name, email, phone, unitCount, address, workNeeded, preferredContact } = req.body as {
      name?: string; email?: string; phone?: string; unitCount?: string;
      address?: string; workNeeded?: string; preferredContact?: string;
    };
    if (!name || !email || !unitCount || !address || !workNeeded) {
      return res.status(400).json({ error: "Missing required fields" });
    }
    console.log("[Contact Form Submission]", {
      name, email, phone, unitCount, address, workNeeded, preferredContact,
      receivedAt: new Date().toISOString(),
    });
    return res.status(200).json({ ok: true });
  });

  // Unsubscribe endpoint — verifies HMAC token and writes suppression to SQLite
  app.post("/api/unsubscribe", (req, res) => {
    const { token } = req.body as { token?: string };
    if (!token || typeof token !== "string" || token.length > 500) {
      return res.status(400).json({ error: "Invalid token" });
    }

    const secret = process.env.UNSUBSCRIBE_SECRET ?? "";
    const email = verifyUnsubToken(token, secret);
    if (!email) {
      return res.status(400).json({ error: "Token verification failed" });
    }

    const dbPath = process.env.OUTREACH_DB_PATH
      ?? path.resolve(__dirname, "..", "..", "outreach", "data", "outreach.db");

    let db: InstanceType<typeof Database> | null = null;
    try {
      db = new Database(dbPath, { readonly: false });
      const domain = email.split("@")[1] ?? null;

      db.prepare(`
        INSERT OR IGNORE INTO suppression_list (email, domain, reason, notes, added_at, permanent)
        VALUES (?, ?, 'unsubscribe', 'Unsubscribed via email link', datetime('now'), 1)
      `).run(email, domain);

      db.prepare("UPDATE contacts SET do_not_contact = 1 WHERE lower(email) = ?").run(email);

      db.prepare(`
        UPDATE email_campaigns SET status = 'suppressed'
        WHERE contact_id IN (SELECT id FROM contacts WHERE lower(email) = ?)
        AND status IN ('draft', 'queued')
      `).run(email);

      console.log(`[Unsubscribe] Suppressed: ${email}`);
      return res.status(200).json({ ok: true });
    } catch (err) {
      console.error("[Unsubscribe] Error:", err);
      return res.status(500).json({ error: "Server error" });
    } finally {
      db?.close();
    }
  });

  // Client-side routing catch-all
  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticPath, "index.html"));
  });

  const port = process.env.PORT || 3000;
  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

startServer().catch(console.error);
