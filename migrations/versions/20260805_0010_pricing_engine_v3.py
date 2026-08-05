"""Replace demand pricing with cached-market and range urgency settings.

Revision ID: 20260805_0010
Revises: 20260801_0009
Create Date: 2026-08-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260805_0010"
down_revision = "20260801_0009"
branch_labels = None
depends_on = None


DEMAND_KEYS = {
    "competitor_weight",
    "pricing_group_weight",
    "neutral_demand_score",
    "demand_adjustment_slope",
    "minimum_demand_adjustment",
    "maximum_demand_adjustment",
    "demand_adjustment_enabled",
}


def urgency_ranges(values: list[dict]) -> list[dict]:
    """Convert cumulative v2 maximum-day tiers into disjoint v3 ranges."""

    if not values:
        return []
    if all("minimum_days" in item for item in values):
        return [
            {
                "minimum_days": int(item["minimum_days"]),
                "maximum_days": int(item["maximum_days"]),
                "adjustment": float(item["adjustment"]),
            }
            for item in sorted(values, key=lambda item: int(item["minimum_days"]))
        ]
    result = []
    minimum = 0
    for item in sorted(values, key=lambda item: int(item["maximum_days"])):
        maximum = int(item["maximum_days"])
        result.append(
            {
                "minimum_days": minimum,
                "maximum_days": maximum,
                "adjustment": float(item["adjustment"]),
            }
        )
        minimum = maximum + 1
    return result


def cleaned(values: dict | None) -> dict:
    """Remove demand keys and convert the old market offset and urgency shape."""

    result = dict(values or {})
    for key in DEMAND_KEYS:
        result.pop(key, None)
    if "market_price_adjustment" in result:
        result["market_positioning_factor"] = 1 + float(
            result.pop("market_price_adjustment")
        )
    if "urgency_adjustments" in result:
        result["urgency_adjustments"] = urgency_ranges(
            result["urgency_adjustments"]
        )
    return result


def merged_urgency(parent: list[dict], override: list[dict]) -> list[dict]:
    """Overlay old partial ranges without leaving overlapping v3 ranges."""

    result = [dict(item) for item in parent]
    for replacement in override:
        result = [
            item
            for item in result
            if int(item["maximum_days"]) < int(replacement["minimum_days"])
            or int(item["minimum_days"]) > int(replacement["maximum_days"])
        ]
        result.append(dict(replacement))
    return sorted(result, key=lambda item: int(item["minimum_days"]))


def upgrade() -> None:
    """Create market snapshots and clean inherited pricing JSON settings."""

    bind = op.get_bind()
    if "market_price_snapshots" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "market_price_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("property_id", sa.Integer(), nullable=False),
            sa.Column("stay_date", sa.Date(), nullable=False),
            sa.Column("guest_market_median", sa.Numeric(14, 2), nullable=False),
            sa.Column("competitor_count", sa.Integer(), nullable=False),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
            sa.UniqueConstraint(
                "property_id",
                "stay_date",
                name="uq_market_price_snapshot_property_date",
            ),
        )
    metadata = sa.MetaData()
    settings = sa.Table("settings", metadata, autoload_with=bind)
    groups = sa.Table("pricing_groups", metadata, autoload_with=bind)
    properties = sa.Table("properties", metadata, autoload_with=bind)

    global_values = bind.execute(
        sa.select(settings.c.value).where(settings.c.key == "pricing_engine_v2")
    ).scalar_one_or_none()
    global_values = cleaned(global_values)
    bind.execute(
        settings.update()
        .where(settings.c.key == "pricing_engine_v2")
        .values(value=global_values)
    )

    group_values = {}
    for row_id, values in bind.execute(
        sa.select(groups.c.id, groups.c.pricing_settings)
    ):
        value = cleaned(values)
        if "urgency_adjustments" in value:
            value["urgency_adjustments"] = merged_urgency(
                global_values.get("urgency_adjustments", []),
                value["urgency_adjustments"],
            )
        group_values[row_id] = value
        bind.execute(
            groups.update().where(groups.c.id == row_id).values(pricing_settings=value)
        )

    property_group = {
        row_id: group_id
        for row_id, group_id in bind.execute(
            sa.select(properties.c.id, properties.c.pricing_group_id)
        )
    }
    for row_id, values in bind.execute(
        sa.select(properties.c.id, properties.c.pricing_settings)
    ):
        value = cleaned(values)
        if "urgency_adjustments" in value:
            parent = group_values.get(property_group[row_id], global_values)
            value["urgency_adjustments"] = merged_urgency(
                parent.get("urgency_adjustments", []),
                value["urgency_adjustments"],
            )
        bind.execute(
            properties.update().where(properties.c.id == row_id).values(pricing_settings=value)
        )


def downgrade() -> None:
    """Drop v3 snapshots; restoring demand settings would lose user intent."""

    op.drop_table("market_price_snapshots")
