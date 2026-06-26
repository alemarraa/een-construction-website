"""Add unsubscribe_token to email_campaigns

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("email_campaigns") as batch_op:
        batch_op.add_column(sa.Column("unsubscribe_token", sa.String(36), nullable=True))
        batch_op.create_index("ix_email_campaigns_unsubscribe_token", ["unsubscribe_token"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("email_campaigns") as batch_op:
        batch_op.drop_index("ix_email_campaigns_unsubscribe_token")
        batch_op.drop_column("unsubscribe_token")
