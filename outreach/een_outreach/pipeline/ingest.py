"""Ingest stage: fetch raw records from sources and upsert into the database."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import AuditLog, CrawlRun, Property, SourceRecord
from ..pipeline.normalize import normalize_address, normalize_org_name
from ..sources.base import RawProperty

logger = logging.getLogger(__name__)


def ingest_raw(session: Session, raw: RawProperty, run: CrawlRun) -> Property:
    """Upsert a RawProperty into the database. Returns the Property row."""
    norm_addr = normalize_address(
        raw.street_address, raw.city, raw.state or "MD", raw.zip_code
    )

    # Try to find existing property by normalised address + county
    prop = (
        session.query(Property)
        .filter_by(normalized_address=norm_addr, county=raw.county)
        .first()
    )

    if prop is None:
        prop = Property(
            street_address=raw.street_address.strip(),
            address_line2=raw.address_line2,
            city=raw.city,
            county=raw.county,
            zip_code=raw.zip_code,
            normalized_address=norm_addr,
            name=raw.property_name,
            structure_type=raw.structure_type,
            property_type=raw.property_type or "unknown",
            unit_count=raw.unit_count,
            unit_count_estimated=raw.unit_count,
            unit_count_confidence=raw.unit_count_confidence,
            unit_count_source=raw.unit_count_source,
            unit_count_is_estimated=raw.unit_count_is_estimated,
            license_number=raw.license_number,
            license_status=raw.license_status,
            license_type=raw.license_type,
            tax_id=raw.tax_id,
            ownership_type=raw.ownership_type,
            owner_entity=raw.owner_entity,
            data_confidence=raw.data_confidence,
            source_url=raw.source_url,
            source_checked_at=raw.fetched_at,
            notes=raw.notes,
        )
        session.add(prop)
        session.flush()
        run.records_new += 1
        logger.debug("New property: %s [%s]", norm_addr, raw.county)
    else:
        # Update only if new data is more confident
        if raw.data_confidence >= prop.data_confidence:
            _update_property(prop, raw)
        run.records_updated += 1

    # Always record the raw source
    sr = SourceRecord(
        property_id=prop.id,
        source_name=raw.source,
        source_url=raw.source_url,
        raw_data=json.dumps(raw.raw, default=str) if raw.raw else None,
        fetched_at=raw.fetched_at,
    )
    session.add(sr)
    run.records_fetched += 1
    return prop


def _update_property(prop: Property, raw: RawProperty) -> None:
    """Overwrite stale fields with fresher source data."""
    if raw.unit_count is not None and not raw.unit_count_is_estimated:
        prop.unit_count = raw.unit_count
        prop.unit_count_confidence = raw.unit_count_confidence
        prop.unit_count_source = raw.unit_count_source
        prop.unit_count_is_estimated = raw.unit_count_is_estimated

    if raw.license_number:
        prop.license_number = raw.license_number
    if raw.license_status:
        prop.license_status = raw.license_status
    if raw.tax_id and not prop.tax_id:
        prop.tax_id = raw.tax_id
    if raw.owner_entity and not prop.owner_entity:
        prop.owner_entity = raw.owner_entity
    if raw.structure_type and not prop.structure_type:
        prop.structure_type = raw.structure_type
    if raw.property_type and prop.property_type == "unknown":
        prop.property_type = raw.property_type

    prop.data_confidence = max(prop.data_confidence, raw.data_confidence)
    prop.source_checked_at = raw.fetched_at
    prop.updated_at = datetime.now(timezone.utc)
