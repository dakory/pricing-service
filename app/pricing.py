from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import median


# Defaults are persisted through the pricing settings API and may be tuned without code changes.
DEFAULT_PRICING_CONFIGURATION = {
    "competitor_weight": 0.70,
    "portfolio_weight": 0.30,
    "neutral_demand_score": 0.50,
    "demand_adjustment_slope": 0.40,
    "minimum_demand_adjustment": -0.20,
    "maximum_demand_adjustment": 0.20,
    "urgency_adjustments": [
        {"maximum_days": 3, "adjustment": -0.15},
        {"maximum_days": 7, "adjustment": -0.10},
        {"maximum_days": 14, "adjustment": -0.05},
        {"maximum_days": 30, "adjustment": -0.02},
    ],
}


def round_to_pricing_step(value: float, pricing_step: int) -> int:
    """Round an IDR price to the nearest configured pricing step."""

    units = (Decimal(str(value)) / Decimal(pricing_step)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(units * pricing_step)


def calculate_demand_adjustment(demand_score: float, configuration: dict) -> float:
    """Convert a demand score to a bounded percentage adjustment."""

    adjustment = (
        demand_score - float(configuration["neutral_demand_score"])
    ) * float(configuration["demand_adjustment_slope"])
    return max(
        float(configuration["minimum_demand_adjustment"]),
        min(float(configuration["maximum_demand_adjustment"]), adjustment),
    )


def calculate_urgency_adjustment(days_until_stay: int, configuration: dict) -> float:
    """Return the configured non-positive adjustment for booking urgency."""

    days_until_stay = max(0, days_until_stay)
    tiers = sorted(
        configuration["urgency_adjustments"],
        key=lambda tier: int(tier["maximum_days"]),
    )
    for tier in tiers:
        if days_until_stay <= int(tier["maximum_days"]):
            return float(tier["adjustment"])
    return 0.0


def calculate_price(
    *,
    stay_date: date,
    current_date: date,
    available_competitor_prices: list[float],
    unavailable_competitor_count: int,
    all_tracked_competitor_count: int,
    booked_own_property_count: int,
    all_own_property_count: int,
    minimum_price: float,
    maximum_price: float,
    pricing_step: int,
    configuration: dict,
    manual_override: float | None = None,
) -> dict:
    """Calculate one Pricing Engine v2 recommendation from prepared inputs."""

    if not available_competitor_prices:
        raise ValueError("at least one available competitor price is required")
    if all_tracked_competitor_count <= 0:
        raise ValueError("all_tracked_competitor_count must be positive")
    if all_own_property_count <= 0:
        raise ValueError("all_own_property_count must be positive")

    market_price = float(median(available_competitor_prices))
    competitor_unavailability = (
        unavailable_competitor_count / all_tracked_competitor_count
    )
    portfolio_occupancy = booked_own_property_count / all_own_property_count
    competitor_weight = float(configuration["competitor_weight"])
    portfolio_weight = float(configuration["portfolio_weight"])
    demand_score = (
        competitor_weight * competitor_unavailability
        + portfolio_weight * portfolio_occupancy
    )
    demand_adjustment = calculate_demand_adjustment(demand_score, configuration)
    days_until_stay = max(0, (stay_date - current_date).days)
    urgency_adjustment = calculate_urgency_adjustment(
        days_until_stay, configuration
    )
    raw_price = market_price * (1 + demand_adjustment + urgency_adjustment)
    bounded_price = min(maximum_price, max(minimum_price, raw_price))
    rounded_price = round_to_pricing_step(bounded_price, pricing_step)
    final_price = float(manual_override) if manual_override is not None else rounded_price

    return {
        "price": final_price,
        "explanation": {
            "engine_version": "v2",
            "stay_date": stay_date.isoformat(),
            "days_until_stay": days_until_stay,
            "available_competitor_count": len(available_competitor_prices),
            "unavailable_competitor_count": unavailable_competitor_count,
            "all_tracked_competitor_count": all_tracked_competitor_count,
            "competitor_unavailability": competitor_unavailability,
            "market_price": market_price,
            "booked_own_property_count": booked_own_property_count,
            "all_own_property_count": all_own_property_count,
            "portfolio_occupancy": portfolio_occupancy,
            "competitor_weight": competitor_weight,
            "portfolio_weight": portfolio_weight,
            "demand_score": demand_score,
            "demand_adjustment": demand_adjustment,
            "urgency_adjustment": urgency_adjustment,
            "raw_price": round(raw_price, 2),
            "bounded_price": round(bounded_price, 2),
            "rounded_price": rounded_price,
            "pricing_step": pricing_step,
            "manual_override": manual_override,
            "final_price": final_price,
        },
    }
