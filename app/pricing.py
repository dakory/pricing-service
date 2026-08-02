from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import median


# Defaults are persisted through the pricing settings API and may be tuned without code changes.
DEFAULT_PRICING_CONFIGURATION = {
    "base_price_mode": "market_median",
    "manual_base_price": None,
    # Converts Airbnb's guest-facing total to a comparable canonical host price.
    "guest_to_host_price_factor": 0.839,
    "market_price_adjustment": 0.0,
    "demand_adjustment_enabled": True,
    "urgency_adjustment_enabled": True,
    "competitor_weight": 0.70,
    "pricing_group_weight": 0.30,
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


def merge_pricing_configuration(
    parent: dict, overrides: dict | None = None
) -> dict:
    """Merge pricing overrides while inheriting untouched urgency tiers."""

    overrides = {
        key: value
        for key, value in (overrides or {}).items()
        if value is not None
    }
    merged = {**parent, **overrides}
    parent_tiers = {
        int(tier["maximum_days"]): dict(tier)
        for tier in parent.get("urgency_adjustments", [])
    }
    for tier in overrides.get("urgency_adjustments", []):
        parent_tiers[int(tier["maximum_days"])] = dict(tier)
    merged["urgency_adjustments"] = [
        parent_tiers[maximum_days] for maximum_days in sorted(parent_tiers)
    ]
    return merged


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
    booked_pricing_group_property_count: int,
    all_pricing_group_property_count: int,
    minimum_price: float,
    maximum_price: float,
    pricing_step: int,
    configuration: dict,
    manual_override: float | None = None,
) -> dict:
    """Calculate one Pricing Engine v2 recommendation from prepared inputs."""

    if all_pricing_group_property_count <= 0:
        raise ValueError("all_pricing_group_property_count must be positive")

    base_price_mode = configuration["base_price_mode"]
    airbnb_guest_market_median = (
        float(median(available_competitor_prices))
        if available_competitor_prices
        else None
    )
    guest_to_host_price_factor = float(
        configuration["guest_to_host_price_factor"]
    )
    estimated_host_price_median = (
        airbnb_guest_market_median * guest_to_host_price_factor
        if airbnb_guest_market_median is not None
        else None
    )
    market_price_adjustment = float(configuration["market_price_adjustment"])
    if base_price_mode == "market_median":
        if estimated_host_price_median is None:
            raise ValueError(
                "at least one available competitor price is required for market_median mode"
            )
        base_price = estimated_host_price_median * (1 + market_price_adjustment)
    elif base_price_mode == "manual":
        manual_base_price = configuration.get("manual_base_price")
        if manual_base_price is None:
            raise ValueError("manual_base_price is required for manual mode")
        base_price = float(manual_base_price)
    else:
        raise ValueError(f"unsupported base_price_mode: {base_price_mode}")

    competitor_unavailability = (
        unavailable_competitor_count / all_tracked_competitor_count
        if all_tracked_competitor_count
        else 0.0
    )
    pricing_group_occupancy = (
        booked_pricing_group_property_count
        / all_pricing_group_property_count
    )
    competitor_weight = float(configuration["competitor_weight"])
    pricing_group_weight = float(configuration["pricing_group_weight"])
    demand_score = (
        competitor_weight * competitor_unavailability
        + pricing_group_weight * pricing_group_occupancy
    )
    demand_adjustment_enabled = bool(
        configuration["demand_adjustment_enabled"]
    )
    demand_adjustment = (
        calculate_demand_adjustment(demand_score, configuration)
        if demand_adjustment_enabled
        else 0.0
    )
    days_until_stay = max(0, (stay_date - current_date).days)
    urgency_adjustment_enabled = bool(
        configuration["urgency_adjustment_enabled"]
    )
    urgency_adjustment = (
        calculate_urgency_adjustment(days_until_stay, configuration)
        if urgency_adjustment_enabled
        else 0.0
    )
    raw_price = base_price * (1 + demand_adjustment + urgency_adjustment)
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
            "airbnb_guest_market_median": airbnb_guest_market_median,
            "guest_to_host_price_factor": guest_to_host_price_factor,
            "estimated_host_price_median": estimated_host_price_median,
            "base_price_mode": base_price_mode,
            "market_price_adjustment": market_price_adjustment,
            "manual_base_price": configuration.get("manual_base_price"),
            "base_price": round(base_price, 2),
            "booked_pricing_group_property_count": booked_pricing_group_property_count,
            "all_pricing_group_property_count": all_pricing_group_property_count,
            "pricing_group_occupancy": pricing_group_occupancy,
            "competitor_weight": competitor_weight,
            "pricing_group_weight": pricing_group_weight,
            "demand_score": demand_score,
            "demand_adjustment_enabled": demand_adjustment_enabled,
            "demand_adjustment": demand_adjustment,
            "urgency_adjustment_enabled": urgency_adjustment_enabled,
            "urgency_adjustment": urgency_adjustment,
            "raw_price": round(raw_price, 2),
            "bounded_price": round(bounded_price, 2),
            "rounded_price": rounded_price,
            "pricing_step": pricing_step,
            "manual_override": manual_override,
            "final_price": final_price,
        },
    }
