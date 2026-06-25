"""Tests for address and org-name normalisation."""

import pytest
from een_outreach.pipeline.normalize import normalize_address, normalize_org_name, is_in_range


@pytest.mark.parametrize("raw,expected_fragment", [
    ("123 Main Street", "MAIN ST"),
    ("456 Oak Avenue NW", "OAK AVE"),
    ("789 N. Broadway Blvd", "BROADWAY BLVD"),
    ("  1000  Elm   Drive  ", "ELM DR"),
])
def test_address_normalisation_fragments(raw, expected_fragment):
    result = normalize_address(raw)
    assert expected_fragment in result


def test_address_deduplication_same_norm():
    a = normalize_address("123 Main Street")
    b = normalize_address("123 main st")
    assert a == b


def test_address_includes_state():
    result = normalize_address("100 Test Ave")
    assert "MD" in result


@pytest.mark.parametrize("raw,expected_fragment", [
    ("Greystar Real Estate Partners, LLC", "GREYSTAR"),
    ("AIMCO Properties Inc.", "AIMCO"),
    ("Smith & Associates Corp.", "SMITH"),
])
def test_org_name_normalisation_strips_suffixes(raw, expected_fragment):
    result = normalize_org_name(raw)
    assert expected_fragment in result
    # Legal suffixes should be stripped
    for suffix in ("LLC", "INC", "CORP", "PROPERTIES", "ASSOCIATES"):
        if suffix in raw.upper():
            # The suffix should NOT appear in isolation (word boundary stripped)
            assert not result.strip().endswith(suffix.strip())


@pytest.mark.parametrize("n,expected", [
    (4, True),
    (100, True),
    (50, True),
    (3, False),
    (101, False),
    (0, False),
])
def test_is_in_range(n, expected):
    assert is_in_range(n) == expected


def test_is_in_range_none():
    assert is_in_range(None) is False
