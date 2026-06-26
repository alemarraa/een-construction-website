"""HMAC-signed unsubscribe token generation and verification.

Token format: base64url(email) + "." + base64url(hmac_sha256(secret, "unsub:" + email))

The email is base64url-encoded (not plaintext in the URL), and the HMAC prevents
forgery. No database lookup is required — the token is self-verifiable.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import re

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+$")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def generate_token(email: str, secret: str) -> str:
    """Return a signed unsubscribe token for the given email address."""
    email_b64 = _b64url(email.lower().strip().encode())
    sig = hmac.new(
        secret.encode(),
        msg=f"unsub:{email.lower().strip()}".encode(),
        digestmod=hashlib.sha256,
    ).digest()
    return f"{email_b64}.{_b64url(sig)}"


def verify_token(token: str, secret: str) -> str | None:
    """Verify a token and return the email address, or None if invalid."""
    if not token or not _TOKEN_RE.match(token):
        return None
    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        email_b64, sig_b64 = parts
        email = _b64url_decode(email_b64).decode()
        expected_sig = hmac.new(
            secret.encode(),
            msg=f"unsub:{email.lower().strip()}".encode(),
            digestmod=hashlib.sha256,
        ).digest()
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        return email.lower().strip()
    except Exception:
        return None


def generate_secret() -> str:
    """Generate a cryptographically strong secret for UNSUBSCRIBE_SECRET."""
    return secrets.token_hex(32)
