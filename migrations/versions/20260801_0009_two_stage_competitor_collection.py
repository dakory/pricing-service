"""Support two-stage competitor calendar and quote collection.

Revision ID: 20260801_0009
Revises: 20260730_0008
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op


revision = "20260801_0009"
down_revision = "20260730_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Migrate observations and make stay quotes independently reusable."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    observation_columns = {
        item["name"] for item in inspector.get_columns("competitor_observations")
    }
    if "bookable" not in observation_columns:
        op.add_column(
            "competitor_observations",
            sa.Column(
                "bookable", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
    if "collection_mode" not in observation_columns:
        op.add_column(
            "competitor_observations",
            sa.Column(
                "collection_mode",
                sa.String(length=20),
                nullable=False,
                server_default="precise",
            ),
        )
    if "available_for_checkin" in observation_columns:
        op.execute(
            "UPDATE competitor_observations "
            "SET bookable = available_for_checkin"
        )

    quote_columns = {
        item["name"] for item in inspector.get_columns("competitor_stay_quotes")
    }
    if "competitor_observation_id" in quote_columns:
        _migrate_legacy_quotes(bind)

    if "competitor_price_targets" not in inspector.get_table_names():
        _create_price_targets()
    if "competitor_scrape_batches" not in inspector.get_table_names():
        _create_scrape_batches()

    if "available_for_checkin" in observation_columns:
        op.drop_column("competitor_observations", "available_for_checkin")
    if "available" in observation_columns:
        op.drop_column("competitor_observations", "available")


def _create_quote_table() -> None:
    """Create the independently reusable quote table."""

    op.create_table(
        "competitor_stay_quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scrape_run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column(
            "competitor_listing_id",
            sa.Integer(),
            sa.ForeignKey("competitor_listings.id"),
            nullable=False,
        ),
        sa.Column("quote_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=False),
        sa.Column("adults", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IDR"),
        sa.Column("total_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parser_version", sa.String(length=30), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "check_in_date",
            "check_out_date",
            "adults",
            "currency",
            name="uq_competitor_stay_quote_interval",
        ),
    )


def _migrate_legacy_quotes(bind) -> None:
    """Copy legacy observation-bound quotes before dropping their table."""

    op.rename_table("competitor_stay_quotes", "competitor_stay_quotes_legacy")
    _create_quote_table()
    metadata = sa.MetaData()
    legacy_quotes = sa.Table(
        "competitor_stay_quotes_legacy", metadata, autoload_with=bind
    )
    new_quotes = sa.Table(
        "competitor_stay_quotes", metadata, autoload_with=bind
    )
    observations = sa.Table(
        "competitor_observations", metadata, autoload_with=bind
    )
    legacy_rows = bind.execute(
        sa.select(
            legacy_quotes.c.id,
            legacy_quotes.c.check_out_date,
            legacy_quotes.c.total_price,
            legacy_quotes.c.raw,
            observations.c.scrape_run_id,
            observations.c.competitor_listing_id,
            observations.c.stay_date,
            observations.c.currency,
            observations.c.scraped_at,
            observations.c.parser_version,
        ).join(
            observations,
            observations.c.id == legacy_quotes.c.competitor_observation_id,
        )
    )
    for row in legacy_rows:
        if row.scrape_run_id is None:
            continue
        bind.execute(
            new_quotes.insert().values(
                scrape_run_id=row.scrape_run_id,
                competitor_listing_id=row.competitor_listing_id,
                quote_id=f"legacy_{row.id}",
                check_in_date=row.stay_date,
                check_out_date=row.check_out_date,
                adults=4,
                currency=row.currency,
                total_price=row.total_price,
                scraped_at=row.scraped_at,
                parser_version=row.parser_version,
                raw=row.raw or {},
            )
        )
    op.drop_table("competitor_stay_quotes_legacy")


def _create_price_targets() -> None:
    """Create persisted target calculation plans."""

    op.create_table(
        "competitor_price_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scrape_run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column(
            "competitor_listing_id",
            sa.Integer(),
            sa.ForeignKey("competitor_listings.id"),
            nullable=False,
        ),
        sa.Column("stay_date", sa.Date(), nullable=False),
        sa.Column("minimum_stay", sa.Integer(), nullable=True),
        sa.Column("collection_mode", sa.String(length=20), nullable=False),
        sa.Column("price_method", sa.String(length=40), nullable=False),
        sa.Column("quote_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "stay_date",
            name="uq_competitor_price_target_run_date",
        ),
    )


def _create_scrape_batches() -> None:
    """Create idempotent Lambda batch tracking."""

    op.create_table(
        "competitor_scrape_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scrape_run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column(
            "competitor_listing_id",
            sa.Integer(),
            sa.ForeignKey("competitor_listings.id"),
            nullable=False,
        ),
        sa.Column("operation", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("expected_quote_ids", sa.JSON(), nullable=False),
        sa.Column("quote_requests", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Restore observation-bound quotes while preserving raw totals."""

    bind = op.get_bind()
    op.add_column(
        "competitor_observations",
        sa.Column(
            "available", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "competitor_observations",
        sa.Column(
            "available_for_checkin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(
        "UPDATE competitor_observations SET available = bookable, "
        "available_for_checkin = bookable"
    )

    op.rename_table("competitor_stay_quotes", "competitor_stay_quotes_v2")
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
    metadata = sa.MetaData()
    observations = sa.Table(
        "competitor_observations", metadata, autoload_with=bind
    )
    targets = sa.Table(
        "competitor_price_targets", metadata, autoload_with=bind
    )
    quotes_v2 = sa.Table(
        "competitor_stay_quotes_v2", metadata, autoload_with=bind
    )
    legacy_quotes = sa.Table(
        "competitor_stay_quotes", metadata, autoload_with=bind
    )
    target_rows = list(bind.execute(sa.select(targets)))
    observations_by_key = {
        (row.scrape_run_id, row.competitor_listing_id, row.stay_date): row.id
        for row in bind.execute(sa.select(observations))
    }
    for quote in bind.execute(sa.select(quotes_v2)):
        target = next(
            (
                item
                for item in target_rows
                if item.scrape_run_id == quote.scrape_run_id
                and item.competitor_listing_id == quote.competitor_listing_id
                and quote.quote_id in (item.quote_ids or [])
            ),
            None,
        )
        if target is None:
            continue
        observation_id = observations_by_key.get(
            (
                target.scrape_run_id,
                target.competitor_listing_id,
                target.stay_date,
            )
        )
        if observation_id is None:
            continue
        bind.execute(
            legacy_quotes.insert().values(
                competitor_observation_id=observation_id,
                check_out_date=quote.check_out_date,
                stay_nights=(quote.check_out_date - quote.check_in_date).days,
                total_price=quote.total_price,
                raw=quote.raw or {},
            )
        )

    op.drop_table("competitor_stay_quotes_v2")
    op.drop_table("competitor_price_targets")
    op.drop_table("competitor_scrape_batches")
    op.drop_column("competitor_observations", "collection_mode")
    op.drop_column("competitor_observations", "bookable")
