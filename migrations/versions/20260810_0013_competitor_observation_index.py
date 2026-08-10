"""Index dated competitor observations for latest-snapshot queries.

Revision ID: 20260810_0013
Revises: 20260809_0012
"""

from __future__ import annotations

from alembic import op


revision = "20260810_0013"
down_revision = "20260809_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the index used by competitor history and deduplication queries."""

    op.create_index(
        "ix_competitor_observations_listing_date_scraped",
        "competitor_observations",
        ["competitor_listing_id", "stay_date", "scraped_at"],
    )


def downgrade() -> None:
    """Remove the latest-observation query index."""

    op.drop_index(
        "ix_competitor_observations_listing_date_scraped",
        table_name="competitor_observations",
    )
