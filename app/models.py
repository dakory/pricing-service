from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunKind(str, enum.Enum):
    """Enumerate the background workflows recorded by the service."""

    scrape = "scrape"
    import_ = "import"
    optimize = "optimize"
    publish = "publish"
    reconcile = "reconcile"


class RunStatus(str, enum.Enum):
    """Enumerate terminal and active background-run states."""

    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class PricingGroup(Base):
    """Group comparable properties, competitors, and pricing defaults."""

    __tablename__ = "pricing_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    pricing_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    competitor_urls: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    properties: Mapped[list["Property"]] = relationship(back_populates="pricing_group")


class Property(Base):
    """Store one managed property and its Pricing Engine v2 bounds."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    pricing_group_id: Mapped[int] = mapped_column(ForeignKey("pricing_groups.id"))
    name: Mapped[str] = mapped_column(String(200))
    hostex_property_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    hostex_listing_id: Mapped[str] = mapped_column(String(100), unique=True)
    booking_site_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    max_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    rounding_increment: Mapped[int] = mapped_column(Integer, default=50_000)
    pricing_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    weekly_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    monthly_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="property")
    pricing_group: Mapped[PricingGroup] = relationship(back_populates="properties")


class HostexListing(Base):
    """Store a channel listing imported from Hostex."""

    __tablename__ = "hostex_listings"
    __table_args__ = (UniqueConstraint("channel_type", "listing_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"))
    hostex_property_id: Mapped[Optional[int]] = mapped_column(Integer)
    listing_id: Mapped[str] = mapped_column(String(150))
    channel_type: Mapped[str] = mapped_column(String(50))
    channel_account_id: Mapped[Optional[int]] = mapped_column(Integer)
    readonly: Mapped[bool] = mapped_column(Boolean, default=False)
    pricing_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 3))
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class HostexCalendarDay(Base):
    """Store one imported channel-listing calendar day."""

    __tablename__ = "hostex_calendar_days"
    __table_args__ = (UniqueConstraint("listing_id", "channel_type", "stay_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"))
    listing_id: Mapped[str] = mapped_column(String(150))
    channel_type: Mapped[str] = mapped_column(String(50))
    stay_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    inventory: Mapped[Optional[int]] = mapped_column(Integer)
    minimum_stay: Mapped[Optional[int]] = mapped_column(Integer)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Reservation(Base):
    """Store a reservation imported from Hostex."""

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
    """Store one dated competitor price and availability observation."""

    __tablename__ = "competitor_observations"
    __table_args__ = (UniqueConstraint("url", "stay_date", "scraped_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pricing_group_id: Mapped[int] = mapped_column(ForeignKey("pricing_groups.id"))
    url: Mapped[str] = mapped_column(Text)
    stay_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    available: Mapped[bool] = mapped_column(Boolean)
    currency: Mapped[str] = mapped_column(String(3), default="IDR")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    parser_version: Mapped[str] = mapped_column(String(30))


class Recommendation(Base):
    """Store one explainable property-date pricing recommendation."""

    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("property_id", "stay_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    stay_date: Mapped[date] = mapped_column(Date)
    actual_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    recommended_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    published_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    explanation: Mapped[dict] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    property: Mapped[Property] = relationship(back_populates="recommendations")


class Override(Base):
    """Store a hard price lock for a date range."""

    __tablename__ = "overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    reason: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Run(Base):
    """Record execution status and results for an operational workflow."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[RunKind] = mapped_column(Enum(RunKind))
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[Optional[str]] = mapped_column(Text)


class Setting(Base):
    """Store a small JSON-backed application setting."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


class AdminSession(Base):
    """Store a hashed single-administrator browser session."""

    __tablename__ = "admin_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
