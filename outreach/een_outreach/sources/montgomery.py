"""Montgomery County Housing Licensing and Registration source adapter.

Data: https://data.montgomerycountymd.gov/resource/et5s-xste.json
API: Socrata open data (no auth required; app token speeds up rate limits).
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Iterator

import httpx

from ..config import get_settings
from .base import BaseSource, RawProperty

logger = logging.getLogger(__name__)

DATASET_BASE = "https://data.montgomerycountymd.gov/resource"

# Structure types that indicate multifamily rental property
MULTIFAMILY_TYPES = {
    "Garden Apartment - Multifamily with 1-4 stories": "garden_apartment",
    "Midrise - Multifamily with 5-8 stories": "midrise",
    "Highrise - Multifamily with 9+ stories": "highrise",
    "Townhouse - Multifamily": "townhouse_multifamily",
    "Quadraplex - Single Family with 4 floors or units": "quadplex",
}

ACTIVE_STATUSES = {"Active", "Renewed", "Pending Renewal"}

# Ownership type normalisation
OWNERSHIP_MAP = {
    "LLC - Limited Liability Company": "llc",
    "Corporation": "corporation",
    "Sole ownership/Proprietor": "sole_proprietor",
    "Partnership": "partnership",
    "Trust": "trust",
}


class MontgomeryHousingSource(BaseSource):
    """Fetches multifamily rental licences from Montgomery County open data."""

    name = "montgomery_housing_licensing"
    county = "montgomery"

    def __init__(self):
        self._settings = get_settings()
        self._dataset_id = self._settings.montgomery_dataset_id
        self._app_token = self._settings.socrata_app_token

    def is_available(self) -> bool:
        try:
            url = f"{DATASET_BASE}/{self._dataset_id}.json"
            r = httpx.get(url, params={"$limit": 1}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def fetch(self) -> Iterator[RawProperty]:
        """Fetch and group multifamily records by tax_id (property level)."""
        raw_records: list[dict] = self._fetch_all_multifamily()
        logger.info(
            "Montgomery: fetched %d individual licence records", len(raw_records)
        )

        # Group by tax_id to aggregate units per property address
        by_tax: dict[str, list[dict]] = defaultdict(list)
        no_tax: list[dict] = []
        for rec in raw_records:
            tid = rec.get("taxid", "").strip()
            if tid:
                by_tax[tid].append(rec)
            else:
                no_tax.append(rec)

        # Process grouped records
        for tax_id, recs in by_tax.items():
            prop = self._merge_records(tax_id, recs)
            if prop:
                yield prop

        # Records without a tax_id — dedupe by normalised address
        by_addr: dict[str, list[dict]] = defaultdict(list)
        for rec in no_tax:
            key = f"{rec.get('streetaddress','').upper().strip()}|{rec.get('zipcode','').strip()}"
            by_addr[key].append(rec)

        for _key, recs in by_addr.items():
            prop = self._merge_records(None, recs)
            if prop:
                yield prop

    # ── Private helpers ────────────────────────────────────────────────────

    def _fetch_all_multifamily(self) -> list[dict]:
        """Page through the Socrata API returning only multifamily records."""
        url = f"{DATASET_BASE}/{self._dataset_id}.json"
        headers = {}
        if self._app_token:
            headers["X-App-Token"] = self._app_token

        # Build where clause for multifamily structure types
        type_list = ", ".join(f"'{t}'" for t in MULTIFAMILY_TYPES)
        where = f"structuretype in({type_list})"

        limit = 1000
        offset = 0
        results: list[dict] = []

        while True:
            params = {
                "$where": where,
                "$limit": limit,
                "$offset": offset,
                "$order": "taxid ASC",
            }
            try:
                r = httpx.get(url, params=params, headers=headers, timeout=30)
                r.raise_for_status()
                batch = r.json()
                if not batch:
                    break
                results.extend(batch)
                logger.debug("Montgomery: fetched offset=%d, batch=%d", offset, len(batch))
                if len(batch) < limit:
                    break
                offset += limit
                time.sleep(0.2)  # polite delay
            except httpx.HTTPError as exc:
                logger.error("Montgomery fetch error at offset %d: %s", offset, exc)
                break

        return results

    def _merge_records(
        self, tax_id: str | None, recs: list[dict]
    ) -> RawProperty | None:
        if not recs:
            return None

        # Use first active record as primary, fallback to first
        primary = next(
            (r for r in recs if r.get("licensestatus", "") in ACTIVE_STATUSES), recs[0]
        )

        # Aggregate unit count across all units in building
        unit_count = self._total_units(recs)

        street = primary.get("streetaddress", "").strip()
        if not street:
            return None

        structure_type = primary.get("structuretype", "").strip()
        property_type = MULTIFAMILY_TYPES.get(structure_type, "unknown")

        # Confidence: higher when we have tax_id + active licence + confirmed units
        confidence = 0.5
        if tax_id:
            confidence += 0.15
        if primary.get("licensestatus", "") in ACTIVE_STATUSES:
            confidence += 0.2
        if unit_count and unit_count > 0:
            confidence += 0.15

        return RawProperty(
            source=self.name,
            source_url=(
                f"https://data.montgomerycountymd.gov/resource/{self._dataset_id}.json"
                f"?taxid={tax_id}" if tax_id else None
            ),
            county="montgomery",
            street_address=street,
            city=primary.get("city", "").strip() or None,
            zip_code=primary.get("zipcode", "").strip() or None,
            structure_type=structure_type,
            property_type=property_type,
            unit_count=unit_count,
            unit_count_is_estimated=False,
            unit_count_confidence=0.85 if unit_count else 0.0,
            unit_count_source="montgomery_housing_licensing_sum",
            license_number=primary.get("licensenumber", "").strip() or None,
            license_status=primary.get("licensestatus", "").strip() or None,
            license_type=primary.get("licensetype", "").strip() or None,
            tax_id=tax_id,
            ownership_type=OWNERSHIP_MAP.get(
                primary.get("ownershiptype", ""), "unknown"
            ),
            data_confidence=round(confidence, 2),
            notes=(
                f"{len(recs)} licence record(s) found for this tax ID. "
                f"Year built: {primary.get('yearbuilt', 'unknown')}."
            ),
            raw=primary,
        )

    @staticmethod
    def _total_units(recs: list[dict]) -> int | None:
        """Sum unitcount across records; None if no numeric values found."""
        total = 0
        found_any = False
        for r in recs:
            uc = r.get("unitcount", "")
            try:
                val = int(float(uc))
                if val > 0:
                    total += val
                    found_any = True
            except (ValueError, TypeError):
                pass
        return total if found_any else None
