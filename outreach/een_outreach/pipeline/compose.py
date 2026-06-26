"""Email draft composition — renders the Jinja2 template with verified personalisation."""

from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Contact, EmailCampaign, Organization, Property

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_jinja_env: Environment | None = None


def _get_jinja() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "jinja2"]),
        )
    return _jinja_env


def _html_to_text(html_body: str) -> str:
    """Very lightweight HTML → plain-text fallback."""
    # Strip <style> and <head> blocks entirely
    text = re.sub(r"<style[^>]*>.*?</style>", "", html_body, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<head[^>]*>.*?</head>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_personalization_line(prop: Property, org: Organization | None) -> str:
    """One sentence tied to the specific property — no generic filler."""
    city = (prop.city or prop.county.replace("_", " ").title()).title()
    if prop.unit_count and not prop.unit_count_is_estimated:
        n = prop.unit_count
        addr = prop.street_address.title()
        if org and org.name:
            return (
                f"I came across the {n}-unit property at {addr} while looking at "
                f"rental communities in {city} and wanted to reach out about "
                f"supporting your team with turns and maintenance work."
            )
        return (
            f"I came across the {n}-unit building at {addr} and wanted to reach out "
            f"about supporting your team with unit turns and maintenance work in {city}."
        )
    addr = prop.street_address.title()
    return (
        f"I came across the rental property at {addr} in {city} and wanted to "
        f"reach out about supporting your team with turns and maintenance work."
    )


def compose_draft(
    db: Session,
    prop: Property,
    contact: Contact,
    sequence_number: int = 0,
) -> EmailCampaign:
    """Render a draft EmailCampaign for prop × contact.

    Returns the persisted (but unsent) EmailCampaign.
    Raises ValueError if sender identity is incomplete.
    """
    cfg = get_settings()
    if not cfg.sender_identity_complete:
        raise ValueError(
            "Sender identity incomplete — fill SENDER_NAME, BUSINESS_EMAIL, "
            "BUSINESS_PHONE, PHYSICAL_MAILING_ADDRESS, UNSUBSCRIBE_URL in .env"
        )

    org: Organization | None = contact.organization

    first_name = contact.first_name
    personalization_line = _build_personalization_line(prop, org)

    city = (prop.city or prop.county.replace("_", " ").title()).title()
    if prop.unit_count and not prop.unit_count_is_estimated:
        subject = f"Quick question — unit turns and maintenance at {prop.street_address.title()}"
    else:
        subject = f"Quick question — contractor support for your {city} properties"

    from ..unsub_token import generate_token, generate_secret
    secret = cfg.unsubscribe_secret or generate_secret()
    token = generate_token(contact.email or "", secret)
    base = cfg.unsubscribe_url.rstrip("/")
    unsubscribe_token_url = f"{base}/unsubscribe?t={token}"

    template = _get_jinja().get_template("outreach_intro.html.jinja2")
    body_html = template.render(
        first_name=first_name,
        sender_name=cfg.sender_name,
        business_name=cfg.business_name,
        business_email=cfg.business_email,
        business_phone=cfg.business_phone,
        business_website=cfg.business_website,
        physical_mailing_address=cfg.physical_mailing_address,
        unsubscribe_url=unsubscribe_token_url,
        county=prop.county,
        personalization_line=personalization_line,
    )
    body_text = _html_to_text(body_html)

    campaign = EmailCampaign(
        property_id=prop.id,
        contact_id=contact.id,
        status="draft",
        sequence_number=sequence_number,
        lead_score=prop.lead_score,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        personalization_notes=personalization_line,
        dry_run=cfg.dry_run,
        unsubscribe_token=token,
    )
    db.add(campaign)
    db.flush()
    return campaign


def compose_all(
    db: Session,
    min_lead_score: float | None = None,
) -> list[EmailCampaign]:
    """Compose drafts for all qualified properties that don't yet have a draft.

    Returns newly created campaigns.
    """
    cfg = get_settings()
    threshold = min_lead_score if min_lead_score is not None else cfg.min_lead_score

    # Properties that qualify and have no existing campaign yet
    already_campaigned = db.query(EmailCampaign.property_id).distinct()

    props = (
        db.query(Property)
        .filter(Property.qualifies.is_(True), Property.lead_score >= threshold)
        .filter(~Property.id.in_(already_campaigned))
        .all()
    )

    created: list[EmailCampaign] = []
    for prop in props:
        contact = _best_contact_for_property(db, prop)
        if contact is None:
            continue
        campaign = compose_draft(db, prop, contact)
        created.append(campaign)

    db.commit()
    return created


def _best_contact_for_property(db: Session, prop: Property) -> Contact | None:
    """Return highest-priority contact for a property, or None."""
    from ..models import Organization, PropertyOrgRelationship

    role_priority = [
        "property_manager",
        "community_manager",
        "regional_manager",
        "maintenance_supervisor",
        "facilities_manager",
        "operations_manager",
        "asset_manager",
        "owner",
        "generic",
    ]

    org_ids_list = [
        row[0] for row in
        db.query(PropertyOrgRelationship.organization_id)
        .filter(PropertyOrgRelationship.property_id == prop.id)
        .all()
    ]
    if not org_ids_list:
        return None

    contacts = (
        db.query(Contact)
        .filter(
            Contact.organization_id.in_(org_ids_list),
            Contact.do_not_contact.is_(False),
            Contact.email.isnot(None),
            Contact.email_status.in_(["verified", "unknown", "catch_all"]),
        )
        .all()
    )

    if not contacts:
        return None


    def _rank(c: Contact) -> int:
        try:
            return role_priority.index(c.role)
        except ValueError:
            return len(role_priority)

    contacts.sort(key=_rank)
    return contacts[0]
