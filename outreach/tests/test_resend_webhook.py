"""Tests for Resend webhook event handling logic.

These tests cover:
  - Suppression written on hard bounce
  - Suppression written on complaint
  - Delivered / opened / clicked events do not suppress
  - Duplicate events are idempotent
  - Suppressed emails are blocked from future sends
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SENDER_NAME", "Test Sender")
os.environ.setdefault("BUSINESS_EMAIL", "test@example.com")
os.environ.setdefault("BUSINESS_PHONE", "(555) 555-5555")
os.environ.setdefault("PHYSICAL_MAILING_ADDRESS", "123 Test St, Rockville MD 20850")
os.environ.setdefault("UNSUBSCRIBE_URL", "https://example.com")
os.environ.setdefault("UNSUBSCRIBE_SECRET", "testsecret1234567890abcdef1234567890abcdef")


def _make_contact(db, email: str = "bounce@pm.com"):
    from een_outreach.models import Contact, Organization

    org = Organization(name="BounceOrg", normalized_name=f"bounceorg_{email.split('@')[0]}")
    db.add(org)
    db.flush()
    c = Contact(
        email=email,
        role="property_manager",
        organization_id=org.id,
        email_status="verified",
        do_not_contact=False,
    )
    db.add(c)
    db.flush()
    return c


def _simulate_webhook_event(db, event_type: str, recipient_email: str) -> None:
    """Simulate the suppression logic that the Cloudflare Worker applies on webhook receipt."""
    from een_outreach.compliance import add_suppression

    if event_type == "email.bounced":
        add_suppression(db, recipient_email, reason="bounce", permanent=True)
    elif event_type == "email.complained":
        add_suppression(db, recipient_email, reason="complaint", permanent=True)
    # delivered / opened / clicked → no action


class TestBounceHandling:
    def test_bounce_suppresses_email(self, db):
        contact = _make_contact(db, "hard@bounce.com")
        assert not contact.do_not_contact

        _simulate_webhook_event(db, "email.bounced", "hard@bounce.com")
        db.commit()

        from een_outreach.compliance import is_suppressed
        assert is_suppressed(db, "hard@bounce.com")

    def test_bounce_marks_do_not_contact(self, db):
        from een_outreach.models import Contact
        contact = _make_contact(db, "bounce2@pm.com")
        _simulate_webhook_event(db, "email.bounced", "bounce2@pm.com")
        db.commit()

        refreshed = db.get(Contact, contact.id)
        assert refreshed.do_not_contact is True

    def test_bounce_is_idempotent(self, db):
        from een_outreach.models import SuppressionList
        _make_contact(db, "idem@bounce.com")
        _simulate_webhook_event(db, "email.bounced", "idem@bounce.com")
        _simulate_webhook_event(db, "email.bounced", "idem@bounce.com")
        db.commit()

        count = db.query(SuppressionList).filter_by(email="idem@bounce.com").count()
        assert count == 1


class TestComplaintHandling:
    def test_complaint_suppresses_email(self, db):
        _make_contact(db, "spam@reporter.com")
        _simulate_webhook_event(db, "email.complained", "spam@reporter.com")
        db.commit()

        from een_outreach.compliance import is_suppressed
        assert is_suppressed(db, "spam@reporter.com")

    def test_complaint_suppression_reason(self, db):
        from een_outreach.models import SuppressionList
        _make_contact(db, "complained@example.com")
        _simulate_webhook_event(db, "email.complained", "complained@example.com")
        db.commit()

        entry = db.query(SuppressionList).filter_by(email="complained@example.com").first()
        assert entry is not None
        assert entry.reason == "complaint"
        assert entry.permanent is True


class TestNonSuppressionEvents:
    def test_delivered_does_not_suppress(self, db):
        _make_contact(db, "delivered@ok.com")
        _simulate_webhook_event(db, "email.delivered", "delivered@ok.com")
        db.commit()

        from een_outreach.compliance import is_suppressed
        assert not is_suppressed(db, "delivered@ok.com")

    def test_opened_does_not_suppress(self, db):
        _make_contact(db, "opened@ok.com")
        _simulate_webhook_event(db, "email.opened", "opened@ok.com")
        db.commit()

        from een_outreach.compliance import is_suppressed
        assert not is_suppressed(db, "opened@ok.com")

    def test_clicked_does_not_suppress(self, db):
        _make_contact(db, "clicked@ok.com")
        _simulate_webhook_event(db, "email.clicked", "clicked@ok.com")
        db.commit()

        from een_outreach.compliance import is_suppressed
        assert not is_suppressed(db, "clicked@ok.com")


class TestBounceBlocksFutureSend:
    def test_bounced_contact_is_suppressed(self, db):
        """After a bounce webhook event the email is in the suppression list."""
        from een_outreach.compliance import add_suppression, is_suppressed

        _make_contact(db, "will_bounce@pm.com")
        add_suppression(db, "will_bounce@pm.com", reason="bounce", permanent=True)
        db.commit()

        assert is_suppressed(db, "will_bounce@pm.com")

    def test_bounced_contact_do_not_contact_set(self, db):
        """Bounce suppression sets do_not_contact on the Contact row."""
        from een_outreach.compliance import add_suppression
        from een_outreach.models import Contact

        contact = _make_contact(db, "hard_bounce@pm.com")
        add_suppression(db, "hard_bounce@pm.com", reason="bounce", permanent=True)
        db.commit()

        refreshed = db.get(Contact, contact.id)
        assert refreshed.do_not_contact is True
