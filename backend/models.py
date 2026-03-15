from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


def json_type():
    return JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ListingSnapshot(Base, TimestampMixin):
    __tablename__ = "listing_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    marketplace: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_listing_id: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    available_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    competitor_prices: Mapped[list[float]] = mapped_column(json_type(), nullable=False, default=list)
    views_last_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales_last_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attributes: Mapped[dict] = mapped_column(json_type(), nullable=False, default=dict)


class PricingDecision(Base, TimestampMixin):
    __tablename__ = "pricing_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    min_margin_percent: Mapped[float] = mapped_column(Float, nullable=False)
    target_position: Mapped[str] = mapped_column(String(50), nullable=False)
    recommended_price: Mapped[float] = mapped_column(Float, nullable=False)
    expected_margin_percent: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    rationale: Mapped[list[str]] = mapped_column(json_type(), nullable=False, default=list)


class ListingEvaluation(Base, TimestampMixin):
    __tablename__ = "listing_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    business_goal: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    actions: Mapped[list[str]] = mapped_column(json_type(), nullable=False, default=list)
    risks: Mapped[list[str]] = mapped_column(json_type(), nullable=False, default=list)
    pricing_source: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)


class BuyerQuestionLog(Base, TimestampMixin):
    __tablename__ = "buyer_question_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    buyer_question: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(50), nullable=False)
    reply: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_actions: Mapped[list[str]] = mapped_column(json_type(), nullable=False, default=list)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
