"""Unify manual anchors and hard overrides into price assignments.

Revision ID: 20260813_0016
Revises: 20260813_0015
"""

from alembic import op
import sqlalchemy as sa

revision = "20260813_0016"
down_revision = "20260813_0015"
branch_labels = None
depends_on = None


def upgrade():
    """Create the unified assignment table and copy legacy rows."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "price_assignments" not in inspector.get_table_names():
        op.create_table(
            "price_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
            sa.Column("stay_date", sa.Date(), nullable=False),
            sa.Column("price", sa.Numeric(14, 2), nullable=False),
            sa.Column("suggest_prices", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("reason", sa.String(300), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("property_id", "stay_date", name="uq_price_assignment_property_date"),
        )

    # Newest assignment wins when legacy tables overlap.
    op.execute(sa.text("""
        INSERT INTO price_assignments
            (property_id, stay_date, price, suggest_prices, reason, created_at, updated_at)
        SELECT property_id, stay_date, source_price, COALESCE(suggest_prices, TRUE),
               COALESCE(source_metadata->>'reason', 'Migrated manual base price'),
               created_at, updated_at
        FROM price_anchors a
        WHERE NOT EXISTS (
            SELECT 1 FROM price_assignments p
            WHERE p.property_id = a.property_id AND p.stay_date = a.stay_date
        )
    """))
    op.execute(sa.text("""
        INSERT INTO price_assignments
            (property_id, stay_date, price, suggest_prices, reason, created_at, updated_at)
        SELECT property_id, start_date, price, FALSE, reason, created_at, created_at
        FROM overrides o
        WHERE price IS NOT NULL
          AND start_date = end_date
          AND NOT EXISTS (
            SELECT 1 FROM price_assignments p
            WHERE p.property_id = o.property_id AND p.stay_date = o.start_date
        )
    """))


def downgrade():
    """Drop the unified table while retaining legacy tables."""

    op.drop_table("price_assignments")
