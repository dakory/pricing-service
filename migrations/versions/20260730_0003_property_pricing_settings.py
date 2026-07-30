"""Add property-level pricing setting overrides.

Revision ID: 20260730_0003
Revises: 20260730_0002
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260730_0003"
down_revision = "20260730_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add an initially empty JSON override map to every property."""

    existing = {
        column["name"]
        for column in inspect(op.get_bind()).get_columns("properties")
    }
    if "pricing_settings" in existing:
        return
    with op.batch_alter_table("properties") as batch:
        batch.add_column(
            sa.Column(
                "pricing_settings",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )


def downgrade() -> None:
    """Remove property-level pricing overrides."""

    with op.batch_alter_table("properties") as batch:
        batch.drop_column("pricing_settings")
