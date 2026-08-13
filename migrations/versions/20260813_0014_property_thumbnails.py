"""Store Hostex property cover thumbnails.

Revision ID: 20260813_0014
Revises: 20260810_0013
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260813_0014"
down_revision = "20260810_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the optional thumbnail URL without changing imported properties."""

    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("properties")}
    if "thumbnail_url" not in columns:
        with op.batch_alter_table("properties") as batch:
            batch.add_column(sa.Column("thumbnail_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    """Remove the optional thumbnail URL."""

    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("properties")}
    if "thumbnail_url" in columns:
        with op.batch_alter_table("properties") as batch:
            batch.drop_column("thumbnail_url")
