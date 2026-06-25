"""SQLAlchemy ORM models for the EEN Construction outreach system."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────


class County(str, enum.Enum):
    montgomery = "montgomery"
    prince_georges = "prince_georges"


class LicenseStatus(str, enum.Enum):
    active = "Active"
    renewed = "Renewed"
    expired = "Expired"
    denied = "Denied"
    withdrawn = "Withdrawn"
    unknown = "Unknown"


class PropertyType(str, enum.Enum):
    garden_apartment = "garden_apartment"
    midrise = "midrise"
    highrise = "highrise"
    townhouse_multifamily = "townhouse_multifamily"
    quadplex = "quadplex"
    mixed_use = "mixed_use"
    unknown = "unknown"


class OwnershipType(str, enum.Enum):
    llc = "llc"
    corporation = "corporation"
    sole_proprietor = "sole_proprietor"
    partnership = "partnership"
    trust = "trust"
    unknown = "unknown"


class ContactRole(str, enum.Enum):
    property_manager = "property_manager"
    community_manager = "community_manager"
    regional_manager = "regional_manager"
    maintenance_supervisor = "maintenance_supervisor"
    facilities_manager = "facilities_manager"
    operations_manager = "operations_manager"
    asset_manager = "asset_manager"
    owner = "owner"
    generic = "generic"


class EmailStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    invalid = "invalid"
    risky = "risky"
    catch_all = "catch_all"
    disposable = "disposable"
    unknown = "unknown"


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    queued = "queued"
    sent = "sent"
    bounced = "bounced"
    complained = "complained"
    replied = "replied"
    unsubscribed = "unsubscribed"
    suppressed = "suppressed"


class MessageStatus(str, enum.Enum):
    draft = "draft"
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    bounced_soft = "bounced_soft"
    bounced_hard = "bounced_hard"
    complained = "complained"
    replied = "replied"
    skipped = "skipped"


# ── Core Models ────────────────────────────────────────────────────────────


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("normalized_address", "county", name="uq_property_addr_county"),
        Index("ix_property_tax_id", "tax_id"),
        Index("ix_property_license_num", "license_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(300))
    street_address: Mapped[str] = mapped_column(String(300), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    county: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    state: Mapped[str] = mapped_column(String(2), default="MD")
    normalized_address: Mapped[str] = mapped_column(String(400), nullable=False)

    # Unit counts
    unit_count: Mapped[Optional[int]] = mapped_column(Integer)
    unit_count_estimated: Mapped[Optional[int]] = mapped_column(Integer)
    unit_count_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    unit_count_source: Mapped[Optional[str]] = mapped_column(String(200))
    unit_count_is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Classification
    property_type: Mapped[str] = mapped_column(String(50), default="unknown")
    structure_type: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # License
    license_number: Mapped[Optional[str]] = mapped_column(String(50))
    license_status: Mapped[Optional[str]] = mapped_column(String(50))
    license_type: Mapped[Optional[str]] = mapped_column(String(200))

    # Tax / ownership
    tax_id: Mapped[Optional[str]] = mapped_column(String(50))
    ownership_type: Mapped[Optional[str]] = mapped_column(String(50))
    owner_entity: Mapped[Optional[str]] = mapped_column(String(300))

    # Scoring
    data_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)
    qualifies: Mapped[bool] = mapped_column(Boolean, default=False)
    disqualify_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Meta
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    source_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    # Relationships
    org_relationships: Mapped[list[PropertyOrgRelationship]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    source_records: Mapped[list[SourceRecord]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    email_campaigns: Mapped[list[EmailCampaign]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_org_name"),
        Index("ix_org_domain", "website_domain"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(300), nullable=False)
    org_type: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    website_domain: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    street_address: Mapped[Optional[str]] = mapped_column(String(300))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(2))
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    contacts: Mapped[list[Contact]] = relationship(back_populates="organization")
    property_relationships: Mapped[list[PropertyOrgRelationship]] = relationship(
        back_populates="organization"
    )


class PropertyOrgRelationship(Base):
    __tablename__ = "property_organization_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # owner, manager, parent
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    property: Mapped[Property] = relationship(back_populates="org_relationships")
    organization: Mapped[Organization] = relationship(back_populates="property_relationships")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("email", name="uq_contact_email"),
        Index("ix_contact_org", "organization_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    job_title: Mapped[Optional[str]] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(50), default="generic")
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[Optional[str]] = mapped_column(String(320))
    email_source: Mapped[Optional[str]] = mapped_column(String(200))
    email_status: Mapped[str] = mapped_column(String(30), default="unknown")
    email_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_generic_address: Mapped[bool] = mapped_column(Boolean, default=False)
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    organization: Mapped[Optional[Organization]] = relationship(back_populates="contacts")
    email_campaigns: Mapped[list[EmailCampaign]] = relationship(back_populates="contact")


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"))
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    raw_data: Mapped[Optional[str]] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    property: Mapped[Optional[Property]] = relationship(back_populates="source_records")


class EmailCampaign(Base):
    """One campaign = one contact × one property (or portfolio)."""

    __tablename__ = "email_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"))
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    sequence_number: Mapped[int] = mapped_column(Integer, default=0)
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    personalization_notes: Mapped[Optional[str]] = mapped_column(Text)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    queued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    skip_reason: Mapped[Optional[str]] = mapped_column(String(500))

    property: Mapped[Optional[Property]] = relationship(back_populates="email_campaigns")
    contact: Mapped[Contact] = relationship(back_populates="email_campaigns")
    messages: Mapped[list[EmailMessage]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class EmailMessage(Base):
    """Individual delivery attempt within a campaign."""

    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("email_campaigns.id"), nullable=False)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    bounce_type: Mapped[Optional[str]] = mapped_column(String(30))
    bounce_reason: Mapped[Optional[str]] = mapped_column(Text)
    complained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    campaign: Mapped[EmailCampaign] = relationship(back_populates="messages")
    events: Mapped[list[EmailEvent]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("email_messages.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    provider_data: Mapped[Optional[str]] = mapped_column(Text)

    message: Mapped[EmailMessage] = relationship(back_populates="events")


class SuppressionList(Base):
    __tablename__ = "suppression_list"
    __table_args__ = (UniqueConstraint("email", name="uq_suppression_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # unsubscribe, bounce_hard, complaint, manual
    notes: Mapped[Optional[str]] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    permanent: Mapped[bool] = mapped_column(Boolean, default=True)


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    county: Mapped[Optional[str]] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_new: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class EnrichmentRun(Base):
    __tablename__ = "enrichment_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contacts.id"))
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"))
    ran_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    result_summary: Mapped[Optional[str]] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
