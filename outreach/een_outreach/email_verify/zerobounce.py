"""ZeroBounce email-verification adapter.

Docs: https://www.zerobounce.net/docs/
"""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from .base import BaseVerifier, VerificationResult

logger = logging.getLogger(__name__)

ZB_BASE = "https://api.zerobounce.net/v2"

STATUS_MAP = {
    "valid": ("verified", 0.95, True),
    "invalid": ("invalid", 0.95, False),
    "catch-all": ("catch_all", 0.6, False),
    "unknown": ("unknown", 0.4, False),
    "spamtrap": ("invalid", 1.0, False),
    "abuse": ("risky", 0.8, False),
    "do_not_mail": ("risky", 0.9, False),
}


class ZeroBounceVerifier(BaseVerifier):
    name = "zerobounce"

    def __init__(self):
        self._api_key = get_settings().zerobounce_api_key

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def verify(self, email: str) -> VerificationResult:
        if not self.is_configured():
            from .base import NullVerifier
            return NullVerifier().verify(email)
        try:
            r = httpx.get(
                f"{ZB_BASE}/validate",
                params={"api_key": self._api_key, "email": email},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPError as exc:
            logger.error("ZeroBounce verify error for %s: %s", email, exc)
            return VerificationResult(
                email=email, status="unknown", confidence=0.3,
                is_sendable=False, reason=str(exc), provider=self.name,
            )

        raw_status = (data.get("status") or "unknown").lower()
        status, confidence, sendable = STATUS_MAP.get(
            raw_status, ("unknown", 0.3, False)
        )
        return VerificationResult(
            email=email,
            status=status,
            confidence=confidence,
            is_sendable=sendable,
            reason=data.get("sub_status") or None,
            provider=self.name,
        )
