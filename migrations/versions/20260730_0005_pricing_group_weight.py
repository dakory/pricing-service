"""Rename portfolio weight to pricing-group weight.

Revision ID: 20260730_0005
Revises: 20260730_0004
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260730_0005"
down_revision = "20260730_0004"
branch_labels = None
depends_on = None


def renamed(settings: dict | None) -> dict:
    """Return settings with the obsolete portfolio key renamed."""

    values = dict(settings or {})
    if "portfolio_weight" in values:
        values["pricing_group_weight"] = values.pop("portfolio_weight")
    return values


def upgrade() -> None:
    """Rename the weight key in every configuration inheritance level."""

    bind = op.get_bind()
    metadata = sa.MetaData()
    settings = sa.Table("settings", metadata, autoload_with=bind)
    properties = sa.Table("properties", metadata, autoload_with=bind)
    groups = sa.Table("pricing_groups", metadata, autoload_with=bind)

    global_row = bind.execute(
        sa.select(settings.c.value).where(
            settings.c.key == "pricing_engine_v2"
        )
    ).scalar_one_or_none()
    if global_row is not None:
        bind.execute(
            settings.update()
            .where(settings.c.key == "pricing_engine_v2")
            .values(value=renamed(global_row))
        )
    for table in (properties, groups):
        for row_id, values in bind.execute(
            sa.select(table.c.id, table.c.pricing_settings)
        ):
            bind.execute(
                table.update()
                .where(table.c.id == row_id)
                .values(pricing_settings=renamed(values))
            )


def downgrade() -> None:
    """Refuse to restore obsolete portfolio terminology."""

    raise RuntimeError("pricing_group_weight cannot be renamed safely")
