from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PropertyBase(BaseModel):
    """Define shared property pricing-policy fields."""

    name: str
    hostex_listing_id: str
    booking_site_listing_id: str | None = None
    active: bool = True
    base_price: Decimal = Field(gt=0)
    min_price: Decimal = Field(gt=0)
    max_price: Decimal = Field(gt=0)
    rounding_increment: int = Field(default=50_000, gt=0)
    season_factors: dict[str, float] = {}
    weekday_factors: dict[str, float] = {}
    minimum_stay_rules: dict = {}
    orphan_gap_rules: dict = {}
    weekly_discount: Decimal | None = None
    monthly_discount: Decimal | None = None
    competitor_urls: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def valid_bounds(self):
        """Require the canonical base to remain inside configured bounds."""

        if not self.min_price <= self.base_price <= self.max_price:
            raise ValueError("price bounds must satisfy min <= base <= max")
        return self


class PropertyCreate(PropertyBase):
    """Validate creation of a managed property."""

    pass


class PropertyUpdate(BaseModel):
    """Validate a partial update to a property pricing policy."""

    name: str | None = None
    active: bool | None = None
    base_price: Decimal | None = Field(default=None, gt=0)
    min_price: Decimal | None = Field(default=None, gt=0)
    max_price: Decimal | None = Field(default=None, gt=0)
    rounding_increment: int | None = Field(default=None, gt=0)
    season_factors: dict[str, float] | None = None
    weekday_factors: dict[str, float] | None = None
    minimum_stay_rules: dict | None = None
    orphan_gap_rules: dict | None = None
    weekly_discount: Decimal | None = None
    monthly_discount: Decimal | None = None
    competitor_urls: list[str] | None = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def valid_factors(self):
        """Reject invalid factor and minimum-stay configuration values."""

        for factors in (self.season_factors, self.weekday_factors):
            if factors and any(value <= 0 or value > 3 for value in factors.values()):
                raise ValueError("pricing factors must be greater than 0 and at most 3")
        if self.minimum_stay_rules and int(self.minimum_stay_rules.get("default", 1)) < 1:
            raise ValueError("default minimum stay must be at least 1")
        return self


class PropertyRead(PropertyBase):
    """Serialize a stored property for API responses."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class OverrideCreate(BaseModel):
    """Validate creation of a hard date-range override."""

    property_id: int
    start_date: date
    end_date: date
    price: Decimal | None = Field(default=None, gt=0)
    minimum_stay: int | None = Field(default=None, ge=1)
    reason: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def valid_override(self):
        """Require a valid range and at least one locked value."""

        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        if self.price is None and self.minimum_stay is None:
            raise ValueError("price or minimum_stay is required")
        return self


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
