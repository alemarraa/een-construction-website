"""Abstract base for email-sending providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendResult:
    success: bool
    provider_message_id: str | None = None
    error: str | None = None
    provider: str = ""


class BaseEmailSender(ABC):
    name: str = ""

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def send(
        self,
        to_email: str,
        to_name: str | None,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
        reply_to: str | None = None,
        unsubscribe_url: str | None = None,
        headers: dict | None = None,
    ) -> SendResult: ...
