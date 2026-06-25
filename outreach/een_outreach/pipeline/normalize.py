"""Address and entity name normalisation utilities."""

from __future__ import annotations

import re
import unicodedata


# ── Address normalisation ──────────────────────────────────────────────────

_STREET_ABBR = {
    r"\bAVENUE\b": "AVE",
    r"\bBOULEVARD\b": "BLVD",
    r"\bCIRCLE\b": "CIR",
    r"\bCOURT\b": "CT",
    r"\bDRIVE\b": "DR",
    r"\bEXPRESSWAY\b": "EXPY",
    r"\bFREEWAY\b": "FWY",
    r"\bHIGHWAY\b": "HWY",
    r"\bLANE\b": "LN",
    r"\bPARKWAY\b": "PKWY",
    r"\bPLACE\b": "PL",
    r"\bROAD\b": "RD",
    r"\bROUTE\b": "RT",
    r"\bSTREET\b": "ST",
    r"\bTERRACE\b": "TER",
    r"\bTRAIL\b": "TRL",
    r"\bWAY\b": "WAY",
    r"\bNORTH\b(?=\s)": "N",
    r"\bSOUTH\b(?=\s)": "S",
    r"\bEAST\b(?=\s)": "E",
    r"\bWEST\b(?=\s)": "W",
}

_DIRECTIONS = re.compile(
    r"\b(NORTH|SOUTH|EAST|WEST|N|S|E|W|NE|NW|SE|SW)\b", re.IGNORECASE
)


def normalize_address(
    street: str,
    city: str | None = None,
    state: str = "MD",
    zip_code: str | None = None,
) -> str:
    """Return a canonical address string for deduplication purposes."""
    addr = _ascii_upper(street)

    # Remove punctuation except hyphens in numbers
    addr = re.sub(r"[^\w\s\-]", " ", addr)
    addr = re.sub(r"\s+", " ", addr).strip()

    # Apply abbreviations
    for pattern, replacement in _STREET_ABBR.items():
        addr = re.sub(pattern, replacement, addr)

    parts = [addr]
    if city:
        parts.append(_ascii_upper(city))
    if state:
        parts.append(state.upper())
    if zip_code:
        parts.append(zip_code[:5])

    return ", ".join(p.strip() for p in parts if p.strip())


def normalize_org_name(name: str) -> str:
    """Canonical organisation name for deduplication."""
    n = _ascii_upper(name)
    # Strip legal suffixes for matching
    n = re.sub(
        r"\b(LLC|INC|CORP|LTD|LP|LLP|PLLC|PROPERTIES|PROPERTY|MANAGEMENT|REALTY|GROUP|ASSOCIATES|CO)\b",
        "",
        n,
    )
    n = re.sub(r"[^\w\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _ascii_upper(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.upper()


# ── Unit count helpers ─────────────────────────────────────────────────────


def is_in_range(unit_count: int | None, low: int = 4, high: int = 100) -> bool:
    if unit_count is None:
        return False
    return low <= unit_count <= high


def estimate_units_from_structure_type(structure_type: str) -> tuple[int | None, float]:
    """Return (estimated_count, confidence) from structure type string alone."""
    st = structure_type.lower()
    if "quadraplex" in st or "quadplex" in st:
        return 4, 0.6
    if "duplex" in st:
        return 2, 0.6
    if "highrise" in st or "high rise" in st:
        return 50, 0.25  # wide range; very uncertain
    if "midrise" in st or "mid rise" in st:
        return 24, 0.25
    if "garden" in st and "multifamily" in st:
        return 12, 0.2
    return None, 0.0
