"""Repair the PostgreSQL sequence after copying explicit anchor IDs.

Revision ID: 20260809_0012
Revises: 20260809_0011
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260809_0012"
down_revision = "20260809_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Advance the anchor ID sequence beyond migrated rows."""

    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('price_anchors', 'id'),
                COALESCE((SELECT MAX(id) FROM price_anchors), 1),
                EXISTS (SELECT 1 FROM price_anchors)
            )
            """
        )
    )


def downgrade() -> None:
    """Leave the repaired sequence unchanged on downgrade."""

    pass
