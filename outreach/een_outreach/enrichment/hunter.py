"""Hunter.io enrichment adapter.

Hunter's domain-search endpoint returns publicly listed email addresses
and associated names/roles for a company domain.

Docs: https://hunter.io/api-documentation/v2
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from ..config import get_settings
from .base import BaseEnrichmentProvider, EnrichedContact

logger = logging.getLogger(__name__)

HUNTER_BASE = "https://api.hunter.io/v2"

# Roles Hunter returns that map to our priority contacts
PRIORITY_TITLES = {
    "property manager",
    "community manager",
    "regional manager",
    "regional property manager",
    "maintenance supervisor",
    "director of maintenance",
    "facilities manager",
    "operations manager",
    "asset manager",
    "portfolio manager",
    "property management",
    "leasing manager",
    "director of operations",
}


def _domain_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "").strip("/").lower()
        return domain if "." in domain else None
    except Exception:
        return None


class HunterProvider(BaseEnrichmentProvider):
    name = "hunter"

    def __init__(self):
        self._api_key = get_settings().hunter_api_key

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def find_contacts_for_domain(self, domain: str, company: str) -> list[EnrichedContact]:
        if not self.is_configured():
            return []
        clean = _domain_from_url(domain) or domain
        return self._domain_search(clean)

    def find_contacts_for_company(self, company: str) -> list[EnrichedContact]:
        # Hunter requires a domain; we can't search by company name alone
        return []

    def _domain_search(self, domain: str) -> list[EnrichedContact]:
        try:
            r = httpx.get(
                f"{HUNTER_BASE}/domain-search",
                params={
                    "domain": domain,
                    "api_key": self._api_key,
                    "limit": 20,
                    "type": "generic",
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json().get("data", {})
        except httpx.HTTPError as exc:
            logger.error("Hunter domain search failed for %s: %s", domain, exc)
            return []

        contacts: list[EnrichedContact] = []
        for email_entry in data.get("emails", []):
            email = email_entry.get("value", "")
            if not email:
                continue

            first = email_entry.get("first_name") or ""
            last = email_entry.get("last_name") or ""
            title = email_entry.get("position") or ""
            confidence = email_entry.get("confidence", 0) / 100.0

            contacts.append(
                EnrichedContact(
                    first_name=first or None,
                    last_name=last or None,
                    full_name=f"{first} {last}".strip() or None,
                    job_title=title or None,
                    email=email,
                    email_confidence=confidence,
                    source="hunter_domain_search",
                    raw=email_entry,
                )
            )

        # Prioritise by title relevance
        def priority(c: EnrichedContact) -> int:
            if not c.job_title:
                return 99
            return 0 if any(kw in c.job_title.lower() for kw in PRIORITY_TITLES) else 50

        contacts.sort(key=priority)
        logger.info("Hunter found %d contacts for %s", len(contacts), domain)
        return contacts
