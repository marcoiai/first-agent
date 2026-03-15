"""create initial tables

Revision ID: 20260314_0001
Revises: None
Create Date: 2026-03-14 18:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260314_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_type = sa.JSON()
    if op.get_bind().dialect.name == "postgresql":
        json_type = postgresql.JSONB(astext_type=sa.Text())

    op.create_table(
        "listing_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_listing_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("available_stock", sa.Integer(), nullable=False),
        sa.Column("competitor_prices", json_type, nullable=False),
        sa.Column("views_last_7d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_last_30d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attributes", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_listing_snapshots_external_listing_id", "listing_snapshots", ["external_listing_id"])
    op.create_index("ix_listing_snapshots_category", "listing_snapshots", ["category"])

    op.create_table(
        "pricing_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("listing_snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("min_margin_percent", sa.Float(), nullable=False),
        sa.Column("target_position", sa.String(length=50), nullable=False),
        sa.Column("recommended_price", sa.Float(), nullable=False),
        sa.Column("expected_margin_percent", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("rationale", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pricing_decisions_listing_snapshot_id", "pricing_decisions", ["listing_snapshot_id"])

    op.create_table(
        "listing_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("listing_snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("business_goal", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("actions", json_type, nullable=False),
        sa.Column("risks", json_type, nullable=False),
        sa.Column("pricing_source", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_listing_evaluations_listing_snapshot_id", "listing_evaluations", ["listing_snapshot_id"])

    op.create_table(
        "buyer_question_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("listing_snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("buyer_question", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(length=50), nullable=False),
        sa.Column("reply", sa.Text(), nullable=False),
        sa.Column("follow_up_actions", json_type, nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_buyer_question_logs_listing_snapshot_id", "buyer_question_logs", ["listing_snapshot_id"])


def downgrade() -> None:
    op.drop_index("ix_buyer_question_logs_listing_snapshot_id", table_name="buyer_question_logs")
    op.drop_table("buyer_question_logs")
    op.drop_index("ix_listing_evaluations_listing_snapshot_id", table_name="listing_evaluations")
    op.drop_table("listing_evaluations")
    op.drop_index("ix_pricing_decisions_listing_snapshot_id", table_name="pricing_decisions")
    op.drop_table("pricing_decisions")
    op.drop_index("ix_listing_snapshots_category", table_name="listing_snapshots")
    op.drop_index("ix_listing_snapshots_external_listing_id", table_name="listing_snapshots")
    op.drop_table("listing_snapshots")
