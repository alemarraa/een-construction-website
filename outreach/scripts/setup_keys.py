#!/usr/bin/env python3
"""Interactive setup script — prompts for API keys and writes them to outreach/.env.

Keys are never printed to the terminal. Run:
    python3 scripts/setup_keys.py
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ENV_FILE = ROOT / ".env"


def _current_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _write_env(env: dict) -> None:
    lines = []
    for k, v in env.items():
        lines.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(lines) + "\n")
    print(f"[OK] .env updated at {ENV_FILE}")


def _prompt_secret(prompt: str, current: str = "") -> str:
    """Prompt for a secret without echoing. Returns current value if user hits Enter."""
    hint = " (press Enter to keep existing)" if current else ""
    value = getpass.getpass(f"{prompt}{hint}: ")
    return value.strip() or current


def _test_hunter(key: str) -> bool:
    try:
        import httpx
        r = httpx.get("https://api.hunter.io/v2/account", params={"api_key": key}, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            print(f"  Hunter.io: plan={data.get('plan_name')}, calls left={data.get('calls', {}).get('left')}")
            return True
        print(f"  Hunter.io: HTTP {r.status_code}")
        return False
    except Exception as e:
        print(f"  Hunter.io: {e}")
        return False


def _test_resend(key: str) -> bool:
    try:
        import httpx
        r = httpx.get("https://api.resend.com/domains", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        if r.status_code == 200:
            domains = r.json().get("data", [])
            print(f"  Resend: authenticated. Verified domains: {[d['name'] for d in domains]}")
            return True
        print(f"  Resend: HTTP {r.status_code} — {r.text[:100]}")
        return False
    except Exception as e:
        print(f"  Resend: {e}")
        return False


def _test_zerobounce(key: str) -> bool:
    try:
        import httpx
        r = httpx.get(f"https://api.zerobounce.net/v2/getcredits?api_key={key}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"  ZeroBounce: credits={data.get('Credits')}")
            return True
        print(f"  ZeroBounce: HTTP {r.status_code}")
        return False
    except Exception as e:
        print(f"  ZeroBounce: {e}")
        return False


def _test_upstash(url: str, token: str) -> bool:
    try:
        import httpx
        r = httpx.post(f"{url}/ping", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code == 200 and "PONG" in r.text:
            print("  Upstash Redis: connected.")
            return True
        print(f"  Upstash Redis: HTTP {r.status_code}")
        return False
    except Exception as e:
        print(f"  Upstash Redis: {e}")
        return False


def main() -> None:
    print("\nEEN Construction Outreach — API Key Setup")
    print("=" * 48)
    print("Keys are written to outreach/.env (git-ignored).")
    print("They are never displayed on screen.\n")

    env = _current_env()

    # 1. Resend (required for sending)
    print("── Resend (required for email delivery) ──")
    print("  Sign up free at https://resend.com (no credit card)")
    print("  After signup: API Keys → Create API Key → copy key")
    key = _prompt_secret("  Resend API key", env.get("RESEND_API_KEY", ""))
    if key:
        env["RESEND_API_KEY"] = key
        print("  Testing…")
        _test_resend(key)

    # 2. Hunter.io (optional but recommended)
    print("\n── Hunter.io (contact discovery — optional) ──")
    print("  Sign up free at https://hunter.io (25 searches/month free)")
    key = _prompt_secret("  Hunter.io API key", env.get("HUNTER_API_KEY", ""))
    if key:
        env["HUNTER_API_KEY"] = key
        print("  Testing…")
        _test_hunter(key)

    # 3. ZeroBounce (optional)
    print("\n── ZeroBounce (email verification — optional) ──")
    print("  Sign up at https://zerobounce.net (100 free credits)")
    key = _prompt_secret("  ZeroBounce API key", env.get("ZEROBOUNCE_API_KEY", ""))
    if key:
        env["ZEROBOUNCE_API_KEY"] = key
        print("  Testing…")
        _test_zerobounce(key)

    # 4. Upstash Redis (for deployed unsubscribe sync)
    print("\n── Upstash Redis (unsubscribe suppression sync — free) ──")
    print("  Sign up free at https://upstash.com (no credit card)")
    print("  Create a Redis DB → copy REST URL and REST Token")
    url = _prompt_secret("  Upstash REST URL", env.get("UPSTASH_REDIS_URL", ""))
    if url:
        env["UPSTASH_REDIS_URL"] = url
        token = _prompt_secret("  Upstash REST Token", env.get("UPSTASH_REDIS_TOKEN", ""))
        if token:
            env["UPSTASH_REDIS_TOKEN"] = token
            print("  Testing…")
            _test_upstash(url, token)

    # 5. Unsubscribe secret
    print("\n── Unsubscribe HMAC secret ──")
    if not env.get("UNSUBSCRIBE_SECRET"):
        import secrets as _s
        generated = _s.token_hex(32)
        env["UNSUBSCRIBE_SECRET"] = generated
        print("  Auto-generated a new secret.")
        print(f"  IMPORTANT: add this same value to your Cloudflare Worker secret:")
        print(f"    cd workers && npx wrangler secret put UNSUBSCRIBE_SECRET")
        print(f"  (the value will be prompted securely there too)")
    else:
        print("  Existing secret kept.")

    # 6. Socrata App Token (free, for PG County data)
    print("\n── Socrata App Token (PG County data — free) ──")
    print("  Create a free account at https://data.maryland.gov")
    print("  Profile → App Tokens → Register a New Application → copy token")
    key = _prompt_secret("  Socrata App Token", env.get("SOCRATA_APP_TOKEN", ""))
    if key:
        env["SOCRATA_APP_TOKEN"] = key

    _write_env(env)
    print("\nSetup complete. Run `een-outreach compliance` to verify all checks pass.")


if __name__ == "__main__":
    main()
