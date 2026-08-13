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
    partially_succeeded = "partially_succeeded"
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
    competitor_listings: Mapped[list["CompetitorListing"]] = relationship(
        back_populates="pricing_group"
    )


class Property(Base):
    """Store one managed property and its Pricing Engine v2 bounds."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    pricing_group_id: Mapped[int] = mapped_column(ForeignKey("pricing_groups.id"))
    name: Mapped[str] = mapped_column(String(200))
    hostex_property_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000))
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


class CompetitorListing(Base):
    """Store one normalized competitor listing monitored for a pricing group."""

    __tablename__ = "competitor_listings"
    __table_args__ = (UniqueConstraint("pricing_group_id", "canonical_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pricing_group_id: Mapped[int] = mapped_column(ForeignKey("pricing_groups.id"))
    canonical_url: Mapped[str] = mapped_column(Text)
    external_listing_id: Mapped[str] = mapped_column(String(150))
    current_minimum_stay: Mapped[Optional[int]] = mapped_column(Integer)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    pricing_group: Mapped[PricingGroup] = relationship(
        back_populates="competitor_listings"
    )
    observations: Mapped[list["CompetitorObservation"]] = relationship(
        back_populates="competitor_listing"
    )


class CompetitorObservation(Base):
    """Store one dated competitor price and availability observation."""

    __tablename__ = "competitor_observations"
    __table_args__ = (
        UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "stay_date",
            name="uq_competitor_observation_run_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_listing_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_listings.id")
    )
    scrape_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("runs.id"))
    stay_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    bookable: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_stay: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="IDR")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    parser_version: Mapped[str] = mapped_column(String(30))
    price_method: Mapped[str] = mapped_column(String(40), default="unknown")
    collection_mode: Mapped[str] = mapped_column(String(20), default="precise")

    competitor_listing: Mapped[CompetitorListing] = relationship(
        back_populates="observations"
    )

    @property
    def available(self) -> bool:
        """Expose the legacy availability name during the transition."""

        return self.bookable

    @available.setter
    def available(self, value: bool) -> None:
        self.bookable = value

    @property
    def available_for_checkin(self) -> bool:
        """Expose the legacy check-in name during the transition."""

        return self.bookable

    @available_for_checkin.setter
    def available_for_checkin(self, value: bool) -> None:
        self.bookable = value


class CompetitorStayQuote(Base):
    """Store one raw stay quote reusable by multiple target dates."""

    __tablename__ = "competitor_stay_quotes"
    __table_args__ = (
        UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "check_in_date",
            "check_out_date",
            "adults",
            "currency",
            name="uq_competitor_stay_quote_interval",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    competitor_listing_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_listings.id")
    )
    quote_id: Mapped[str] = mapped_column(String(64), unique=True)
    check_in_date: Mapped[date] = mapped_column(Date)
    check_out_date: Mapped[date] = mapped_column(Date)
    adults: Mapped[int] = mapped_column(Integer, default=4)
    currency: Mapped[str] = mapped_column(String(3), default="IDR")
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    parser_version: Mapped[str] = mapped_column(String(30))
    raw: Mapped[dict] = mapped_column(JSON, default=dict)


class CompetitorPriceTarget(Base):
    """Store the backend plan used to calculate one dated competitor price."""

    __tablename__ = "competitor_price_targets"
    __table_args__ = (
        UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "stay_date",
            name="uq_competitor_price_target_run_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    competitor_listing_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_listings.id")
    )
    stay_date: Mapped[date] = mapped_column(Date)
    minimum_stay: Mapped[Optional[int]] = mapped_column(Integer)
    collection_mode: Mapped[str] = mapped_column(String(20))
    price_method: Mapped[str] = mapped_column(String(40))
    quote_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error: Mapped[Optional[str]] = mapped_column(Text)


class CompetitorScrapeBatch(Base):
    """Track one idempotent calendar or quote Lambda invocation."""

    __tablename__ = "competitor_scrape_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    competitor_listing_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_listings.id")
    )
    operation: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    expected_quote_ids: Mapped[list] = mapped_column(JSON, default=list)
    quote_requests: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )


class CompetitorDateError(Base):
    """Store one date-specific collection failure for a scrape run."""

    __tablename__ = "competitor_date_errors"
    __table_args__ = (
        UniqueConstraint(
            "scrape_run_id",
            "competitor_listing_id",
            "stay_date",
            name="uq_competitor_date_error_run_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    competitor_listing_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_listings.id")
    )
    stay_date: Mapped[date] = mapped_column(Date)
    code: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500))


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


class PriceAnchor(Base):
    """Persist one stable date-level input for pricing calculations."""

    __tablename__ = "price_anchors"
    __table_args__ = (
        UniqueConstraint(
            "property_id",
            "stay_date",
            name="uq_price_anchor_property_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    stay_date: Mapped[date] = mapped_column(Date)
    source_type: Mapped[str] = mapped_column(String(40))
    source_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="IDR")
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AdminSession(Base):
    """Store a hashed single-administrator browser session."""

    __tablename__ = "admin_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
