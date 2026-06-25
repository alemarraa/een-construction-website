"""Qualification stage: decide which properties meet the 4–100 unit criteria."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import AuditLog, Property
from ..pipeline.normalize import estimate_units_from_structure_type, is_in_range

logger = logging.getLogger(__name__)

MIN_UNITS = 4
MAX_UNITS = 100

# Confidence threshold below which we DON'T auto-qualify (requires manual review)
AUTO_QUALIFY_CONFIDENCE = 0.5

# Active licence statuses
ACTIVE_STATUSES = {"Active", "Renewed", "Pending Renewal"}


def qualify_all(session: Session) -> tuple[int, int, int]:
    """Qualify every unscored property. Returns (qualified, rejected, needs_review)."""
    qualified = rejected = needs_review = 0
    props = session.query(Property).all()

    for prop in props:
        result, reason = _qualify(prop)
        prop.qualifies = result is True
        prop.disqualify_reason = reason if result is not True else None
        session.add(
            AuditLog(
                entity_type="property",
                entity_id=prop.id,
                action="qualify",
                detail=f"result={result}, reason={reason or 'ok'}",
            )
        )
        if result is True:
            qualified += 1
        elif result is False:
            rejected += 1
        else:
            needs_review += 1

    return qualified, rejected, needs_review


def _qualify(prop: Property) -> tuple[bool | None, str | None]:
    """
    Returns:
      (True,  None)         → qualifies
      (False, reason)       → definitely rejected
      (None,  reason)       → needs manual review
    """
    # Must be in one of the two target counties
    if prop.county not in ("montgomery", "prince_georges"):
        return False, f"Wrong county: {prop.county}"

    # Determine effective unit count
    unit_count = prop.unit_count
    confidence = prop.unit_count_confidence

    # If no exact count, try to estimate from structure type
    if unit_count is None and prop.structure_type:
        est, est_conf = estimate_units_from_structure_type(prop.structure_type)
        if est is not None:
            unit_count = est
            confidence = est_conf
            prop.unit_count_estimated = est
            prop.unit_count_confidence = est_conf
            prop.unit_count_is_estimated = True
            prop.unit_count_source = "structure_type_inference"

    # No unit count at all
    if unit_count is None:
        return None, "Unit count unknown; needs manual verification"

    # Outside range
    if not is_in_range(unit_count, MIN_UNITS, MAX_UNITS):
        return False, f"Unit count {unit_count} outside 4–100 range"

    # Low-confidence estimates need manual review
    if prop.unit_count_is_estimated and confidence < AUTO_QUALIFY_CONFIDENCE:
        return None, (
            f"Estimated unit count {unit_count} (confidence {confidence:.0%}); "
            "needs manual verification"
        )

    # Check for inactive/denied licence
    if prop.license_status and prop.license_status not in ACTIVE_STATUSES:
        # Don't hard-reject: licence might be expired but property still operating
        if prop.license_status in ("Denied", "Withdrawn"):
            return False, f"Licence status: {prop.license_status}"

    return True, None
