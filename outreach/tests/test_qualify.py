"""Tests for the property qualification stage."""

import pytest
from een_outreach.models import Property
from een_outreach.pipeline.qualify import qualify_all
from een_outreach.pipeline.normalize import normalize_address


def _make_property(db, address, county, unit_count, confidence=0.8, estimated=False):
    prop = Property(
        street_address=address,
        county=county,
        normalized_address=normalize_address(address),
        unit_count=unit_count,
        unit_count_is_estimated=estimated,
        unit_count_confidence=confidence,
        data_confidence=confidence,
    )
    db.add(prop)
    db.flush()
    return prop


def test_qualifies_4_units(db):
    _make_property(db, "100 Test St", "montgomery", 4)
    qualified, rejected, review = qualify_all(db)
    assert qualified == 1
    assert rejected == 0


def test_qualifies_100_units(db):
    _make_property(db, "200 Test St", "montgomery", 100)
    qualified, rejected, review = qualify_all(db)
    assert qualified == 1


def test_rejects_3_units(db):
    _make_property(db, "300 Test St", "montgomery", 3)
    qualified, rejected, review = qualify_all(db)
    assert rejected == 1
    assert qualified == 0


def test_rejects_101_units(db):
    _make_property(db, "400 Test St", "montgomery", 101)
    qualified, rejected, review = qualify_all(db)
    assert rejected == 1


def test_needs_review_when_low_confidence_estimated(db):
    _make_property(db, "500 Test St", "montgomery", 50, confidence=0.3, estimated=True)
    qualified, rejected, review = qualify_all(db)
    assert review == 1


def test_mixed_portfolio(db):
    _make_property(db, "1 Good St", "montgomery", 10)
    _make_property(db, "2 Too Small St", "montgomery", 2)
    _make_property(db, "3 Too Large St", "montgomery", 150)
    qualified, rejected, review = qualify_all(db)
    assert qualified == 1
    assert rejected == 2
