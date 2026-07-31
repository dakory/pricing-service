"""Normalize competitor listings and asynchronous observations.

Revision ID: 20260730_0006
Revises: 20260730_0005
Create Date: 2026-07-30
"""

import re

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "20260730_0006"
down_revision = "20260730_0005"
branch_labels = None
depends_on = None


def external_listing_id(url: str) -> str:
    """Extract a stable external identifier from a migrated listing URL."""

    match = re.search(r"/rooms/(\d+)", url)
    return match.group(1) if match else url.rstrip("/").rsplit("/", 1)[-1][:150]


def upgrade() -> None:
    """Create normalized listings and migrate all existing observations."""

    bind = op.get_bind()
    if "competitor_listings" in inspect(bind).get_table_names():
        return
    op.create_table(
        "competitor_listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pricing_group_id",
            sa.Integer(),
            sa.ForeignKey("pricing_groups.id"),
            nullable=False,
        ),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("external_listing_id", sa.String(length=150), nullable=False),
        sa.Column("current_minimum_stay", sa.Integer(), nullable=True),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "pricing_group_id",
            "canonical_url",
            name="uq_competitor_listing_group_url",
        ),
    )
    metadata = sa.MetaData()
    groups = sa.Table("pricing_groups", metadata, autoload_with=bind)
    listings = sa.Table("competitor_listings", metadata, autoload_with=bind)
    observations = sa.Table(
        "competitor_observations", metadata, autoload_with=bind
    )
    pairs: set[tuple[int, str]] = set()
    for group_id, urls in bind.execute(
        sa.select(groups.c.id, groups.c.competitor_urls)
    ):
        pairs.update((group_id, url) for url in (urls or []))
    pairs.update(
        bind.execute(
            sa.select(
                observations.c.pricing_group_id, observations.c.url
            ).distinct()
        )
    )
    for group_id, url in sorted(pairs):
        bind.execute(
            listings.insert().values(
                pricing_group_id=group_id,
                canonical_url=url,
                external_listing_id=external_listing_id(url),
            )
        )

    with op.batch_alter_table("competitor_observations") as batch:
        batch.add_column(
            sa.Column("competitor_listing_id", sa.Integer(), nullable=True)
        )
        batch.add_column(sa.Column("scrape_run_id", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column(
                "available_for_checkin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(sa.Column("minimum_stay", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column(
                "price_method",
                sa.String(length=40),
                nullable=False,
                server_default="legacy",
            )
        )

    observations = sa.Table(
        "competitor_observations", sa.MetaData(), autoload_with=bind
    )
    listings = sa.Table(
        "competitor_listings", sa.MetaData(), autoload_with=bind
    )
    for listing_id, group_id, url in bind.execute(
        sa.select(
            listings.c.id,
            listings.c.pricing_group_id,
            listings.c.canonical_url,
        )
    ):
        bind.execute(
            observations.update()
            .where(
                observations.c.pricing_group_id == group_id,
                observations.c.url == url,
            )
            .values(competitor_listing_id=listing_id)
        )

    with op.batch_alter_table("competitor_observations") as batch:
        batch.alter_column("competitor_listing_id", nullable=False)
        batch.create_foreign_key(
            "fk_competitor_observation_listing",
            "competitor_listings",
            ["competitor_listing_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_competitor_observation_run",
            "runs",
            ["scrape_run_id"],
            ["id"],
        )
        batch.create_unique_constraint(
            "uq_competitor_observation_run_date",
            ["scrape_run_id", "competitor_listing_id", "stay_date"],
        )
        batch.drop_column("pricing_group_id")
        batch.drop_column("url")


def downgrade() -> None:
    """Refuse a lossy downgrade to denormalized competitor URLs."""

    raise RuntimeError("Normalized competitor observations cannot be downgraded safely")
