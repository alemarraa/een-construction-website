import express from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const server = createServer(app);

  // Serve static files from dist/public in production
  const staticPath =
    process.env.NODE_ENV === "production"
      ? path.resolve(__dirname, "public")
      : path.resolve(__dirname, "..", "dist", "public");

  app.use(express.json());
  app.use(express.static(staticPath));

  // Contact form endpoint
  app.post("/api/contact", (req, res) => {
    const { name, email, phone, unitCount, address, workNeeded, preferredContact } = req.body as {
      name?: string
      email?: string
      phone?: string
      unitCount?: string
      address?: string
      workNeeded?: string
      preferredContact?: string
    }
    if (!name || !email || !unitCount || !address || !workNeeded) {
      return res.status(400).json({ error: "Missing required fields" })
    }
    // Log submission — replace with email/CRM integration as needed
    console.log("[Contact Form Submission]", {
      name, email, phone, unitCount, address, workNeeded, preferredContact,
      receivedAt: new Date().toISOString(),
    })
    return res.status(200).json({ ok: true })
  })

  // Handle client-side routing - serve index.html for all routes
  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticPath, "index.html"));
  });

  const port = process.env.PORT || 3000;

  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

startServer().catch(console.error);
