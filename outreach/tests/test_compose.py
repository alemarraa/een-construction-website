"""Tests for email draft composition."""

from __future__ import annotations

import pytest

from een_outreach.models import Contact, EmailCampaign, Organization, Property
from een_outreach.pipeline.normalize import normalize_address


def _setup_env(monkeypatch):
    monkeypatch.setenv("SENDER_NAME", "Alex Smith")
    monkeypatch.setenv("BUSINESS_EMAIL", "alex@eenconstruction.com")
    monkeypatch.setenv("BUSINESS_PHONE", "240-555-0100")
    monkeypatch.setenv("PHYSICAL_MAILING_ADDRESS", "123 Builder Lane, Rockville MD 20850")
    monkeypatch.setenv("UNSUBSCRIBE_URL", "https://eenconstruction.com/unsubscribe")
    monkeypatch.setenv("BUSINESS_WEBSITE", "https://eenconstruction.com")
    from een_outreach.config import reset_settings
    reset_settings()


def _make_property_and_contact(db):
    prop = Property(
        street_address="500 Oak Ave",
        city="Silver Spring",
        county="montgomery",
        normalized_address=normalize_address("500 Oak Ave"),
        unit_count=24,
        unit_count_confidence=0.85,
        data_confidence=0.85,
        qualifies=True,
        lead_score=72.0,
    )
    db.add(prop)
    db.flush()

    org = Organization(name="Silver Spring Realty LLC", normalized_name="silver spring realty")
    db.add(org)
    db.flush()

    from een_outreach.models import PropertyOrgRelationship
    rel = PropertyOrgRelationship(
        property_id=prop.id,
        organization_id=org.id,
        relationship_type="manager",
        is_primary=True,
        confidence=0.8,
    )
    db.add(rel)

    contact = Contact(
        first_name="Maria",
        last_name="Lopez",
        full_name="Maria Lopez",
        role="property_manager",
        organization_id=org.id,
        email="maria@ssrealty.com",
        email_status="verified",
        email_confidence=0.90,
    )
    db.add(contact)
    db.flush()

    return prop, contact


def test_compose_draft_renders_template(db, monkeypatch):
    _setup_env(monkeypatch)
    prop, contact = _make_property_and_contact(db)

    from een_outreach.pipeline.compose import compose_draft
    campaign = compose_draft(db, prop, contact)

    assert campaign.id is not None
    assert campaign.status == "draft"
    assert campaign.body_html
    assert "EEN Construction" in campaign.body_html
    assert "Maria" in campaign.body_html


def test_compose_draft_includes_unsubscribe(db, monkeypatch):
    _setup_env(monkeypatch)
    prop, contact = _make_property_and_contact(db)

    from een_outreach.pipeline.compose import compose_draft
    campaign = compose_draft(db, prop, contact)

    assert "unsubscribe" in campaign.body_html.lower()
    assert "https://eenconstruction.com/unsubscribe" in campaign.body_html


def test_compose_draft_includes_physical_address(db, monkeypatch):
    _setup_env(monkeypatch)
    prop, contact = _make_property_and_contact(db)

    from een_outreach.pipeline.compose import compose_draft
    campaign = compose_draft(db, prop, contact)

    assert "123 Builder Lane" in campaign.body_html


def test_compose_raises_without_sender_identity(db, monkeypatch):
    monkeypatch.setenv("SENDER_NAME", "")
    monkeypatch.setenv("BUSINESS_EMAIL", "")
    from een_outreach.config import reset_settings
    reset_settings()

    prop, contact = _make_property_and_contact(db)

    from een_outreach.pipeline.compose import compose_draft
    with pytest.raises(ValueError, match="Sender identity incomplete"):
        compose_draft(db, prop, contact)


def test_compose_generates_plain_text(db, monkeypatch):
    _setup_env(monkeypatch)
    prop, contact = _make_property_and_contact(db)

    from een_outreach.pipeline.compose import compose_draft
    campaign = compose_draft(db, prop, contact)

    assert campaign.body_text
    assert "<" not in campaign.body_text  # no HTML tags in plaintext
