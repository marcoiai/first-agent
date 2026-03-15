"""add marketplace to listing snapshots

Revision ID: 20260314_0002
Revises: 20260314_0001
Create Date: 2026-03-14 18:45:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260314_0002"
down_revision = "20260314_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listing_snapshots",
        sa.Column("marketplace", sa.String(length=50), nullable=True),
    )
    op.execute(
        "UPDATE listing_snapshots SET marketplace = 'mercadolivre' "
        "WHERE marketplace IS NULL"
    )
    with op.batch_alter_table("listing_snapshots") as batch_op:
        batch_op.alter_column("marketplace", existing_type=sa.String(length=50), nullable=False)
    op.create_index("ix_listing_snapshots_marketplace", "listing_snapshots", ["marketplace"])


def downgrade() -> None:
    op.drop_index("ix_listing_snapshots_marketplace", table_name="listing_snapshots")
    op.drop_column("listing_snapshots", "marketplace")
