"""Abstract base for contact-enrichment providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EnrichedContact:
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    job_title: str | None = None
    email: str | None = None
    email_confidence: float = 0.0
    phone: str | None = None
    linkedin_url: str | None = None
    source: str = ""
    raw: dict = field(default_factory=dict)


class BaseEnrichmentProvider(ABC):
    name: str = ""

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def find_contacts_for_domain(self, domain: str, company: str) -> list[EnrichedContact]:
        """Return publicly listed contacts at a domain."""
        ...

    @abstractmethod
    def find_contacts_for_company(self, company: str) -> list[EnrichedContact]:
        """Return contacts when only a company name is available."""
        ...
