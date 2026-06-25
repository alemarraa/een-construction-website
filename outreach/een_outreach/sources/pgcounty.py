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

# Correct field names from the actual dataset schema
_LU_FIELD = "land_use_code_mdp_field_lu_desclu_sdat_field_50"
_DW_FIELD = "additional_c_a_m_a_data_dwelling_type_mdp_field_strubldg_sdat_field_265"
_UNITS_FIELD = "c_a_m_a_system_data_number_of_dwelling_units_mdp_field_bldg_units_sdat_field_239"
_ADDR_NUM_FIELD = "premise_address_number_mdp_field_premsnum_sdat_field_20"
_ADDR_NAME_FIELD = "premise_address_name_mdp_field_premsnam_sdat_field_23"
_ADDR_TYPE_FIELD = "premise_address_type_mdp_field_premstyp_sdat_field_24"
_CITY_FIELD = "premise_address_city_mdp_field_premcity_sdat_field_25"
_ZIP_FIELD = "premise_address_zip_code_mdp_field_premzip_sdat_field_26"
_ACCOUNT_FIELD = "parent_account_number_account_number_sdat_field_388"
_COUNTY_FIELD = "county_name_mdp_field_cntyname"
_YEAR_BUILT_FIELD = "c_a_m_a_system_data_year_built_yyyy_mdp_field_yearblt_sdat_field_235"
_IMPROVEMENTS_FIELD = "current_cycle_data_improvements_value_mdp_field_names_nfmimpvl_curimpvl_and_salimpvl_sdat_field_165"

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
    """Fetches Prince George's County multifamily properties from SDAT open data.

    Requires a free Socrata app token from https://opendata.maryland.gov to bypass
    Cloudflare bot-protection on filtered queries. Set SOCRATA_APP_TOKEN in .env.
    Without a token, filtered queries return 403 and the source is marked unavailable.
    """

    name = "pgcounty_sdat"
    county = "prince_georges"

    def __init__(self):
        from ..config import get_settings
        self._app_token = get_settings().socrata_app_token

    def _headers(self) -> dict:
        if self._app_token:
            return {"X-App-Token": self._app_token}
        return {}

    def is_available(self) -> bool:
        """Returns True only if filtered queries succeed (requires App Token)."""
        try:
            url = f"{SDAT_BASE}/{PG_DATASET_ID}.json"
            r = httpx.get(
                url,
                params={f"$where": f"{_LU_FIELD} like '%Apartment%'", "$limit": 1},
                headers=self._headers(),
                timeout=10,
            )
            return r.status_code == 200
        except Exception:
            return False

    def fetch(self) -> Iterator[RawProperty]:
        yield from self._fetch_from_api()

    def _fetch_from_api(self) -> Iterator[RawProperty]:
        url = f"{SDAT_BASE}/{PG_DATASET_ID}.json"

        where = (
            f"{_LU_FIELD} like '%Apartment%' OR "
            f"{_LU_FIELD} like '%Multi%' OR "
            f"{_DW_FIELD} like '%Apartment%' OR "
            f"{_DW_FIELD} like '%Multi%'"
        )

        limit = 1000
        offset = 0

        while True:
            params = {
                "$where": where,
                "$limit": limit,
                "$offset": offset,
                "$order": f"{_ACCOUNT_FIELD} ASC",
            }
            try:
                r = httpx.get(url, params=params, headers=self._headers(), timeout=45)
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
        county_name = rec.get(_COUNTY_FIELD, "")
        if "Prince George" not in county_name:
            return None

        # Build street address from number + name + type
        addr_num = rec.get(_ADDR_NUM_FIELD, "").strip()
        addr_name = rec.get(_ADDR_NAME_FIELD, "").strip()
        addr_type = rec.get(_ADDR_TYPE_FIELD, "").strip()
        street = " ".join(part for part in [addr_num, addr_name, addr_type] if part)
        if not street or street == "0":
            return None

        city = rec.get(_CITY_FIELD, "").strip() or None
        zip_code = rec.get(_ZIP_FIELD, "").strip()
        dwelling_type = rec.get(_DW_FIELD, "").strip()
        property_type = self._map_property_type(dwelling_type)
        account_number = rec.get(_ACCOUNT_FIELD, "").strip()

        # Unit count from CAMA if available
        raw_units = rec.get(_UNITS_FIELD, "")
        try:
            unit_count = int(raw_units) if raw_units else None
        except (ValueError, TypeError):
            unit_count = None

        improvements = 0
        try:
            improvements = int(rec.get(_IMPROVEMENTS_FIELD, 0) or 0)
        except (ValueError, TypeError):
            pass
        has_improvements = improvements > 10_000

        confidence = 0.4
        if has_improvements:
            confidence += 0.1
        if unit_count:
            confidence += 0.1

        return RawProperty(
            source=self.name,
            source_url=f"https://opendata.maryland.gov/resource/{PG_DATASET_ID}.json",
            county="prince_georges",
            street_address=street,
            city=city,
            zip_code=zip_code[:5] if zip_code else None,
            property_type=property_type,
            structure_type=dwelling_type or None,
            unit_count=unit_count,
            unit_count_is_estimated=unit_count is None,
            unit_count_confidence=0.7 if unit_count else 0.2,
            unit_count_source="sdat_cama_units" if unit_count else "sdat_dwelling_type_inference",
            tax_id=account_number or None,
            data_confidence=round(confidence, 2),
            notes=(
                f"SDAT record. Dwelling type: {dwelling_type or 'unknown'}. "
                f"{'Unit count from CAMA.' if unit_count else 'Unit count not in source; verify manually.'}"
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
