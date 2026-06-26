"""Tests for the unsubscribe token flow and suppression."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SENDER_NAME", "Test Sender")
os.environ.setdefault("BUSINESS_EMAIL", "test@example.com")
os.environ.setdefault("BUSINESS_PHONE", "(555) 555-5555")
os.environ.setdefault("PHYSICAL_MAILING_ADDRESS", "123 Test St, Rockville MD 20850")
os.environ.setdefault("UNSUBSCRIBE_URL", "https://example.com")
os.environ.setdefault("UNSUBSCRIBE_SECRET", "testsecret1234567890abcdef1234567890abcdef")


_TEST_SECRET = "testsecret1234567890abcdef1234567890abcdef"


def _make_contact(db, email: str = "pm@testcorp.com"):
    from een_outreach.models import Contact, Organization

    org = Organization(name="TestCorp", normalized_name="testcorp")
    db.add(org)
    db.flush()

    contact = Contact(
        email=email,
        role="property_manager",
        organization_id=org.id,
        email_status="verified",
        do_not_contact=False,
    )
    db.add(contact)
    db.flush()
    return contact


def _make_campaign(db, contact, token: str | None = None):
    from een_outreach.models import EmailCampaign
    from een_outreach.unsub_token import generate_token

    campaign = EmailCampaign(
        contact_id=contact.id,
        status="draft",
        dry_run=True,
        unsubscribe_token=token or generate_token(contact.email or "pm@testcorp.com", _TEST_SECRET),
        body_html="<p>hello</p>",
    )
    db.add(campaign)
    db.flush()
    return campaign


# ── Token generation ──────────────────────────────────────────────────────


def test_compose_generates_hmac_token(db):
    """compose_draft must assign an HMAC-signed unsubscribe_token."""
    from een_outreach.config import reset_settings
    from een_outreach.models import Organization, Property, PropertyOrgRelationship
    from een_outreach.pipeline.compose import compose_draft
    from een_outreach.unsub_token import verify_token

    reset_settings()
    org = Organization(name="CorpA", normalized_name="corpa")
    db.add(org)
    db.flush()

    prop = Property(
        street_address="100 Main St",
        normalized_address="100 MAIN ST, MD",
        county="montgomery",
        unit_count=20,
        lead_score=50.0,
        qualifies=True,
    )
    db.add(prop)
    db.flush()

    rel = PropertyOrgRelationship(
        property_id=prop.id,
        organization_id=org.id,
        relationship_type="manager",
    )
    db.add(rel)
    db.flush()

    contact = _make_contact(db)
    contact.organization_id = org.id
    db.flush()

    campaign = compose_draft(db, prop, contact)

    assert campaign.unsubscribe_token is not None
    # Must match HMAC format: base64url.base64url
    assert "." in campaign.unsubscribe_token
    parts = campaign.unsubscribe_token.split(".")
    assert len(parts) == 2
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for p in parts for c in p)
    # Must be verifiable with the configured secret
    verified = verify_token(campaign.unsubscribe_token, _TEST_SECRET)
    assert verified == "pm@testcorp.com"


def test_two_campaigns_have_different_tokens(db):
    """Each email address gets a distinct HMAC token."""
    from een_outreach.config import reset_settings
    from een_outreach.models import Contact, Organization, Property, PropertyOrgRelationship
    from een_outreach.pipeline.compose import compose_draft

    reset_settings()
    org = Organization(name="CorpB", normalized_name="corpb")
    db.add(org)
    db.flush()

    def _prop(addr, norm):
        p = Property(
            street_address=addr,
            normalized_address=norm,
            county="montgomery",
            unit_count=10,
            lead_score=50.0,
            qualifies=True,
        )
        db.add(p)
        db.flush()
        r = PropertyOrgRelationship(property_id=p.id, organization_id=org.id, relationship_type="manager")
        db.add(r)
        db.flush()
        return p

    contact1 = _make_contact(db, "pm2@testcorp.com")
    contact1.organization_id = org.id
    db.flush()

    contact2 = Contact(email="pm3@testcorp.com", role="generic", organization_id=org.id,
                       email_status="verified", do_not_contact=False)
    db.add(contact2)
    db.flush()

    p1 = _prop("1 Oak St", "1 OAK ST, MD")
    c1 = compose_draft(db, p1, contact1)
    db.commit()

    p2 = _prop("2 Oak St", "2 OAK ST, MD")
    c2 = compose_draft(db, p2, contact2)
    db.commit()

    assert c1.unsubscribe_token != c2.unsubscribe_token


def test_token_url_in_email_body(db):
    """The rendered email body must contain the HMAC token URL fragment."""
    from een_outreach.config import reset_settings
    from een_outreach.models import Organization, Property, PropertyOrgRelationship
    from een_outreach.pipeline.compose import compose_draft

    reset_settings()
    org = Organization(name="CorpC", normalized_name="corpc")
    db.add(org)
    db.flush()

    prop = Property(
        street_address="200 Elm Ave",
        normalized_address="200 ELM AVE, MD",
        county="montgomery",
        unit_count=30,
        lead_score=60.0,
        qualifies=True,
    )
    db.add(prop)
    db.flush()

    rel = PropertyOrgRelationship(property_id=prop.id, organization_id=org.id, relationship_type="manager")
    db.add(rel)
    db.flush()

    contact = _make_contact(db, "pm4@testcorp.com")
    contact.organization_id = org.id
    db.flush()

    campaign = compose_draft(db, prop, contact)

    assert "/unsubscribe?t=" in (campaign.body_html or "")
    assert campaign.unsubscribe_token in (campaign.body_html or "")


# ── Token module unit tests ───────────────────────────────────────────────


def test_generate_and_verify_token():
    """generate_token produces a token that verify_token accepts."""
    from een_outreach.unsub_token import generate_token, verify_token

    email = "owner@example.com"
    token = generate_token(email, _TEST_SECRET)
    assert "." in token
    assert verify_token(token, _TEST_SECRET) == email.lower()


def test_verify_rejects_wrong_secret():
    """verify_token returns None when the secret doesn't match."""
    from een_outreach.unsub_token import generate_token, verify_token

    token = generate_token("owner@example.com", _TEST_SECRET)
    assert verify_token(token, "wrong_secret") is None


def test_verify_rejects_malformed_token():
    """verify_token returns None for garbage input."""
    from een_outreach.unsub_token import verify_token

    assert verify_token("notavalidtoken", _TEST_SECRET) is None
    assert verify_token("", _TEST_SECRET) is None
    assert verify_token("abc.def.ghi", _TEST_SECRET) is None


# ── Suppression via token lookup ──────────────────────────────────────────


def test_suppression_via_token(db):
    """Finding a token in the DB, marking do_not_contact, and adding suppression entry."""
    from een_outreach.compliance import add_suppression
    from een_outreach.models import Contact, EmailCampaign, SuppressionList
    from een_outreach.unsub_token import generate_token

    contact = _make_contact(db)
    token = generate_token(contact.email, _TEST_SECRET)
    campaign = _make_campaign(db, contact, token)
    db.commit()

    # Simulate what the Express endpoint does: look up token → email → suppress
    result = db.query(EmailCampaign).filter_by(unsubscribe_token=token).first()
    assert result is not None

    looked_up_contact = db.get(Contact, result.contact_id)
    assert looked_up_contact.email == "pm@testcorp.com"

    add_suppression(db, looked_up_contact.email, reason="unsubscribe", permanent=True)
    db.commit()

    entry = db.query(SuppressionList).filter_by(email="pm@testcorp.com").first()
    assert entry is not None
    assert entry.reason == "unsubscribe"
    assert entry.permanent is True

    refreshed = db.get(Contact, looked_up_contact.id)
    assert refreshed.do_not_contact is True


def test_unknown_token_returns_none(db):
    """A lookup for a non-existent token returns None."""
    from een_outreach.models import EmailCampaign
    from een_outreach.unsub_token import generate_token

    fake_token = generate_token("nobody@nowhere.com", _TEST_SECRET)
    result = db.query(EmailCampaign).filter_by(unsubscribe_token=fake_token).first()
    assert result is None


def test_unsubscribed_is_suppressed(db):
    """After unsubscribe, is_suppressed() returns True for that email."""
    from een_outreach.compliance import add_suppression, is_suppressed

    contact = _make_contact(db, "pm5@corp.com")
    assert not is_suppressed(db, "pm5@corp.com")

    add_suppression(db, "pm5@corp.com", reason="unsubscribe", permanent=True)
    db.commit()

    assert is_suppressed(db, "pm5@corp.com")
    assert contact.do_not_contact is True
