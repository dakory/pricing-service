"""Store raw competitor stay quotes before backend normalization.

Revision ID: 20260730_0007
Revises: 20260730_0006
Create Date: 2026-07-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "20260730_0007"
down_revision = "20260730_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the raw stay quote audit table."""

    bind = op.get_bind()
    if "competitor_stay_quotes" in inspect(bind).get_table_names():
        return
    op.create_table(
        "competitor_stay_quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "competitor_observation_id",
            sa.Integer(),
            sa.ForeignKey("competitor_observations.id"),
            nullable=False,
        ),
        sa.Column("check_out_date", sa.Date(), nullable=False),
        sa.Column("stay_nights", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("accommodation_subtotal", sa.Numeric(14, 2), nullable=True),
        sa.Column("cleaning_fee", sa.Numeric(14, 2), nullable=True),
        sa.Column("taxes", sa.Numeric(14, 2), nullable=True),
        sa.Column("other_excluded_fees", sa.Numeric(14, 2), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "competitor_observation_id",
            "check_out_date",
            name="uq_competitor_stay_quote_checkout",
        ),
    )


def downgrade() -> None:
    """Drop raw stay quotes while retaining normalized observations."""

    op.drop_table("competitor_stay_quotes")
