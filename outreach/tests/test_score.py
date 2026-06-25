"""Tests for lead scoring."""

import pytest
from een_outreach.models import Property, Organization, PropertyOrgRelationship, Contact
from een_outreach.pipeline.normalize import normalize_address
from een_outreach.pipeline.score import score_property


def _base_prop(db, unit_count=20, confidence=0.8):
    prop = Property(
        street_address="100 Score St",
        county="montgomery",
        normalized_address=normalize_address("100 Score St"),
        unit_count=unit_count,
        unit_count_confidence=confidence,
        data_confidence=confidence,
        qualifies=True,
    )
    db.add(prop)
    db.flush()
    return prop


def test_score_increases_with_verified_contact(db):
    prop = _base_prop(db)
    org = Organization(name="Test Mgmt", normalized_name="test mgmt")
    db.add(org)
    db.flush()
    rel = PropertyOrgRelationship(
        property_id=prop.id,
        organization_id=org.id,
        relationship_type="manager",
        is_primary=True,
        confidence=0.8,
    )
    db.add(rel)
    contact = Contact(
        organization_id=org.id,
        email="pm@testmgmt.com",
        email_status="verified",
        email_confidence=0.95,
        role="property_manager",
    )
    db.add(contact)
    db.flush()

    score = score_property(prop, db)
    assert score > 50, f"Expected score > 50, got {score}"


def test_score_is_bounded_0_to_100(db):
    prop = _base_prop(db, unit_count=50, confidence=1.0)
    score = score_property(prop, db)
    assert 0 <= score <= 100


def test_score_without_contact_is_lower(db):
    prop_no_contact = _base_prop(db, unit_count=20, confidence=0.8)
    score_no = score_property(prop_no_contact, db)

    prop_with = Property(
        street_address="200 Score St",
        county="montgomery",
        normalized_address=normalize_address("200 Score St"),
        unit_count=20,
        unit_count_confidence=0.8,
        data_confidence=0.8,
        qualifies=True,
    )
    db.add(prop_with)
    db.flush()
    org = Organization(name="Mgmt Co", normalized_name="mgmt co")
    db.add(org)
    db.flush()
    db.add(PropertyOrgRelationship(
        property_id=prop_with.id, organization_id=org.id,
        relationship_type="manager", is_primary=True, confidence=0.8,
    ))
    db.add(Contact(
        organization_id=org.id, email="pm@mgmt.com",
        email_status="verified", email_confidence=0.95, role="property_manager",
    ))
    db.flush()
    score_with = score_property(prop_with, db)

    assert score_with > score_no
