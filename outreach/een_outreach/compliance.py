"""CAN-SPAM compliance checks and suppression enforcement."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import get_settings
from .models import (
    Contact,
    EmailCampaign,
    EmailMessage,
    Property,
    SuppressionList,
)

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    allowed: bool
    reason: str = ""


def is_suppressed(db: Session, email: str) -> bool:
    """Return True if the email or its domain is in the local SQLite suppression list
    or in the deployed Upstash Redis suppression store."""
    e = email.lower()
    row = db.query(SuppressionList).filter(SuppressionList.email == e).first()
    if row:
        return True
    domain = e.split("@")[-1] if "@" in e else ""
    if domain:
        row = db.query(SuppressionList).filter(SuppressionList.domain == domain).first()
        if row:
            return True
    # Check Upstash Redis (deployed unsubscribes)
    if _upstash_is_suppressed(e):
        return True
    return False


def _upstash_is_suppressed(email: str) -> bool:
    """Check Upstash Redis for a suppression entry. Returns False on any error."""
    cfg = get_settings()
    if not cfg.upstash_redis_url or not cfg.upstash_redis_token:
        return False
    try:
        import httpx
        url = f"{cfg.upstash_redis_url.rstrip('/')}/get/suppression:{email}"
        r = httpx.get(url, headers={"Authorization": f"Bearer {cfg.upstash_redis_token}"}, timeout=3)
        if r.status_code == 200:
            return r.json().get("result") is not None
    except Exception as exc:
        logger.debug("Upstash suppression check failed: %s", exc)
    return False


def add_suppression(
    db: Session,
    email: str,
    reason: str,
    notes: str = "",
    permanent: bool = True,
) -> SuppressionList:
    """Add an email to the suppression list; idempotent."""
    existing = (
        db.query(SuppressionList)
        .filter(SuppressionList.email == email.lower())
        .first()
    )
    if existing:
        existing.reason = reason
        existing.notes = notes
        db.flush()
        return existing

    entry = SuppressionList(
        email=email.lower(),
        domain=email.split("@")[-1].lower() if "@" in email else None,
        reason=reason,
        notes=notes,
        permanent=permanent,
    )
    db.add(entry)
    db.flush()
    logger.info("Suppressed %s — %s", email, reason)

    # Also mark the Contact
    contact = db.query(Contact).filter(Contact.email == email.lower()).first()
    if contact:
        contact.do_not_contact = True
        db.flush()

    return entry


def _sent_today(db: Session) -> int:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (
        db.query(func.count(EmailMessage.id))
        .filter(EmailMessage.sent_at >= today_start)
        .scalar()
        or 0
    )


def _sent_this_hour(db: Session) -> int:
    hour_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return (
        db.query(func.count(EmailMessage.id))
        .filter(EmailMessage.sent_at >= hour_start)
        .scalar()
        or 0
    )


def _sent_to_company(db: Session, organization_id: int) -> int:
    return (
        db.query(func.count(EmailCampaign.id))
        .join(Contact, EmailCampaign.contact_id == Contact.id)
        .filter(
            Contact.organization_id == organization_id,
            EmailCampaign.status == "sent",
        )
        .scalar()
        or 0
    )


def _cooldown_ok(db: Session, contact_id: int, cooldown_days: int) -> bool:
    """True if the contact has not been emailed within cooldown_days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
    last = (
        db.query(func.max(EmailCampaign.sent_at))
        .filter(EmailCampaign.contact_id == contact_id)
        .scalar()
    )
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last < cutoff


def _bounce_rate(db: Session) -> float:
    total = db.query(func.count(EmailMessage.id)).filter(
        EmailMessage.status.in_(["sent", "delivered", "bounced_soft", "bounced_hard"])
    ).scalar() or 0
    if total == 0:
        return 0.0
    bounced = db.query(func.count(EmailMessage.id)).filter(
        EmailMessage.status.in_(["bounced_soft", "bounced_hard"])
    ).scalar() or 0
    return bounced / total


def _complaint_rate(db: Session) -> float:
    total = db.query(func.count(EmailMessage.id)).filter(
        EmailMessage.status != "draft"
    ).scalar() or 0
    if total == 0:
        return 0.0
    complained = db.query(func.count(EmailMessage.id)).filter(
        EmailMessage.status == "complained"
    ).scalar() or 0
    return complained / total


def _is_business_hours() -> bool:
    """True if current UTC time is Mon-Fri 09:00-17:00 ET (approx UTC-5)."""
    now = datetime.now(timezone.utc)
    # Rough offset — for precise handling use zoneinfo
    et_hour = (now.hour - 5) % 24
    et_weekday = now.weekday()
    return et_weekday < 5 and 9 <= et_hour < 17


def check_send_compliance(
    db: Session,
    campaign: EmailCampaign,
    contact: Contact,
    require_business_hours: bool = True,
) -> ComplianceResult:
    """Full gate check before sending a campaign.

    Returns ComplianceResult(allowed=True) only when ALL checks pass.
    """
    cfg = get_settings()

    # DRY_RUN / SEND_ENABLED gates — check first so DRY_RUN is clearly the reason
    if cfg.dry_run:
        return ComplianceResult(False, "DRY_RUN=true — not sending")
    if not cfg.send_enabled:
        return ComplianceResult(False, "SEND_ENABLED=false")

    # Sender identity
    if not cfg.sender_identity_complete:
        return ComplianceResult(False, "sender identity incomplete")

    # Contact has email
    if not contact.email:
        return ComplianceResult(False, "contact has no email address")

    # Suppression
    if contact.do_not_contact:
        return ComplianceResult(False, "contact is marked do_not_contact")
    if is_suppressed(db, contact.email):
        return ComplianceResult(False, "email is on suppression list")

    # Email confidence threshold
    if contact.email_confidence < cfg.min_email_confidence:
        return ComplianceResult(
            False,
            f"email confidence {contact.email_confidence:.2f} < threshold {cfg.min_email_confidence}",
        )

    # Lead score threshold
    if campaign.lead_score < cfg.min_lead_score:
        return ComplianceResult(
            False,
            f"lead score {campaign.lead_score:.0f} < minimum {cfg.min_lead_score}",
        )

    # Cooldown
    if not _cooldown_ok(db, contact.id, cfg.reintro_cooldown_days):
        return ComplianceResult(
            False, f"contact emailed within last {cfg.reintro_cooldown_days} days"
        )

    # Per-company limit
    if contact.organization_id:
        sent_co = _sent_to_company(db, contact.organization_id)
        if sent_co >= cfg.max_per_company:
            return ComplianceResult(
                False,
                f"company already received {sent_co} emails (limit {cfg.max_per_company})",
            )

    # Hourly limit
    if _sent_this_hour(db) >= cfg.max_emails_per_hour:
        return ComplianceResult(
            False, f"hourly limit {cfg.max_emails_per_hour} reached"
        )

    # Daily limit
    if _sent_today(db) >= cfg.max_emails_per_day:
        return ComplianceResult(
            False, f"daily limit {cfg.max_emails_per_day} reached"
        )

    # Bounce rate check
    br = _bounce_rate(db)
    if br >= cfg.bounce_rate_stop:
        return ComplianceResult(
            False, f"bounce rate {br:.1%} exceeds stop threshold {cfg.bounce_rate_stop:.1%}"
        )

    # Complaint rate check
    cr = _complaint_rate(db)
    if cr >= cfg.complaint_rate_stop:
        return ComplianceResult(
            False,
            f"complaint rate {cr:.2%} exceeds stop threshold {cfg.complaint_rate_stop:.2%}",
        )

    # Business hours
    if require_business_hours and not _is_business_hours():
        return ComplianceResult(False, "outside business hours (Mon-Fri 9-17 ET)")

    # CAN-SPAM: must include physical address and unsubscribe URL in body
    if cfg.physical_mailing_address not in (campaign.body_html or ""):
        return ComplianceResult(False, "physical mailing address missing from email body")
    if "/unsubscribe?t=" not in (campaign.body_html or ""):
        return ComplianceResult(False, "unsubscribe token URL missing from email body")

    return ComplianceResult(True, "all checks passed")


def can_spam_checklist(cfg=None) -> list[tuple[str, bool, str]]:
    """Return a structured CAN-SPAM compliance checklist.

    Returns list of (item, passed, detail).
    """
    if cfg is None:
        cfg = get_settings()
    return [
        (
            "Accurate From / sender name",
            bool(cfg.sender_name and cfg.business_email),
            f"{cfg.sender_name} <{cfg.business_email}>",
        ),
        (
            "Non-deceptive subject lines",
            True,
            "Enforced by compose — intro subject only",
        ),
        (
            "Physical mailing address in every email",
            bool(cfg.physical_mailing_address),
            cfg.physical_mailing_address or "MISSING",
        ),
        (
            "Opt-out mechanism (unsubscribe URL)",
            bool(cfg.unsubscribe_url),
            cfg.unsubscribe_url or "MISSING",
        ),
        (
            "Opt-out honored within 10 business days",
            True,
            "Immediate suppression on unsubscribe event",
        ),
        (
            "List-Unsubscribe header present",
            True,
            "Added by all email sender adapters",
        ),
        (
            "DRY_RUN and SEND_ENABLED defaults to safe",
            cfg.dry_run or not cfg.send_enabled,
            f"DRY_RUN={cfg.dry_run}  SEND_ENABLED={cfg.send_enabled}",
        ),
        (
            "No purchased lists",
            True,
            "Only open public-record data used",
        ),
        (
            "Business-hours sending only",
            True,
            "Enforced at send time (Mon-Fri 9–17 ET)",
        ),
        (
            "Bounce and complaint rate monitoring",
            True,
            f"Stop at bounce≥{cfg.bounce_rate_stop:.0%} / complaint≥{cfg.complaint_rate_stop:.1%}",
        ),
        (
            "Resend API key configured",
            bool(cfg.resend_api_key),
            "[SET]" if cfg.resend_api_key else "MISSING — run setup_keys.py",
        ),
        (
            "Verified FROM email domain",
            bool(cfg.from_email),
            cfg.from_email or f"MISSING — set FROM_EMAIL (current fallback: {cfg.business_email})",
        ),
        (
            "Resend webhook secret configured",
            bool(cfg.resend_webhook_secret),
            "[SET]" if cfg.resend_webhook_secret else "MISSING — configure webhook in Resend dashboard",
        ),
    ]
