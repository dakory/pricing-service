"""Baseline the pricing platform schema.

Revision ID: 20260722_0001
Revises:
Create Date: 2026-07-22
"""
from alembic import op

from app.database import Base
import app.models  # noqa: F401

revision = "20260722_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create missing baseline tables while adopting existing MVP schemas."""

    # The MVP originally used Base.metadata.create_all. Keeping the baseline
    # idempotent allows Alembic to adopt those existing databases without
    # deleting imported Hostex data. Subsequent revisions use explicit ops.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Refuse a destructive baseline downgrade."""

    # Dropping the entire baseline would destroy operational data. Restore
    # from backup instead of offering an unsafe automatic downgrade.
    raise RuntimeError("The baseline migration cannot be downgraded safely")
