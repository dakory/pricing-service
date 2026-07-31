"""Persist partial competitor scrape results.

Revision ID: 20260730_0008
Revises: 20260730_0007
Create Date: 2026-07-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "20260730_0008"
down_revision = "20260730_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add partial run status and date-scoped collection errors."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TYPE runstatus ADD VALUE IF NOT EXISTS "
            "'partially_succeeded'"
        )
    if "competitor_date_errors" in inspect(bind).get_table_names():
        return
    op.create_table(
        "competitor_date_errors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "scrape_run_id",
            sa.Integer(),
            sa.ForeignKey("runs.id"),
            nullable=False,
        ),
        sa.Column(
            "competitor_listing_id",
            sa.Integer(),
            sa.ForeignKey("competitor_listings.id"),
            nullable=False,
        ),
        sa.Column("stay_date", sa.Date(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "stay_date",
            name="uq_competitor_date_error_run_date",
        ),
    )


def downgrade() -> None:
    """Remove dated errors while retaining the PostgreSQL enum value."""

    op.drop_table("competitor_date_errors")
