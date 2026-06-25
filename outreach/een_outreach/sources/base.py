"""Abstract base class for property data sources."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class RawProperty:
    """Normalized record returned by any source adapter."""

    source: str
    source_url: str | None
    county: str  # "montgomery" | "prince_georges"

    street_address: str
    address_line2: str | None = None
    city: str | None = None
    zip_code: str | None = None
    state: str = "MD"

    property_name: str | None = None
    structure_type: str | None = None
    property_type: str | None = None  # garden_apartment, midrise, etc.

    unit_count: int | None = None
    unit_count_is_estimated: bool = False
    unit_count_confidence: float = 0.0
    unit_count_source: str | None = None

    license_number: str | None = None
    license_status: str | None = None
    license_type: str | None = None

    tax_id: str | None = None
    ownership_type: str | None = None
    owner_entity: str | None = None

    management_company: str | None = None
    management_website: str | None = None
    property_website: str | None = None
    public_phone: str | None = None

    data_confidence: float = 0.0
    notes: str | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict | None = None

    def effective_unit_count(self) -> int | None:
        return self.unit_count if self.unit_count is not None else self.unit_count_is_estimated


class BaseSource(ABC):
    """Every source adapter must implement this interface."""

    name: str = ""
    county: str = ""

    @abstractmethod
    def fetch(self) -> Iterator[RawProperty]:
        """Yield raw property records from the source."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the source is reachable / configured."""
        ...
