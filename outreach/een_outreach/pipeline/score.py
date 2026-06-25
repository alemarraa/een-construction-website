"""Lead-scoring stage: compute a 0–100 score for each qualified property."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..models import Contact, EmailCampaign, Organization, Property, PropertyOrgRelationship

logger = logging.getLogger(__name__)

# ── Weight definitions ─────────────────────────────────────────────────────

W_UNIT_FIT = 20        # unit count in 10–50 sweet spot
W_DATA_CONFIDENCE = 20  # how reliable is our property data
W_MGMT_RELATIONSHIP = 15  # management company identified
W_CONTACT_QUALITY = 20  # contact seniority + verified email
W_ACTIVITY_SIGNALS = 15  # evidence of active operation
W_RECENCY = 10          # how recent is the data


def score_property(prop: Property, session: Session) -> float:
    """Return a 0–100 lead score for a qualified property."""
    score = 0.0

    # ── Unit-count fit (sweet spot 10–50 units) ────────────────────────────
    uc = prop.unit_count or prop.unit_count_estimated or 0
    if 10 <= uc <= 50:
        score += W_UNIT_FIT
    elif 4 <= uc < 10:
        score += W_UNIT_FIT * 0.7
    elif 50 < uc <= 100:
        score += W_UNIT_FIT * 0.5

    # ── Data confidence ────────────────────────────────────────────────────
    score += W_DATA_CONFIDENCE * min(prop.data_confidence, 1.0)

    # ── Management relationship ────────────────────────────────────────────
    mgmt_rel = (
        session.query(PropertyOrgRelationship)
        .filter_by(property_id=prop.id, relationship_type="manager")
        .first()
    )
    if mgmt_rel:
        score += W_MGMT_RELATIONSHIP * min(mgmt_rel.confidence, 1.0)
    elif prop.owner_entity:
        score += W_MGMT_RELATIONSHIP * 0.3  # owner only, no manager found

    # ── Contact quality ────────────────────────────────────────────────────
    contact_score = _best_contact_score(prop, session)
    score += W_CONTACT_QUALITY * contact_score

    # ── Activity signals ───────────────────────────────────────────────────
    activity = 0.0
    if prop.license_status in ("Active", "Renewed"):
        activity += 0.6
    if prop.unit_count is not None and not prop.unit_count_is_estimated:
        activity += 0.4
    score += W_ACTIVITY_SIGNALS * min(activity, 1.0)

    # ── Recency ────────────────────────────────────────────────────────────
    if prop.source_checked_at:
        checked = prop.source_checked_at
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - checked).days
        recency = max(0.0, 1.0 - age_days / 365)
        score += W_RECENCY * recency
    else:
        score += W_RECENCY * 0.3

    return round(min(score, 100.0), 1)


def _best_contact_score(prop: Property, session: Session) -> float:
    """Return 0–1 based on best available contact for this property."""
    # Contacts via organisation relationship
    org_ids = [
        r.organization_id
        for r in session.query(PropertyOrgRelationship).filter_by(property_id=prop.id).all()
    ]
    if not org_ids:
        return 0.0

    contacts = (
        session.query(Contact)
        .filter(Contact.organization_id.in_(org_ids))
        .filter(Contact.do_not_contact == False)
        .all()
    )
    if not contacts:
        return 0.0

    # Find the highest-priority contact
    role_priority = {
        "property_manager": 1.0,
        "community_manager": 0.95,
        "regional_manager": 0.9,
        "maintenance_supervisor": 0.85,
        "facilities_manager": 0.8,
        "operations_manager": 0.75,
        "asset_manager": 0.7,
        "owner": 0.6,
        "generic": 0.3,
    }

    email_score_map = {
        "verified": 1.0,
        "catch_all": 0.7,
        "unknown": 0.5,
        "risky": 0.2,
        "invalid": 0.0,
        "disposable": 0.0,
    }

    best = 0.0
    for c in contacts:
        if not c.email:
            continue
        rp = role_priority.get(c.role, 0.3)
        es = email_score_map.get(c.email_status, 0.4)
        ec = c.email_confidence
        combined = rp * 0.5 + es * 0.3 + ec * 0.2
        best = max(best, combined)

    return best


def score_all(session: Session) -> int:
    """Re-score all qualified properties. Returns count updated."""
    props = session.query(Property).filter_by(qualifies=True).all()
    for prop in props:
        prop.lead_score = score_property(prop, session)
    return len(props)
