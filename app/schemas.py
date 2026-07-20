from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PropertyBase(BaseModel):
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
        if not self.min_price <= self.base_price <= self.max_price:
            raise ValueError("price bounds must satisfy min <= base <= max")
        return self


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
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


class PropertyRead(PropertyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class OverrideCreate(BaseModel):
    property_id: int
    start_date: date
    end_date: date
    price: Decimal | None = Field(default=None, gt=0)
    minimum_stay: int | None = Field(default=None, ge=1)
    reason: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def valid_override(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        if self.price is None and self.minimum_stay is None:
            raise ValueError("price or minimum_stay is required")
        return self


class ModeUpdate(BaseModel):
    mode: Literal["shadow", "production"]
    activation_date: date | None = None

    @model_validator(mode="after")
    def production_requires_date(self):
        if self.mode == "production" and not self.activation_date:
            raise ValueError("production mode requires activation_date")
        return self
