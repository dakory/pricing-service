"""Store nullable Suggest prices state on date-level assignments."""

from alembic import op
import sqlalchemy as sa

revision = "20260813_0015"
down_revision = "20260813_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable per-date suggestion flags."""
    op.add_column("overrides", sa.Column("suggest_prices", sa.Boolean(), nullable=True))
    op.add_column("price_anchors", sa.Column("suggest_prices", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Remove per-date suggestion flags."""
    op.drop_column("price_anchors", "suggest_prices")
    op.drop_column("overrides", "suggest_prices")
