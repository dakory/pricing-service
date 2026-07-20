from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from statistics import median


TARGET_CURVE = ((45, 0.25), (28, 0.45), (14, 0.70), (7, 0.85), (2, 0.95))
DIRECT_CONVERSION = 0.839


def target_occupancy(days_out: int) -> float:
    points = sorted(TARGET_CURVE)
    if days_out <= points[0][0]:
        return points[0][1]
    if days_out >= points[-1][0]:
        return points[-1][1]
    for (left_day, left_value), (right_day, right_value) in zip(points, points[1:]):
        if left_day <= days_out <= right_day:
            ratio = (days_out - left_day) / (right_day - left_day)
            return left_value + ratio * (right_value - left_value)
    raise AssertionError("unreachable")


def round_idr(value: float, increment: int) -> int:
    units = (Decimal(str(value)) / Decimal(increment)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(units * increment)


@dataclass(frozen=True)
class Comp:
    price: float
    available: bool
    observed_at: datetime
    last_available_price: float | None = None
    last_available_at: datetime | None = None


def usable_comp_prices(comps: list[Comp], now: datetime) -> list[tuple[float, float]]:
    if not comps or max(item.observed_at for item in comps) < now - timedelta(days=10):
        return []
    prices = []
    for comp in comps:
        if comp.available:
            prices.append((comp.price, 1.0))
        elif (
            comp.last_available_price is not None
            and comp.last_available_at is not None
            and comp.last_available_at >= now - timedelta(days=30)
        ):
            prices.append((comp.last_available_price, 0.5))
    return prices


def weighted_median(values: list[tuple[float, float]]) -> float:
    ordered = sorted(values)
    threshold = sum(weight for _, weight in ordered) / 2
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= threshold:
            return value
    return ordered[-1][0]


def gap_adjustment(gap_length: int | None, rules: dict) -> tuple[float, int | None]:
    if not gap_length:
        return 1.0, None
    max_gap = int(rules.get("max_gap", 0))
    if max_gap and gap_length <= max_gap:
        factor = float(rules.get("price_factor", 1.0))
        relaxed = gap_length if rules.get("relax_minimum_stay", False) else None
        return factor, relaxed
    return 1.0, None


def calculate_price(
    *,
    stay_date: date,
    today: date,
    base_price: float,
    min_price: float,
    max_price: float,
    rounding_increment: int,
    season_factor: float = 1.0,
    weekday_factor: float = 1.0,
    portfolio_occupancy: float = 0.0,
    comps: list[Comp] | None = None,
    competitor_availability: float | None = None,
    gap_length: int | None = None,
    gap_rules: dict | None = None,
    default_minimum_stay: int = 1,
    override_price: float | None = None,
    override_minimum_stay: int | None = None,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    anchor = base_price * season_factor * weekday_factor
    usable = usable_comp_prices(comps or [], now)
    market_median = weighted_median(usable) if len(usable) >= 3 else None
    market_benchmark = market_median * DIRECT_CONVERSION if market_median else None
    blended = 0.6 * market_benchmark + 0.4 * anchor if market_benchmark else anchor

    target = target_occupancy(max(0, (stay_date - today).days))
    pace_adjustment = max(-0.20, min(0.20, portfolio_occupancy - target))
    availability_adjustment = 0.0
    if competitor_availability is not None and usable:
        availability_adjustment = max(-0.05, min(0.05, (0.5 - competitor_availability) * 0.10))

    gap_factor, relaxed_stay = gap_adjustment(gap_length, gap_rules or {})
    before_bounds = blended * (1 + pace_adjustment + availability_adjustment) * gap_factor
    bounded = min(max_price, max(min_price, before_bounds))
    rounded = round_idr(bounded, rounding_increment)
    final_price = round_idr(override_price, rounding_increment) if override_price is not None else rounded
    minimum_stay = override_minimum_stay or relaxed_stay or default_minimum_stay
    return {
        "price": final_price,
        "minimum_stay": minimum_stay,
        "explanation": {
            "internal_anchor": round(anchor, 2),
            "usable_comp_count": len(usable),
            "market_median": market_median,
            "direct_conversion": DIRECT_CONVERSION if market_median else None,
            "market_benchmark": market_benchmark,
            "blended_price": round(blended, 2),
            "target_occupancy": target,
            "portfolio_occupancy": portfolio_occupancy,
            "booking_pace_adjustment": pace_adjustment,
            "competitor_availability_adjustment": availability_adjustment,
            "orphan_gap_factor": gap_factor,
            "before_bounds": round(before_bounds, 2),
            "bounded_price": round(bounded, 2),
            "rounding_increment": rounding_increment,
            "hard_override": override_price is not None or override_minimum_stay is not None,
        },
    }
