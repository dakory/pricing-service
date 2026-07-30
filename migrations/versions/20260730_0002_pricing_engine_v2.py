"""Remove Pricing Engine v1 policy and minimum-stay fields.

Revision ID: 20260730_0002
Revises: 20260722_0001
Create Date: 2026-07-30
"""

from alembic import op
from sqlalchemy import inspect


revision = "20260730_0002"
down_revision = "20260722_0001"
branch_labels = None
depends_on = None


REMOVED_COLUMNS = {
    "properties": [
        "base_price",
        "season_factors",
        "weekday_factors",
        "minimum_stay_rules",
        "orphan_gap_rules",
    ],
    "recommendations": ["minimum_stay", "published_minimum_stay"],
    "overrides": ["minimum_stay"],
}


def upgrade() -> None:
    """Drop fields that no longer belong to Pricing Engine v2."""

    # Recommendations are derived data. V1 explanations must never be shown
    # as V2 results; the next shadow run recreates rows from competitor data.
    op.execute("DELETE FROM recommendations")
    inspector = inspect(op.get_bind())
    for table_name, candidates in REMOVED_COLUMNS.items():
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        columns = [column for column in candidates if column in existing]
        if not columns:
            continue
        with op.batch_alter_table(table_name) as batch:
            for column in columns:
                batch.drop_column(column)


def downgrade() -> None:
    """Refuse to recreate obsolete pricing configuration without valid data."""

    raise RuntimeError(
        "Pricing Engine v1 fields cannot be restored safely; restore a database backup"
    )
