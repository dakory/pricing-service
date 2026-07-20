from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunKind(str, enum.Enum):
    scrape = "scrape"
    import_ = "import"
    optimize = "optimize"
    publish = "publish"
    reconcile = "reconcile"


class RunStatus(str, enum.Enum):
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    hostex_listing_id: Mapped[str] = mapped_column(String(100), unique=True)
    booking_site_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    min_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    max_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    rounding_increment: Mapped[int] = mapped_column(Integer, default=50_000)
    season_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    weekday_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    minimum_stay_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    orphan_gap_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    weekly_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    monthly_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    competitor_urls: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="property")


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("property_id", "hostex_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    hostex_id: Mapped[str] = mapped_column(String(100))
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    booked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="confirmed")


class CompetitorObservation(Base):
    __tablename__ = "competitor_observations"
    __table_args__ = (UniqueConstraint("url", "stay_date", "scraped_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    url: Mapped[str] = mapped_column(Text)
    stay_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    available: Mapped[bool] = mapped_column(Boolean)
    currency: Mapped[str] = mapped_column(String(3), default="IDR")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    parser_version: Mapped[str] = mapped_column(String(30))


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("property_id", "stay_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    stay_date: Mapped[date] = mapped_column(Date)
    actual_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    recommended_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    published_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    minimum_stay: Mapped[int] = mapped_column(Integer, default=1)
    published_minimum_stay: Mapped[Optional[int]] = mapped_column(Integer)
    explanation: Mapped[dict] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    property: Mapped[Property] = relationship(back_populates="recommendations")


class Override(Base):
    __tablename__ = "overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    minimum_stay: Mapped[Optional[int]] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[RunKind] = mapped_column(Enum(RunKind))
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[Optional[str]] = mapped_column(Text)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
