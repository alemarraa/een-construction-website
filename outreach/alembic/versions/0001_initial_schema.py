"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(300)),
        sa.Column("street_address", sa.String(300), nullable=False),
        sa.Column("address_line2", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("county", sa.String(50), nullable=False),
        sa.Column("zip_code", sa.String(10)),
        sa.Column("state", sa.String(2), server_default="MD"),
        sa.Column("normalized_address", sa.String(400), nullable=False),
        sa.Column("unit_count", sa.Integer),
        sa.Column("unit_count_estimated", sa.Integer),
        sa.Column("unit_count_confidence", sa.Float, server_default="0"),
        sa.Column("unit_count_source", sa.String(200)),
        sa.Column("unit_count_is_estimated", sa.Boolean, server_default="0"),
        sa.Column("property_type", sa.String(50), server_default="unknown"),
        sa.Column("structure_type", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("license_number", sa.String(50)),
        sa.Column("license_status", sa.String(50)),
        sa.Column("license_type", sa.String(200)),
        sa.Column("tax_id", sa.String(50)),
        sa.Column("ownership_type", sa.String(50)),
        sa.Column("owner_entity", sa.String(300)),
        sa.Column("data_confidence", sa.Float, server_default="0"),
        sa.Column("lead_score", sa.Float, server_default="0"),
        sa.Column("qualifies", sa.Boolean, server_default="0"),
        sa.Column("disqualify_reason", sa.String(500)),
        sa.Column("source_url", sa.Text),
        sa.Column("source_checked_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("normalized_address", "county", name="uq_property_addr_county"),
    )
    op.create_index("ix_property_tax_id", "properties", ["tax_id"])
    op.create_index("ix_property_license_num", "properties", ["license_number"])

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("normalized_name", sa.String(300), nullable=False),
        sa.Column("org_type", sa.String(50)),
        sa.Column("website", sa.String(500)),
        sa.Column("website_domain", sa.String(200)),
        sa.Column("phone", sa.String(30)),
        sa.Column("street_address", sa.String(300)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(2)),
        sa.Column("zip_code", sa.String(10)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("normalized_name", name="uq_org_name"),
    )
    op.create_index("ix_org_domain", "organizations", ["website_domain"])

    op.create_table(
        "property_organization_relationships",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("organization_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("is_primary", sa.Boolean, server_default="0"),
        sa.Column("confidence", sa.Float, server_default="0"),
        sa.Column("source", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("full_name", sa.String(200)),
        sa.Column("job_title", sa.String(200)),
        sa.Column("role", sa.String(50), server_default="generic"),
        sa.Column("organization_id", sa.Integer, sa.ForeignKey("organizations.id")),
        sa.Column("email", sa.String(320)),
        sa.Column("email_source", sa.String(200)),
        sa.Column("email_status", sa.String(30), server_default="unknown"),
        sa.Column("email_confidence", sa.Float, server_default="0"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("phone", sa.String(30)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("is_generic_address", sa.Boolean, server_default="0"),
        sa.Column("do_not_contact", sa.Boolean, server_default="0"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email", name="uq_contact_email"),
    )
    op.create_index("ix_contact_org", "contacts", ["organization_id"])

    op.create_table(
        "source_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id")),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("source_url", sa.Text),
        sa.Column("raw_data", sa.Text),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "email_campaigns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id")),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("sequence_number", sa.Integer, server_default="0"),
        sa.Column("lead_score", sa.Float, server_default="0"),
        sa.Column("subject", sa.String(500)),
        sa.Column("body_html", sa.Text),
        sa.Column("body_text", sa.Text),
        sa.Column("personalization_notes", sa.Text),
        sa.Column("dry_run", sa.Boolean, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("queued_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("skip_reason", sa.String(500)),
    )

    op.create_table(
        "email_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("email_campaigns.id"), nullable=False),
        sa.Column("provider_message_id", sa.String(200)),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("attempt_number", sa.Integer, server_default="1"),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("bounced_at", sa.DateTime(timezone=True)),
        sa.Column("bounce_type", sa.String(30)),
        sa.Column("bounce_reason", sa.Text),
        sa.Column("complained_at", sa.DateTime(timezone=True)),
        sa.Column("replied_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "email_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("message_id", sa.Integer, sa.ForeignKey("email_messages.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("provider_data", sa.Text),
    )

    op.create_table(
        "suppression_list",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("domain", sa.String(200)),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("added_at", sa.DateTime(timezone=True)),
        sa.Column("permanent", sa.Boolean, server_default="1"),
        sa.UniqueConstraint("email", name="uq_suppression_email"),
    )

    op.create_table(
        "crawl_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("county", sa.String(50)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("records_fetched", sa.Integer, server_default="0"),
        sa.Column("records_new", sa.Integer, server_default="0"),
        sa.Column("records_updated", sa.Integer, server_default="0"),
        sa.Column("records_skipped", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(30), server_default="running"),
        sa.Column("error_message", sa.Text),
    )

    op.create_table(
        "enrichment_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id")),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id")),
        sa.Column("ran_at", sa.DateTime(timezone=True)),
        sa.Column("success", sa.Boolean, server_default="0"),
        sa.Column("result_summary", sa.Text),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("detail", sa.Text),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for table in [
        "audit_logs", "enrichment_runs", "crawl_runs", "suppression_list",
        "email_events", "email_messages", "email_campaigns", "source_records",
        "contacts", "property_organization_relationships", "organizations", "properties",
    ]:
        op.drop_table(table)
