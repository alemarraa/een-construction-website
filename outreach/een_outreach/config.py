"""Central configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Mode ─────────────────────────────────────────────────────────────
    dry_run: bool = True
    send_enabled: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = f"sqlite:///{_ROOT}/outreach.db"

    # ── Sender identity ───────────────────────────────────────────────────
    sender_name: str = ""
    business_name: str = "EEN Construction"
    business_email: str = ""
    business_phone: str = ""
    business_website: str = ""
    physical_mailing_address: str = ""
    # Base URL for the website hosting the unsubscribe endpoint (e.g. https://eenconstruction.com)
    # Per-email links are built as: {unsubscribe_url}/unsubscribe?t={hmac_token}
    unsubscribe_url: str = ""
    # Secret for HMAC-signed unsubscribe tokens — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
    unsubscribe_secret: str = ""

    # ── Upstash Redis (suppression sync for deployed unsubscribe endpoint) ──
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    # ── Email provider ────────────────────────────────────────────────────
    email_provider: Literal["resend", "sendgrid", "postmark", "smtp"] = "resend"
    # from_email: verified sending address (must match a domain verified in Resend)
    # Falls back to business_email if unset.
    from_email: str = ""
    resend_api_key: str = ""
    resend_webhook_secret: str = ""
    sendgrid_api_key: str = ""
    postmark_server_token: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # ── Enrichment ────────────────────────────────────────────────────────
    hunter_api_key: str = ""
    apollo_api_key: str = ""
    pdl_api_key: str = ""

    # ── Email verification ────────────────────────────────────────────────
    zerobounce_api_key: str = ""
    neverbounce_api_key: str = ""

    # ── Sending limits ────────────────────────────────────────────────────
    max_emails_per_day: int = 20
    max_emails_per_hour: int = 5
    max_per_company: int = 2
    min_lead_score: int = 40
    min_email_confidence: float = 0.7
    reintro_cooldown_days: int = 120
    max_followups: int = 2
    bounce_rate_stop: float = 0.03
    complaint_rate_stop: float = 0.001

    # ── Data sources ──────────────────────────────────────────────────────
    montgomery_dataset_id: str = "et5s-xste"
    socrata_app_token: str = ""

    # ── Derived ───────────────────────────────────────────────────────────
    @property
    def sender_identity_complete(self) -> bool:
        required = [
            self.sender_name,
            self.business_email,
            self.business_phone,
            self.physical_mailing_address,
            self.unsubscribe_url,
        ]
        return all(required)

    @property
    def email_provider_key(self) -> str:
        mapping = {
            "resend": self.resend_api_key,
            "sendgrid": self.sendgrid_api_key,
            "postmark": self.postmark_server_token,
            "smtp": self.smtp_host,
        }
        return mapping.get(self.email_provider, "")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """For testing only."""
    global _settings
    _settings = None
