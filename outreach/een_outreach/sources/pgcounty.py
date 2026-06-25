"""Prince George's County property adapter.

Primary source: Maryland SDAT open data via opendata.maryland.gov
Dataset: Prince George's County Real Property Assessments (w3eb-4mzd)

The SDAT dataset does not reliably contain unit counts, so we:
  1. Filter by residential land-use codes that indicate multifamily.
  2. Use the CAMA dwelling-type code where available.
  3. Mark unit_count_is_estimated=True and assign lower confidence.

A CSV import adapter is also provided for manual exports from:
  https://sdat.dat.maryland.gov/RealProperty/Pages/default.aspx
"""

from __future__ import annotations

import csv
import io
import logging
import time
from typing import Iterator

import httpx

from .base import BaseSource, RawProperty

logger = logging.getLogger(__name__)

SDAT_BASE = "https://opendata.maryland.gov/resource"
PG_DATASET_ID = "w3eb-4mzd"

# SDAT land-use codes that typically indicate multifamily rental properties
MULTIFAMILY_LU_CODES = {
    "Apartments (A)",
    "Apartments, High Rise (A)",
    "Residential (R)",  # broad; filter by CAMA dwelling type below
}

# SDAT CAMA dwelling-type codes indicating multifamily
MULTIFAMILY_CAMA_TYPES = {
    "Apartment",
    "Apartments",
    "Garden Apartment",
    "High Rise",
    "Mid Rise",
    "Multi-Family",
    "Multifamily",
    "Duplex/Triplex",  # include for 4-unit aggregation
}


class PGCountySDATSource(BaseSource):
    """Fetches Prince George's County multifamily properties from SDAT open data."""

    name = "pgcounty_sdat"
    county = "prince_georges"

    def is_available(self) -> bool:
        try:
            url = f"{SDAT_BASE}/{PG_DATASET_ID}.json"
            r = httpx.get(url, params={"$limit": 1}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def fetch(self) -> Iterator[RawProperty]:
        yield from self._fetch_from_api()

    def _fetch_from_api(self) -> Iterator[RawProperty]:
        url = f"{SDAT_BASE}/{PG_DATASET_ID}.json"

        # Filter to likely multifamily: Apartments land-use code
        # The field name in this dataset is extremely long
        lu_field = "land_use_code_mdp_field_lu_desclu_sdat_field_50"
        dwelling_field = "additional_c_a_m_a_data_dwelling_type_mdp_field_strubldg_sdat_field_265"

        where = (
            f"{lu_field} like '%Apartment%' OR "
            f"{lu_field} like '%Multi%' OR "
            f"{dwelling_field} like '%Apartment%' OR "
            f"{dwelling_field} like '%Multi%'"
        )

        limit = 1000
        offset = 0

        while True:
            params = {
                "$where": where,
                "$limit": limit,
                "$offset": offset,
                "$order": "parent_account_number_account_number_sdat_field_388 ASC",
            }
            try:
                r = httpx.get(url, params=params, timeout=45)
                r.raise_for_status()
                batch = r.json()
                if not batch:
                    break
                for rec in batch:
                    prop = self._parse_sdat_record(rec)
                    if prop:
                        yield prop
                logger.debug("PG SDAT: offset=%d, batch=%d", offset, len(batch))
                if len(batch) < limit:
                    break
                offset += limit
                time.sleep(0.3)
            except httpx.HTTPError as exc:
                logger.error("PG SDAT fetch error: %s", exc)
                break

    def _parse_sdat_record(self, rec: dict) -> RawProperty | None:
        # Extract key fields (SDAT uses extremely verbose field names)
        county_name = rec.get("county_name_mdp_field_cntyname", "")
        if "Prince George" not in county_name:
            return None

        # Address
        addr_field = "premise_address_street_name_mdp_field_premaddr_sdat_field_20"
        street_num = rec.get("premise_address_street_number_mdp_field_premno_sdat_field_17", "")
        street_name = rec.get(addr_field, "")
        city = rec.get("premise_address_city_mdp_field_premcity_sdat_field_25", "")
        zip_code = rec.get("premise_address_zip_code_mdp_field_premzip_sdat_field_26", "")

        street = f"{street_num} {street_name}".strip()
        if not street or street == "0":
            return None

        # Owner
        owner = rec.get("owner_name_1_mdp_field_ownname1_sdat_field_30", "")

        # Dwelling type for property classification
        dwelling_type = rec.get(
            "additional_c_a_m_a_data_dwelling_type_mdp_field_strubldg_sdat_field_265", ""
        )
        property_type = self._map_property_type(dwelling_type)

        # Unit count: SDAT doesn't reliably carry this; mark estimated
        # Use improvements value as a proxy signal for confidence
        improvements = int(
            rec.get("current_cycle_data_improvements_value_mdp_field_names_nfmimpvl_curimpvl_and_salimpvl_sdat_field_165", 0) or 0
        )
        has_improvements = improvements > 10000

        # Tax account number
        account_number = rec.get(
            "parent_account_number_account_number_sdat_field_388", ""
        )

        confidence = 0.4
        if has_improvements:
            confidence += 0.1
        if owner:
            confidence += 0.1

        return RawProperty(
            source=self.name,
            source_url=f"https://opendata.maryland.gov/resource/{PG_DATASET_ID}.json",
            county="prince_georges",
            street_address=street,
            city=city.strip() or None,
            zip_code=zip_code[:5] if zip_code else None,
            property_type=property_type,
            structure_type=dwelling_type or None,
            unit_count=None,
            unit_count_is_estimated=True,
            unit_count_confidence=0.2,
            unit_count_source="sdat_dwelling_type_inference",
            tax_id=account_number or None,
            owner_entity=owner.strip() or None,
            data_confidence=round(confidence, 2),
            notes=(
                f"SDAT record. Dwelling type: {dwelling_type or 'unknown'}. "
                f"Unit count not available in source; requires manual verification."
            ),
            raw=rec,
        )

    @staticmethod
    def _map_property_type(dwelling_type: str) -> str:
        dt = dwelling_type.lower()
        if "high rise" in dt or "highrise" in dt:
            return "highrise"
        if "mid" in dt:
            return "midrise"
        if "garden" in dt:
            return "garden_apartment"
        if "apartment" in dt or "multi" in dt:
            return "garden_apartment"
        return "unknown"


class PGCountyCSVSource(BaseSource):
    """Accepts a manually exported CSV from the SDAT Real Property search.

    Usage:
        source = PGCountyCSVSource("/path/to/export.csv")
        for prop in source.fetch():
            ...
    """

    name = "pgcounty_csv"
    county = "prince_georges"

    def __init__(self, csv_path: str):
        self._csv_path = csv_path

    def is_available(self) -> bool:
        import os
        return os.path.isfile(self._csv_path)

    def fetch(self) -> Iterator[RawProperty]:
        with open(self._csv_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                prop = self._parse_row(row)
                if prop:
                    yield prop

    def _parse_row(self, row: dict) -> RawProperty | None:
        street = row.get("Address", row.get("STREET_ADDRESS", "")).strip()
        if not street:
            return None

        try:
            unit_count = int(row.get("Units", row.get("UNIT_COUNT", "") or 0))
        except (ValueError, TypeError):
            unit_count = None

        owner = row.get("Owner", row.get("OWNER", "")).strip() or None
        city = row.get("City", row.get("CITY", "")).strip() or None
        zip_code = row.get("Zip", row.get("ZIP", "")).strip()[:5] or None

        return RawProperty(
            source=self.name,
            source_url=None,
            county="prince_georges",
            street_address=street,
            city=city,
            zip_code=zip_code,
            unit_count=unit_count,
            unit_count_is_estimated=unit_count is None,
            unit_count_confidence=0.7 if unit_count else 0.2,
            unit_count_source="csv_export",
            owner_entity=owner,
            data_confidence=0.6 if unit_count else 0.35,
            notes="Manual CSV export from SDAT.",
            raw=dict(row),
        )
