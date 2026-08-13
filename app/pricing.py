from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP


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
    # Global bounds are inherited by groups and properties unless overridden.
    "minimum_price": 1,
    "maximum_price": 999_999_999,
    "rounding_increment": 50_000,
    # Property-level default for whether recommendations remain active.
    "suggest_prices": True,
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

    if not configuration["urgency_adjustment_enabled"]:
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
    price_anchor: dict | None,
    available_competitor_count: int,
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
                "urgency_adjustment_enabled": configuration[
                    "urgency_adjustment_enabled"
                ],
                "urgency_adjustment_applied": False,
                "final_price": float(manual_override),
            },
        }

    base_price_mode = configuration["base_price_mode"]
    market_price_count = available_competitor_count
    market_price: float | None = None
    anchor_source = None
    if price_anchor is not None:
        anchor_source = str(price_anchor["source_type"])
        source_price = float(price_anchor["source_price"])
        if anchor_source == "airbnb_market_median":
            market_price = source_price
            base_price = (
                source_price
                * float(configuration["guest_to_host_price_factor"])
                * float(configuration["market_positioning_factor"])
            )
            price_source = price_anchor.get("price_source", "saved_market")
        elif anchor_source in {"manual_base", "hostex_fallback"}:
            base_price = source_price
            price_source = anchor_source
        else:
            raise ValueError(f"unsupported price anchor source: {anchor_source}")
    elif base_price_mode == "manual":
        manual_base_price = configuration.get("manual_base_price")
        if manual_base_price is None:
            raise ValueError("manual_base_price is required for manual mode")
        base_price = float(manual_base_price)
        price_source = "manual_base"
    else:
        return None

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
            "anchor_source": anchor_source or "manual_base",
            "anchor_source_price": (
                float(price_anchor["source_price"]) if price_anchor else float(base_price)
            ),
            "available_competitor_count": market_price_count,
            "anchor_competitor_count": int(
                (price_anchor or {}).get("source_metadata", {}).get("competitor_count", 0)
            ) or None,
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
            "urgency_adjustment_enabled": configuration["urgency_adjustment_enabled"],
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
