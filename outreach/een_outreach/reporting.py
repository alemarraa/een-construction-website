"""Dashboard, CSV export, and daily report generation."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.table import Table
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import (
    Contact,
    EmailCampaign,
    EmailMessage,
    Organization,
    Property,
    SuppressionList,
)


@dataclass
class PipelineStats:
    total_properties: int = 0
    qualified_properties: int = 0
    disqualified_properties: int = 0
    organizations: int = 0
    contacts: int = 0
    suppressed: int = 0
    campaigns_draft: int = 0
    campaigns_sent: int = 0
    campaigns_skipped: int = 0
    messages_sent: int = 0
    messages_bounced: int = 0
    messages_complained: int = 0
    messages_replied: int = 0
    avg_lead_score: float = 0.0
    bounce_rate: float = 0.0
    complaint_rate: float = 0.0


def get_pipeline_stats(db: Session) -> PipelineStats:
    s = PipelineStats()

    s.total_properties = db.query(func.count(Property.id)).scalar() or 0
    s.qualified_properties = (
        db.query(func.count(Property.id)).filter(Property.qualifies.is_(True)).scalar() or 0
    )
    s.disqualified_properties = s.total_properties - s.qualified_properties
    s.organizations = db.query(func.count(Organization.id)).scalar() or 0
    s.contacts = db.query(func.count(Contact.id)).scalar() or 0
    s.suppressed = db.query(func.count(SuppressionList.id)).scalar() or 0

    campaign_counts = dict(
        db.query(EmailCampaign.status, func.count(EmailCampaign.id))
        .group_by(EmailCampaign.status)
        .all()
    )
    s.campaigns_draft = campaign_counts.get("draft", 0)
    s.campaigns_sent = campaign_counts.get("sent", 0)
    s.campaigns_skipped = campaign_counts.get("suppressed", 0)

    msg_counts = dict(
        db.query(EmailMessage.status, func.count(EmailMessage.id))
        .group_by(EmailMessage.status)
        .all()
    )
    s.messages_sent = (
        (msg_counts.get("sent", 0) or 0) + (msg_counts.get("delivered", 0) or 0)
    )
    s.messages_bounced = (
        (msg_counts.get("bounced_soft", 0) or 0) + (msg_counts.get("bounced_hard", 0) or 0)
    )
    s.messages_complained = msg_counts.get("complained", 0) or 0
    s.messages_replied = msg_counts.get("replied", 0) or 0

    avg = (
        db.query(func.avg(Property.lead_score))
        .filter(Property.qualifies.is_(True))
        .scalar()
    )
    s.avg_lead_score = float(avg or 0)

    total_msgs = s.messages_sent + s.messages_bounced
    if total_msgs:
        s.bounce_rate = s.messages_bounced / total_msgs
    if s.messages_sent:
        s.complaint_rate = s.messages_complained / s.messages_sent

    return s


def print_dashboard(db: Session, console: Console | None = None) -> None:
    c = console or Console()
    s = get_pipeline_stats(db)

    c.rule("[bold]EEN Construction — Outreach Dashboard[/bold]")

    props = Table(title="Properties", show_header=True)
    props.add_column("Status")
    props.add_column("Count", justify="right")
    props.add_row("Total", str(s.total_properties))
    props.add_row("[green]Qualified[/green]", str(s.qualified_properties))
    props.add_row("[red]Disqualified[/red]", str(s.disqualified_properties))
    props.add_row("Avg lead score", f"{s.avg_lead_score:.1f}")
    c.print(props)

    outreach = Table(title="Outreach", show_header=True)
    outreach.add_column("Metric")
    outreach.add_column("Value", justify="right")
    outreach.add_row("Organizations found", str(s.organizations))
    outreach.add_row("Contacts found", str(s.contacts))
    outreach.add_row("Suppressed addresses", str(s.suppressed))
    outreach.add_row("Campaigns drafted", str(s.campaigns_draft))
    outreach.add_row("Campaigns sent", str(s.campaigns_sent))
    outreach.add_row("Campaigns skipped", str(s.campaigns_skipped))
    outreach.add_row("Messages sent", str(s.messages_sent))
    outreach.add_row("Messages bounced", str(s.messages_bounced))
    outreach.add_row("Messages complained", str(s.messages_complained))
    outreach.add_row("Replies", str(s.messages_replied))
    c.print(outreach)

    health = Table(title="Health", show_header=True)
    health.add_column("Rate")
    health.add_column("Value", justify="right")
    health.add_column("Threshold", justify="right")
    bounce_color = "red" if s.bounce_rate >= 0.03 else "green"
    complaint_color = "red" if s.complaint_rate >= 0.001 else "green"
    health.add_row(
        "Bounce rate",
        f"[{bounce_color}]{s.bounce_rate:.1%}[/{bounce_color}]",
        "3.0%",
    )
    health.add_row(
        "Complaint rate",
        f"[{complaint_color}]{s.complaint_rate:.2%}[/{complaint_color}]",
        "0.1%",
    )
    c.print(health)


def export_qualified_csv(db: Session) -> str:
    """Return CSV of all qualified properties with their contacts."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "property_id", "address", "city", "county", "zip",
        "unit_count", "unit_count_confidence", "lead_score",
        "organization", "contact_name", "contact_role",
        "contact_email", "email_status", "email_confidence",
        "campaign_status",
    ])

    props = (
        db.query(Property)
        .filter(Property.qualifies.is_(True))
        .order_by(Property.lead_score.desc())
        .all()
    )
    for prop in props:
        campaigns = prop.email_campaigns
        campaign_status = campaigns[0].status if campaigns else "no_campaign"

        orgs = [r.organization for r in prop.org_relationships]
        if orgs:
            org_name = orgs[0].name
            contacts = orgs[0].contacts
            contact = contacts[0] if contacts else None
        else:
            org_name = ""
            contact = None

        w.writerow([
            prop.id,
            prop.street_address,
            prop.city or "",
            prop.county,
            prop.zip_code or "",
            prop.unit_count or "",
            f"{prop.unit_count_confidence:.2f}",
            f"{prop.lead_score:.1f}",
            org_name,
            contact.full_name if contact else "",
            contact.role if contact else "",
            contact.email if contact else "",
            contact.email_status if contact else "",
            f"{contact.email_confidence:.2f}" if contact else "",
            campaign_status,
        ])
    return buf.getvalue()


def daily_report_text(db: Session) -> str:
    """Plain-text daily digest for operational review."""
    s = get_pipeline_stats(db)
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    recent_sent = (
        db.query(func.count(EmailMessage.id))
        .filter(EmailMessage.sent_at >= since)
        .scalar()
        or 0
    )

    lines = [
        f"EEN Construction — Outreach Daily Report ({now.strftime('%Y-%m-%d %H:%M UTC')})",
        "=" * 60,
        "",
        f"Properties total:        {s.total_properties}",
        f"Properties qualified:    {s.qualified_properties}",
        f"Avg lead score:          {s.avg_lead_score:.1f}",
        "",
        f"Contacts in DB:          {s.contacts}",
        f"Suppressed addresses:    {s.suppressed}",
        "",
        f"Campaigns sent (all):    {s.campaigns_sent}",
        f"Messages sent (24 h):    {recent_sent}",
        f"Messages bounced:        {s.messages_bounced}",
        f"Bounce rate:             {s.bounce_rate:.1%}",
        f"Complaint rate:          {s.complaint_rate:.2%}",
        f"Replies received:        {s.messages_replied}",
        "",
    ]

    if s.bounce_rate >= 0.03:
        lines.append("⚠  ALERT: bounce rate at or above 3% — sending paused")
    if s.complaint_rate >= 0.001:
        lines.append("⚠  ALERT: complaint rate at or above 0.1% — sending paused")
    if s.bounce_rate < 0.03 and s.complaint_rate < 0.001:
        lines.append("✓  Delivery health is within acceptable limits")

    return "\n".join(lines)
