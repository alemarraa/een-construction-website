"""Abstract base for email-verification providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VerificationResult:
    email: str
    status: str  # verified | invalid | risky | catch_all | disposable | unknown
    confidence: float  # 0–1
    is_sendable: bool
    reason: str | None = None
    provider: str = ""


class BaseVerifier(ABC):
    name: str = ""

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def verify(self, email: str) -> VerificationResult: ...

    def verify_bulk(self, emails: list[str]) -> list[VerificationResult]:
        return [self.verify(e) for e in emails]


class NullVerifier(BaseVerifier):
    """Fallback when no verifier is configured: mark everything unknown."""

    name = "null"

    def is_configured(self) -> bool:
        return True

    def verify(self, email: str) -> VerificationResult:
        return VerificationResult(
            email=email,
            status="unknown",
            confidence=0.4,
            is_sendable=False,
            reason="No verification provider configured",
            provider=self.name,
        )
