"""Group comparable properties and competitors.

Revision ID: 20260730_0004
Revises: 20260730_0003
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260730_0004"
down_revision = "20260730_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create a default group and migrate property-level competitor data."""

    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    property_columns = {
        column["name"] for column in inspector.get_columns("properties")
    }

    if "pricing_groups" not in tables:
        op.create_table(
            "pricing_groups",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False, unique=True),
            sa.Column("pricing_settings", sa.JSON(), nullable=False),
            sa.Column("competitor_urls", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        metadata = sa.MetaData()
        groups = sa.Table("pricing_groups", metadata, autoload_with=bind)
        properties = sa.Table("properties", metadata, autoload_with=bind)
        existing_urls = []
        if "competitor_urls" in property_columns:
            for urls in bind.execute(sa.select(properties.c.competitor_urls)).scalars():
                existing_urls.extend(urls or [])
        result = bind.execute(
            groups.insert().values(
                name="Default pricing group",
                pricing_settings={},
                competitor_urls=list(dict.fromkeys(existing_urls)),
                created_at=sa.func.now(),
            )
        )
        default_group_id = result.inserted_primary_key[0]
    else:
        groups = sa.Table(
            "pricing_groups", sa.MetaData(), autoload_with=bind
        )
        default_group_id = bind.scalar(
            sa.select(groups.c.id).order_by(groups.c.id).limit(1)
        )

    if "pricing_group_id" not in property_columns:
        with op.batch_alter_table("properties") as batch:
            batch.add_column(
                sa.Column("pricing_group_id", sa.Integer(), nullable=True)
            )
            batch.create_foreign_key(
                "fk_properties_pricing_group",
                "pricing_groups",
                ["pricing_group_id"],
                ["id"],
            )
        bind.execute(
            sa.text(
                "UPDATE properties SET pricing_group_id = :pricing_group_id"
            ),
            {"pricing_group_id": default_group_id},
        )
        with op.batch_alter_table("properties") as batch:
            batch.alter_column("pricing_group_id", nullable=False)

    observation_columns = {
        column["name"]
        for column in inspect(bind).get_columns("competitor_observations")
    }
    if "pricing_group_id" not in observation_columns:
        with op.batch_alter_table("competitor_observations") as batch:
            batch.add_column(
                sa.Column("pricing_group_id", sa.Integer(), nullable=True)
            )
            batch.create_foreign_key(
                "fk_competitor_observations_pricing_group",
                "pricing_groups",
                ["pricing_group_id"],
                ["id"],
            )
        bind.execute(
            sa.text(
                "UPDATE competitor_observations "
                "SET pricing_group_id = ("
                "SELECT pricing_group_id FROM properties "
                "WHERE properties.id = competitor_observations.property_id)"
            )
        )
        with op.batch_alter_table("competitor_observations") as batch:
            batch.alter_column("pricing_group_id", nullable=False)
            batch.drop_column("property_id")

    property_columns = {
        column["name"] for column in inspect(bind).get_columns("properties")
    }
    if "competitor_urls" in property_columns:
        with op.batch_alter_table("properties") as batch:
            batch.drop_column("competitor_urls")


def downgrade() -> None:
    """Refuse to split shared competitors back into property-level lists."""

    raise RuntimeError(
        "Pricing groups cannot be downgraded without choosing competitor mappings"
    )
