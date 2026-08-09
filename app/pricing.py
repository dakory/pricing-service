from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import median


# Defaults are persisted through the pricing settings API and may be tuned without code changes.
DEFAULT_PRICING_CONFIGURATION = {
    "base_price_mode": "market_median",
    "manual_base_price": None,
    "guest_to_host_price_factor": 0.839,
    "market_positioning_factor": 1.0,
    "minimum_competitor_count": 10,
    "urgency_adjustment_enabled": True,
    "urgency_adjustments": [
        {"minimum_days": 0, "maximum_days": 3, "adjustment": -0.15},
        {"minimum_days": 4, "maximum_days": 7, "adjustment": -0.10},
        {"minimum_days": 8, "maximum_days": 14, "adjustment": -0.05},
        {"minimum_days": 15, "maximum_days": 30, "adjustment": -0.02},
    ],
}


def merge_pricing_configuration(
    parent: dict, overrides: dict | None = None
) -> dict:
    """Merge settings, replacing a supplied urgency list as one unit."""

    overrides = {
        key: value
        for key, value in (overrides or {}).items()
        if value is not None
    }
    merged = {**parent, **overrides}
    if "urgency_adjustments" not in overrides:
        merged["urgency_adjustments"] = [
            dict(rule) for rule in parent.get("urgency_adjustments", [])
        ]
    return merged


def round_to_pricing_step(value: float, pricing_step: int) -> int:
    """Round an IDR price to the nearest configured pricing step."""

    units = (Decimal(str(value)) / Decimal(pricing_step)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(units * pricing_step)


def calculate_urgency_adjustment(days_until_stay: int, configuration: dict) -> float:
    """Return the adjustment from the matching inclusive urgency range."""

    if not configuration.get("urgency_adjustment_enabled", True):
        return 0.0
    days_until_stay = max(0, days_until_stay)
    for rule in sorted(
        configuration.get("urgency_adjustments", []),
        key=lambda item: int(item["minimum_days"]),
    ):
        if int(rule["minimum_days"]) <= days_until_stay <= int(
            rule["maximum_days"]
        ):
            return float(rule["adjustment"])
    return 0.0


def calculate_price(
    *,
    stay_date: date,
    current_date: date,
    competitor_prices: list[float],
    saved_market_price: float | None,
    current_price: float | None,
    minimum_competitor_count: int,
    minimum_price: float,
    maximum_price: float,
    pricing_step: int,
    configuration: dict,
    manual_override: float | None = None,
) -> dict | None:
    """Calculate one Pricing Engine v3 recommendation."""

    days_until_stay = max(0, (stay_date - current_date).days)
    if manual_override is not None:
        return {
            "price": float(manual_override),
                "explanation": {
                    "engine_version": "v3",
                    "stay_date": stay_date.isoformat(),
                    "price_source": "manual_override",
                    "days_until_stay": days_until_stay,
                    "manual_override": manual_override,
                    "urgency_adjustment_enabled": bool(configuration.get("urgency_adjustment_enabled", True)),
                    "urgency_adjustment_applied": False,
                    "final_price": float(manual_override),
                },
        }

    base_price_mode = configuration["base_price_mode"]
    market_price_count = len(competitor_prices)
    market_price_source: str | None = None
    market_price: float | None = None
    if base_price_mode == "manual":
        manual_base_price = configuration.get("manual_base_price")
        if manual_base_price is None:
            raise ValueError("manual_base_price is required for manual mode")
        base_price = float(manual_base_price)
        price_source = "manual_base"
    elif base_price_mode == "market_median":
        if market_price_count >= minimum_competitor_count:
            market_price = float(median(competitor_prices))
            market_price_source = "current_market"
        elif saved_market_price is not None:
            market_price = float(saved_market_price)
            market_price_source = "saved_market"
        elif current_price is not None:
            return {
                "price": float(current_price),
                "explanation": {
                    "engine_version": "v3",
                    "stay_date": stay_date.isoformat(),
                    "price_source": "current_hostex_price",
                    "days_until_stay": days_until_stay,
                    "available_competitor_count": market_price_count,
                    "minimum_competitor_count": minimum_competitor_count,
                    "current_price": current_price,
                    "urgency_adjustment_enabled": bool(configuration.get("urgency_adjustment_enabled", True)),
                    "urgency_adjustment_applied": False,
                    "urgency_adjustment": 0.0,
                    "final_price": float(current_price),
                },
            }
        else:
            return None
        guest_to_host_factor = float(configuration["guest_to_host_price_factor"])
        estimated_host_price_median = market_price * guest_to_host_factor
        positioning_factor = float(configuration["market_positioning_factor"])
        base_price = estimated_host_price_median * positioning_factor
        price_source = market_price_source
    else:
        raise ValueError(f"unsupported base_price_mode: {base_price_mode}")

    urgency_adjustment = calculate_urgency_adjustment(
        days_until_stay, configuration
    )
    raw_price = base_price * (1 + urgency_adjustment)
    rounded_price = round_to_pricing_step(raw_price, pricing_step)
    final_price = min(maximum_price, max(minimum_price, rounded_price))
    guest_to_host_factor = float(configuration["guest_to_host_price_factor"])
    estimated_host_price_median = (
        market_price * guest_to_host_factor
        if market_price is not None
        else None
    )
    return {
        "price": float(final_price),
        "explanation": {
            "engine_version": "v3",
            "stay_date": stay_date.isoformat(),
            "days_until_stay": days_until_stay,
            "price_source": price_source,
            "available_competitor_count": market_price_count,
            "minimum_competitor_count": minimum_competitor_count,
            "airbnb_guest_market_median": market_price,
            "guest_to_host_price_factor": guest_to_host_factor,
            "estimated_host_price_median": estimated_host_price_median,
            "market_positioning_factor": configuration.get(
                "market_positioning_factor", 1.0
            ),
            "base_price_mode": base_price_mode,
            "manual_base_price": configuration.get("manual_base_price"),
            "base_price": round(base_price, 2),
            "urgency_adjustment_enabled": configuration.get(
                "urgency_adjustment_enabled", True
            ),
            "urgency_adjustment_applied": True,
            "urgency_adjustment": urgency_adjustment,
            "raw_price": round(raw_price, 2),
            "rounded_price": rounded_price,
            "minimum_price": minimum_price,
            "maximum_price": maximum_price,
            "pricing_step": pricing_step,
            "manual_override": None,
            "final_price": float(final_price),
        },
    }
