"""Send queued email campaigns with rate limiting, business-hours and DRY_RUN guard."""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..compliance import check_send_compliance
from ..config import get_settings
from ..email_sender.resend import get_sender
from ..models import (
    AuditLog,
    Contact,
    EmailCampaign,
    EmailMessage,
    Property,
)

logger = logging.getLogger(__name__)


@dataclass
class SendSummary:
    sent: int = 0
    skipped: int = 0
    dry_run: int = 0
    errors: int = 0
    skip_reasons: dict[str, int] = field(default_factory=dict)

    def record_skip(self, reason: str) -> None:
        self.skipped += 1
        self.skip_reasons[reason] = self.skip_reasons.get(reason, 0) + 1

    def as_csv(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["outcome", "count"])
        w.writerow(["sent", self.sent])
        w.writerow(["dry_run_drafted", self.dry_run])
        w.writerow(["skipped", self.skipped])
        w.writerow(["errors", self.errors])
        if self.skip_reasons:
            w.writerow([])
            w.writerow(["skip_reason", "count"])
            for reason, count in sorted(self.skip_reasons.items()):
                w.writerow([reason, count])
        return buf.getvalue()


def _send_one(
    db: Session,
    campaign: EmailCampaign,
    contact: Contact,
    require_business_hours: bool,
    summary: SendSummary,
) -> None:
    cfg = get_settings()

    compliance = check_send_compliance(
        db, campaign, contact, require_business_hours=require_business_hours
    )

    if not compliance.allowed:
        if compliance.reason.startswith("DRY_RUN"):
            summary.dry_run += 1
            campaign.status = "draft"
            logger.info("[DRY_RUN] campaign %d: %s", campaign.id, compliance.reason)
        else:
            summary.record_skip(compliance.reason)
            campaign.status = "suppressed"
            campaign.skip_reason = compliance.reason
            logger.info("Skipping campaign %d: %s", campaign.id, compliance.reason)
        db.flush()
        return

    sender = get_sender()
    if not sender.is_configured():
        summary.record_skip("email provider not configured")
        campaign.skip_reason = "email provider not configured"
        db.flush()
        return

    result = sender.send(
        to_email=contact.email,
        to_name=contact.full_name,
        subject=campaign.subject,
        body_html=campaign.body_html or "",
        body_text=campaign.body_text or "",
        from_email=cfg.business_email,
        from_name=cfg.sender_name,
        reply_to=cfg.business_email,
        unsubscribe_url=cfg.unsubscribe_url,
    )

    now = datetime.now(timezone.utc)
    msg = EmailMessage(
        campaign_id=campaign.id,
        provider_message_id=result.provider_message_id,
        status="sent" if result.success else "bounced_soft",
        sent_at=now if result.success else None,
    )
    db.add(msg)

    if result.success:
        campaign.status = "sent"
        campaign.sent_at = now
        summary.sent += 1
        logger.info("Sent campaign %d to %s", campaign.id, contact.email)
    else:
        campaign.status = "draft"
        campaign.skip_reason = result.error
        summary.errors += 1
        logger.error("Failed campaign %d: %s", campaign.id, result.error)

    db.add(
        AuditLog(
            entity_type="email_campaign",
            entity_id=campaign.id,
            action="send_attempt",
            detail=f"provider={result.provider} success={result.success} reason={result.error}",
        )
    )
    db.flush()


def send_queued(
    db: Session,
    limit: int | None = None,
    require_business_hours: bool = True,
) -> SendSummary:
    """Send all 'draft' campaigns that pass compliance checks.

    In DRY_RUN mode, campaigns are evaluated but nothing is transmitted.
    """
    summary = SendSummary()

    query = (
        db.query(EmailCampaign)
        .join(Contact, EmailCampaign.contact_id == Contact.id)
        .filter(
            EmailCampaign.status == "draft",
            Contact.do_not_contact.is_(False),
        )
        .order_by(EmailCampaign.lead_score.desc())
    )
    if limit:
        query = query.limit(limit)

    campaigns = query.all()

    for campaign in campaigns:
        contact = campaign.contact
        _send_one(db, campaign, contact, require_business_hours, summary)

    db.commit()
    return summary
