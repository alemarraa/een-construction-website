"""Tests for compliance checks and suppression enforcement."""

from __future__ import annotations

import os

import pytest

from een_outreach.compliance import (
    add_suppression,
    can_spam_checklist,
    check_send_compliance,
    is_suppressed,
)
from een_outreach.models import Contact, EmailCampaign, Organization, Property
from een_outreach.pipeline.normalize import normalize_address


def _make_contact(db, email="test@example.com", role="property_manager"):
    org = Organization(name="Test Co", normalized_name="test co")
    db.add(org)
    db.flush()
    contact = Contact(
        first_name="Jane",
        last_name="Doe",
        full_name="Jane Doe",
        role=role,
        organization_id=org.id,
        email=email,
        email_status="verified",
        email_confidence=0.95,
    )
    db.add(contact)
    db.flush()
    return contact


def _make_property(db, score=75.0):
    prop = Property(
        street_address="100 Main St",
        county="montgomery",
        normalized_address=normalize_address("100 Main St"),
        unit_count=20,
        data_confidence=0.8,
        qualifies=True,
        lead_score=score,
    )
    db.add(prop)
    db.flush()
    return prop


def _make_campaign(db, prop, contact, body_html="<p>addr</p>"):
    from een_outreach.config import get_settings
    cfg = get_settings()
    # Embed required CAN-SPAM elements
    body_html = (
        f"<p>{cfg.physical_mailing_address or '123 Business St'}</p>"
        f"<a href='{cfg.unsubscribe_url or 'http://unsub.example.com'}'>unsub</a>"
    )
    campaign = EmailCampaign(
        property_id=prop.id,
        contact_id=contact.id,
        status="draft",
        lead_score=prop.lead_score,
        body_html=body_html,
        body_text="plain text",
        dry_run=True,
    )
    db.add(campaign)
    db.flush()
    return campaign


# ── Suppression tests ──────────────────────────────────────────────────────


def test_add_and_check_suppression(db):
    add_suppression(db, "bad@example.com", reason="unsubscribe")
    assert is_suppressed(db, "bad@example.com")


def test_suppression_idempotent(db):
    add_suppression(db, "bad@example.com", reason="unsubscribe")
    add_suppression(db, "bad@example.com", reason="bounce_hard")
    # Should not raise; only one row
    from een_outreach.models import SuppressionList
    count = db.query(SuppressionList).filter(SuppressionList.email == "bad@example.com").count()
    assert count == 1


def test_suppression_marks_contact_do_not_contact(db):
    contact = _make_contact(db, "mark@example.com")
    add_suppression(db, "mark@example.com", reason="unsubscribe")
    db.refresh(contact)
    assert contact.do_not_contact is True


def test_not_suppressed(db):
    assert not is_suppressed(db, "clean@example.com")


# ── Compliance gate tests ──────────────────────────────────────────────────


def test_dry_run_blocks_send(db, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("SEND_ENABLED", "false")
    from een_outreach.config import reset_settings
    reset_settings()

    contact = _make_contact(db)
    prop = _make_property(db)
    campaign = _make_campaign(db, prop, contact)

    result = check_send_compliance(db, campaign, contact, require_business_hours=False)
    assert not result.allowed
    assert "DRY_RUN" in result.reason


def test_low_confidence_blocks_send(db, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("SEND_ENABLED", "true")
    monkeypatch.setenv("SENDER_NAME", "Test Sender")
    monkeypatch.setenv("BUSINESS_EMAIL", "sender@example.com")
    monkeypatch.setenv("BUSINESS_PHONE", "555-0100")
    monkeypatch.setenv("PHYSICAL_MAILING_ADDRESS", "123 Business St, City MD 20001")
    monkeypatch.setenv("UNSUBSCRIBE_URL", "http://unsub.example.com")
    from een_outreach.config import reset_settings
    reset_settings()

    contact = _make_contact(db)
    contact.email_confidence = 0.3  # below threshold
    prop = _make_property(db)
    campaign = _make_campaign(db, prop, contact)

    result = check_send_compliance(db, campaign, contact, require_business_hours=False)
    assert not result.allowed
    assert "confidence" in result.reason


def test_suppressed_contact_blocked(db, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("SEND_ENABLED", "true")
    monkeypatch.setenv("SENDER_NAME", "Test Sender")
    monkeypatch.setenv("BUSINESS_EMAIL", "sender@example.com")
    monkeypatch.setenv("BUSINESS_PHONE", "555-0100")
    monkeypatch.setenv("PHYSICAL_MAILING_ADDRESS", "123 Business St, City MD 20001")
    monkeypatch.setenv("UNSUBSCRIBE_URL", "http://unsub.example.com")
    from een_outreach.config import reset_settings
    reset_settings()

    contact = _make_contact(db, "suppressed@example.com")
    add_suppression(db, "suppressed@example.com", reason="unsubscribe")
    db.refresh(contact)
    prop = _make_property(db)
    campaign = _make_campaign(db, prop, contact)

    result = check_send_compliance(db, campaign, contact, require_business_hours=False)
    assert not result.allowed
    assert "do_not_contact" in result.reason or "suppression" in result.reason


# ── CAN-SPAM checklist ─────────────────────────────────────────────────────


def test_can_spam_checklist_structure():
    items = can_spam_checklist()
    assert len(items) >= 8
    for item, passed, detail in items:
        assert isinstance(item, str)
        assert isinstance(passed, bool)
        assert isinstance(detail, str)
