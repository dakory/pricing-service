"""Unify market snapshots and fallback/manual date anchors.

Revision ID: 20260809_0011
Revises: 20260805_0010
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = "20260809_0011"
down_revision = "20260805_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Copy existing market snapshots into the generic anchor table."""

    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "price_anchors" not in tables:
        op.create_table(
            "price_anchors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("property_id", sa.Integer(), nullable=False),
            sa.Column("stay_date", sa.Date(), nullable=False),
            sa.Column("source_type", sa.String(40), nullable=False),
            sa.Column("source_price", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
            sa.Column("source_metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
            sa.UniqueConstraint(
                "property_id", "stay_date", name="uq_price_anchor_property_date"
            ),
        )
    if "market_price_snapshots" not in tables:
        return

    metadata = sa.MetaData()
    old = sa.Table("market_price_snapshots", metadata, autoload_with=bind)
    new = sa.Table("price_anchors", metadata, autoload_with=bind)
    for row in bind.execute(sa.select(old)).mappings():
        observed_at = row["observed_at"]
        metadata_value = {
            "competitor_count": row["competitor_count"],
            "observed_at": observed_at.isoformat() if observed_at else None,
        }
        bind.execute(
            new.insert().values(
                id=row["id"],
                property_id=row["property_id"],
                stay_date=row["stay_date"],
                source_type="airbnb_market_median",
                source_price=row["guest_market_median"],
                currency="IDR",
                source_metadata=metadata_value,
                created_at=observed_at or datetime.now(timezone.utc),
                updated_at=observed_at or datetime.now(timezone.utc),
            )
        )
    op.drop_table("market_price_snapshots")


def downgrade() -> None:
    """Do not discard generic anchors during downgrade."""

    raise RuntimeError("Downgrading price anchors requires a reviewed data migration")
