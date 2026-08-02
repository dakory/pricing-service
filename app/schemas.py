from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PropertyBase(BaseModel):
    """Define shared property pricing-policy fields."""

    name: str
    pricing_group_id: int
    hostex_listing_id: str
    booking_site_listing_id: str | None = None
    active: bool = True
    min_price: Decimal = Field(gt=0)
    max_price: Decimal = Field(gt=0)
    rounding_increment: int = Field(default=50_000, gt=0)
    pricing_settings: dict = Field(default_factory=dict)
    weekly_discount: Decimal | None = None
    monthly_discount: Decimal | None = None

    @model_validator(mode="after")
    def valid_bounds(self):
        """Require minimum price to remain below maximum price."""

        if self.min_price > self.max_price:
            raise ValueError("price bounds must satisfy min <= max")
        return self


class PropertyCreate(PropertyBase):
    """Validate creation of a managed property."""

    pass


class PropertyUpdate(BaseModel):
    """Validate a partial update to a property pricing policy."""

    name: str | None = None
    active: bool | None = None
    pricing_group_id: int | None = None
    min_price: Decimal | None = Field(default=None, gt=0)
    max_price: Decimal | None = Field(default=None, gt=0)
    rounding_increment: int | None = Field(default=None, gt=0)
    pricing_settings: dict | None = None
    weekly_discount: Decimal | None = None
    monthly_discount: Decimal | None = None


class PropertyRead(PropertyBase):
    """Serialize a stored property for API responses."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class PricingGroupCreate(BaseModel):
    """Validate creation of a pricing group."""

    name: str = Field(min_length=1, max_length=200)
    pricing_settings: dict = Field(default_factory=dict)
    competitor_urls: list[str] = Field(default_factory=list, max_length=30)


class PricingGroupUpdate(BaseModel):
    """Validate a partial pricing-group update."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    pricing_settings: dict | None = None
    competitor_urls: list[str] | None = Field(default=None, max_length=30)


class OverrideCreate(BaseModel):
    """Validate creation of a hard date-range override."""

    property_id: int
    start_date: date
    end_date: date
    price: Decimal | None = Field(default=None, gt=0)
    reason: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def valid_override(self):
        """Require a valid range for a manual price."""

        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        if self.price is None:
            raise ValueError("price is required")
        return self


class PricingConfiguration(BaseModel):
    """Validate global Pricing Engine v2 coefficients."""

    base_price_mode: Literal["market_median", "manual"]
    manual_base_price: Decimal | None = Field(default=None, gt=0)
    guest_to_host_price_factor: float = Field(gt=0, le=1)
    market_price_adjustment: float = Field(gt=-1)
    demand_adjustment_enabled: bool
    urgency_adjustment_enabled: bool
    competitor_weight: float = Field(ge=0, le=1)
    pricing_group_weight: float = Field(ge=0, le=1)
    neutral_demand_score: float = Field(ge=0, le=1)
    demand_adjustment_slope: float = Field(ge=0)
    minimum_demand_adjustment: float = Field(ge=-1, le=0)
    maximum_demand_adjustment: float = Field(ge=0, le=1)
    urgency_adjustments: list[dict]

    @model_validator(mode="after")
    def valid_configuration(self):
        """Require normalized weights and valid non-positive urgency tiers."""

        if abs(self.competitor_weight + self.pricing_group_weight - 1.0) > 1e-9:
            raise ValueError("competitor_weight + pricing_group_weight must equal 1.0")
        if self.base_price_mode == "manual" and self.manual_base_price is None:
            raise ValueError("manual_base_price is required in manual mode")
        maximum_days = []
        for tier in self.urgency_adjustments:
            if "maximum_days" not in tier or "adjustment" not in tier:
                raise ValueError("each urgency tier requires maximum_days and adjustment")
            if int(tier["maximum_days"]) < 0 or float(tier["adjustment"]) > 0:
                raise ValueError("urgency tiers require non-negative days and non-positive adjustments")
            maximum_days.append(int(tier["maximum_days"]))
        if len(maximum_days) != len(set(maximum_days)):
            raise ValueError("urgency tier maximum_days values must be unique")
        return self


class PricingConfigurationOverride(BaseModel):
    """Validate optional property-level overrides of global pricing settings."""

    model_config = ConfigDict(extra="forbid")

    base_price_mode: Literal["market_median", "manual"] | None = None
    manual_base_price: Decimal | None = Field(default=None, gt=0)
    market_price_adjustment: float | None = Field(default=None, gt=-1)
    demand_adjustment_enabled: bool | None = None
    urgency_adjustment_enabled: bool | None = None
    competitor_weight: float | None = Field(default=None, ge=0, le=1)
    pricing_group_weight: float | None = Field(default=None, ge=0, le=1)
    neutral_demand_score: float | None = Field(default=None, ge=0, le=1)
    demand_adjustment_slope: float | None = Field(default=None, ge=0)
    minimum_demand_adjustment: float | None = Field(default=None, ge=-1, le=0)
    maximum_demand_adjustment: float | None = Field(default=None, ge=0, le=1)
    urgency_adjustments: list[dict] | None = None


class ModeUpdate(BaseModel):
    """Validate a shadow or production mode transition."""

    mode: Literal["shadow", "production"]
    activation_date: date | None = None

    @model_validator(mode="after")
    def production_requires_date(self):
        """Require an explicit activation date for production mode."""

        if self.mode == "production" and not self.activation_date:
            raise ValueError("production mode requires activation_date")
        return self


class CompetitorScrapeCreate(BaseModel):
    """Validate a granular manual competitor collection request."""

    competitor_listing_id: int
    start_date: date
    end_date: date
    force_refresh: bool = False
    collection_mode: Literal["precise", "rough"] | None = None

    @model_validator(mode="after")
    def valid_date_range(self):
        """Require an ordered inclusive date range."""

        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self


class CompetitorCalendarDayInput(BaseModel):
    """Validate one minimal calendar fact returned by the collector."""

    model_config = ConfigDict(extra="forbid")

    stay_date: date
    bookable: bool
    min_nights: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def bookable_day_requires_minimum_stay(self):
        """Require a positive minimum stay for every bookable date."""

        if self.bookable and self.min_nights is None:
            raise ValueError("bookable calendar days require min_nights")
        return self


class CompetitorCalendarCallback(BaseModel):
    """Validate a complete calendar-stage collector callback."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["calendar"]
    run_id: int
    external_listing_id: str = Field(min_length=1, max_length=150)
    status: Literal["succeeded", "failed", "source_not_configured"]
    calendar_days: list[CompetitorCalendarDayInput] = Field(default_factory=list)
    scraped_at: datetime
    parser_version: str = Field(min_length=1, max_length=30)
    error: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valid_calendar_result(self):
        """Require successful calendars and reject partial or duplicate days."""

        if self.status == "succeeded" and not self.calendar_days:
            raise ValueError("successful calendar callbacks require days")
        if self.status != "succeeded" and self.calendar_days:
            raise ValueError("failed calendar callbacks must not contain days")
        dates = [item.stay_date for item in self.calendar_days]
        if len(dates) != len(set(dates)):
            raise ValueError("calendar callback contains duplicate dates")
        return self


class CompetitorQuoteInput(BaseModel):
    """Validate one successful raw stay quote."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str = Field(min_length=1, max_length=64)
    check_in_date: date
    check_out_date: date
    adults: int = Field(ge=1)
    total_price: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    scraped_at: datetime
    parser_version: str = Field(min_length=1, max_length=30)
    raw: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def checkout_follows_checkin(self):
        """Reject empty and backwards quote intervals."""

        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date must follow check_in_date")
        return self


class CompetitorQuoteErrorInput(BaseModel):
    """Validate one recoverable quote-scoped error."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1, max_length=500)


class CompetitorQuoteBatchCallback(BaseModel):
    """Validate an idempotent quote-batch collector callback."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["quotes"]
    run_id: int
    batch_id: int
    external_listing_id: str = Field(min_length=1, max_length=150)
    status: Literal["succeeded", "partially_succeeded", "failed"]
    quotes: list[CompetitorQuoteInput] = Field(default_factory=list)
    quote_errors: list[CompetitorQuoteErrorInput] = Field(default_factory=list)
    error: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def valid_result(self):
        """Require callback status to agree with quote and error collections."""

        if self.status == "succeeded" and (not self.quotes or self.quote_errors):
            raise ValueError("successful quote callbacks require only quotes")
        if self.status == "partially_succeeded" and (
            not self.quotes or not self.quote_errors
        ):
            raise ValueError("partial quote callbacks require quotes and errors")
        if self.status == "failed" and self.quotes:
            raise ValueError("failed quote callbacks must not contain quotes")
        identities = [item.quote_id for item in [*self.quotes, *self.quote_errors]]
        if len(identities) != len(set(identities)):
            raise ValueError("quote callback contains duplicate quote IDs")
        return self
