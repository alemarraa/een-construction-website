"""Tests for data source adapters and filtering logic."""

from __future__ import annotations

import pytest
from een_outreach.sources.montgomery import MULTIFAMILY_TYPES, MontgomeryHousingSource
from een_outreach.sources.base import RawProperty


MULTIFAMILY_KEYS = list(MULTIFAMILY_TYPES.keys())
NON_MULTIFAMILY_STRINGS = [
    "Single Family",
    "Duplex",
    "Commercial",
    "Condominium",
]


def test_multifamily_type_keys_present():
    assert "Garden Apartment - Multifamily with 1-4 stories" in MULTIFAMILY_TYPES
    assert "Highrise - Multifamily with 9+ stories" in MULTIFAMILY_TYPES
    assert "Quadraplex - Single Family with 4 floors or units" in MULTIFAMILY_TYPES


def test_non_multifamily_not_in_map():
    for t in NON_MULTIFAMILY_STRINGS:
        assert t not in MULTIFAMILY_TYPES, f"Expected {t!r} NOT in MULTIFAMILY_TYPES"


def test_merge_records_sums_units():
    source = MontgomeryHousingSource()
    records = [
        {"taxid": "TAX001", "structuretype": "Garden Apartment - Multifamily with 1-4 stories",
         "unitcount": "5", "streetaddress": "100 A St", "licensestatus": "Active"},
        {"taxid": "TAX001", "structuretype": "Garden Apartment - Multifamily with 1-4 stories",
         "unitcount": "10", "streetaddress": "100 A St", "licensestatus": "Active"},
        {"taxid": "TAX001", "structuretype": "Garden Apartment - Multifamily with 1-4 stories",
         "unitcount": "5", "streetaddress": "100 A St", "licensestatus": "Active"},
    ]
    result = source._merge_records("TAX001", records)
    assert result is not None
    assert result.unit_count == 20


def test_merge_records_uses_active_as_primary():
    source = MontgomeryHousingSource()
    records = [
        {"taxid": "TAX002", "structuretype": "Highrise - Multifamily with 9+ stories",
         "unitcount": "50", "streetaddress": "200 B St", "licensestatus": "Expired"},
        {"taxid": "TAX002", "structuretype": "Highrise - Multifamily with 9+ stories",
         "unitcount": "50", "streetaddress": "200 B St", "licensestatus": "Active"},
    ]
    result = source._merge_records("TAX002", records)
    assert result is not None
    assert result.license_status == "Active"


def test_merge_records_confidence_with_taxid():
    source = MontgomeryHousingSource()
    records = [
        {"taxid": "TAX003", "structuretype": "Highrise - Multifamily with 9+ stories",
         "unitcount": "100", "streetaddress": "300 C St", "licensestatus": "Active"},
    ]
    result = source._merge_records("TAX003", records)
    assert result is not None
    assert result.data_confidence > 0.5


def test_merge_records_without_street_returns_none():
    source = MontgomeryHousingSource()
    records = [
        {"taxid": "TAX004", "structuretype": "Garden Apartment - Multifamily with 1-4 stories",
         "unitcount": "5", "streetaddress": "", "licensestatus": "Active"},
    ]
    result = source._merge_records("TAX004", records)
    assert result is None


def test_total_units_skips_non_numeric():
    source = MontgomeryHousingSource()
    records = [
        {"unitcount": "5"},
        {"unitcount": "abc"},
        {"unitcount": ""},
        {"unitcount": "10"},
    ]
    assert source._total_units(records) == 15


def test_total_units_returns_none_when_all_empty():
    source = MontgomeryHousingSource()
    records = [{"unitcount": ""}, {"unitcount": "N/A"}]
    assert source._total_units(records) is None


def test_raw_property_schema():
    rp = RawProperty(
        source="montgomery_housing",
        source_url=None,
        county="montgomery",
        street_address="123 Main St",
        unit_count=25,
        unit_count_is_estimated=False,
        unit_count_confidence=0.9,
        data_confidence=0.85,
    )
    assert rp.source == "montgomery_housing"
    assert rp.unit_count == 25
