import { useEffect, useState } from "react"

type State = "idle" | "loading" | "success" | "already" | "invalid" | "error"

function getToken(): string | null {
  const params = new URLSearchParams(window.location.search)
  const t = params.get("t")
  // Accept HMAC tokens: two base64url segments joined by "."
  if (!t || !/^[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+$/.test(t) || t.length > 500) return null
  return t
}

export default function Unsubscribe() {
  const [state, setState] = useState<State>("idle")
  const token = getToken()

  useEffect(() => {
    if (!token) setState("invalid")
  }, [token])

  async function handleUnsubscribe() {
    if (!token) return
    setState("loading")
    try {
      const res = await fetch("/api/unsubscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      })
      if (res.ok) {
        setState("success")
      } else if (res.status === 404) {
        setState("already")
      } else {
        setState("error")
      }
    } catch {
      setState("error")
    }
  }

  return (
    <div style={{ fontFamily: "Arial, sans-serif", maxWidth: 520, margin: "80px auto", padding: "0 24px", color: "#222" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>Unsubscribe from EEN Construction emails</h1>

      {state === "invalid" && (
        <p style={{ color: "#c00" }}>
          This unsubscribe link is invalid or has expired. Please reply directly to the email you received with the word "unsubscribe" and we will remove you immediately.
        </p>
      )}

      {state === "idle" && token && (
        <>
          <p style={{ marginBottom: 24 }}>
            Click the button below to stop receiving emails from EEN Construction. This takes effect immediately and permanently.
          </p>
          <button
            onClick={handleUnsubscribe}
            style={{
              background: "#1a1a1a", color: "#fff", border: "none",
              padding: "12px 28px", fontSize: 15, cursor: "pointer", borderRadius: 4
            }}
          >
            Confirm Unsubscribe
          </button>
        </>
      )}

      {state === "loading" && (
        <p>Processing your request…</p>
      )}

      {state === "success" && (
        <div style={{ background: "#f0faf0", border: "1px solid #4caf50", borderRadius: 4, padding: "20px 24px" }}>
          <p style={{ margin: 0, fontWeight: 600, color: "#2e7d32" }}>You have been unsubscribed.</p>
          <p style={{ marginTop: 8 }}>We will not contact you again. If you received this email in error, please reply to it and we will clarify.</p>
        </div>
      )}

      {state === "already" && (
        <p>This unsubscribe link has already been used or was not found. If you continue to receive emails, please reply directly with "unsubscribe."</p>
      )}

      {state === "error" && (
        <p style={{ color: "#c00" }}>
          Something went wrong. Please reply directly to the email you received with the word "unsubscribe" and we will remove you immediately.
        </p>
      )}

      <p style={{ marginTop: 40, fontSize: 13, color: "#888" }}>
        EEN Construction · Maryland
      </p>
    </div>
  )
}
