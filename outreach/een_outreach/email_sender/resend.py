"""Resend email provider adapter.

Docs: https://resend.com/docs/api-reference/emails/send-email
"""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from .base import BaseEmailSender, SendResult

logger = logging.getLogger(__name__)

RESEND_SEND_URL = "https://api.resend.com/emails"


class ResendSender(BaseEmailSender):
    name = "resend"

    def __init__(self):
        self._api_key = get_settings().resend_api_key

    def is_configured(self) -> bool:
        return bool(self._api_key)

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
    ) -> SendResult:
        if not self.is_configured():
            return SendResult(success=False, error="Resend API key not configured")

        to_formatted = f"{to_name} <{to_email}>" if to_name else to_email
        from_formatted = f"{from_name} <{from_email}>"

        payload: dict = {
            "from": from_formatted,
            "to": [to_formatted],
            "subject": subject,
            "html": body_html,
            "text": body_text,
        }
        if reply_to:
            payload["reply_to"] = reply_to

        # CAN-SPAM unsubscribe header
        h = dict(headers or {})
        if unsubscribe_url:
            h["List-Unsubscribe"] = f"<{unsubscribe_url}>"
            h["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        if h:
            payload["headers"] = h

        try:
            r = httpx.post(
                RESEND_SEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            return SendResult(
                success=True,
                provider_message_id=data.get("id"),
                provider=self.name,
            )
        except httpx.HTTPError as exc:
            logger.error("Resend send failed: %s", exc)
            return SendResult(success=False, error=str(exc), provider=self.name)


class SendGridSender(BaseEmailSender):
    """SendGrid adapter — placeholder with full implementation."""

    name = "sendgrid"

    def __init__(self):
        self._api_key = get_settings().sendgrid_api_key

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def send(self, to_email, to_name, subject, body_html, body_text,
             from_email, from_name, reply_to=None, unsubscribe_url=None, headers=None) -> SendResult:
        if not self.is_configured():
            return SendResult(success=False, error="SendGrid API key not configured")

        to_obj = {"email": to_email}
        if to_name:
            to_obj["name"] = to_name

        payload = {
            "personalizations": [{"to": [to_obj]}],
            "from": {"email": from_email, "name": from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": body_text},
                {"type": "text/html", "value": body_html},
            ],
        }
        if reply_to:
            payload["reply_to"] = {"email": reply_to}

        h = {}
        if unsubscribe_url:
            h["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        if h:
            payload["headers"] = h

        try:
            r = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=20,
            )
            r.raise_for_status()
            msg_id = r.headers.get("X-Message-Id")
            return SendResult(success=True, provider_message_id=msg_id, provider=self.name)
        except httpx.HTTPError as exc:
            logger.error("SendGrid send failed: %s", exc)
            return SendResult(success=False, error=str(exc), provider=self.name)


class SMTPSender(BaseEmailSender):
    """Generic SMTP adapter."""

    name = "smtp"

    def __init__(self):
        cfg = get_settings()
        self._host = cfg.smtp_host
        self._port = cfg.smtp_port
        self._user = cfg.smtp_user
        self._password = cfg.smtp_password
        self._from = cfg.smtp_from or cfg.business_email

    def is_configured(self) -> bool:
        return bool(self._host and self._user)

    def send(self, to_email, to_name, subject, body_html, body_text,
             from_email, from_name, reply_to=None, unsubscribe_url=None, headers=None) -> SendResult:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if not self.is_configured():
            return SendResult(success=False, error="SMTP not configured")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
        if reply_to:
            msg["Reply-To"] = reply_to
        if unsubscribe_url:
            msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"

        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(from_email, [to_email], msg.as_string())
            return SendResult(success=True, provider=self.name)
        except Exception as exc:
            logger.error("SMTP send failed: %s", exc)
            return SendResult(success=False, error=str(exc), provider=self.name)


def get_sender(provider: str | None = None) -> BaseEmailSender:
    """Return the appropriate sender based on config."""
    cfg = get_settings()
    p = provider or cfg.email_provider
    if p == "sendgrid":
        return SendGridSender()
    if p == "smtp":
        return SMTPSender()
    return ResendSender()
