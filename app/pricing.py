from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from statistics import median


# Target portfolio occupancy by booking lead time; reserved for the later pace model.
TARGET_CURVE = ((45, 0.25), (28, 0.45), (14, 0.70), (7, 0.85), (2, 0.95))
# Converts an OTA competitor price into an estimated direct-booking equivalent.
DIRECT_CONVERSION = 0.839


def target_occupancy(days_out: int) -> float:
    """Interpolate target occupancy for the supplied booking lead time."""

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


def round_indonesian_rupiah(value: float, increment: int) -> int:
    """Round an IDR amount to the nearest configured increment."""

    units = (Decimal(str(value)) / Decimal(increment)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(units * increment)


@dataclass(frozen=True)
class CompetitorPrice:
    """Represent one current or recently observed competitor price."""

    price: float
    available: bool
    observed_at: datetime
    last_available_price: float | None = None
    last_available_at: datetime | None = None


def usable_competitor_prices(
    competitor_prices: list[CompetitorPrice], now: datetime
) -> list[tuple[float, float]]:
    """Return fresh competitor prices with lower weights for imputed values."""

    if not competitor_prices or max(item.observed_at for item in competitor_prices) < now - timedelta(days=10):
        return []
    prices = []
    for comp in competitor_prices:
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
    """Calculate the median of values carrying explicit observation weights."""

    ordered = sorted(values)
    threshold = sum(weight for _, weight in ordered) / 2
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= threshold:
            return value
    return ordered[-1][0]


def gap_adjustment(gap_length: int | None, rules: dict) -> tuple[float, int | None]:
    """Return the price factor and optional stay relaxation for an orphan gap."""

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
    apply_booking_pace: bool = True,
    forward_occupancy: float | None = None,
    competitor_prices: list[CompetitorPrice] | None = None,
    competitor_availability: float | None = None,
    gap_length: int | None = None,
    gap_rules: dict | None = None,
    default_minimum_stay: int = 1,
    override_price: float | None = None,
    override_minimum_stay: int | None = None,
    now: datetime | None = None,
) -> dict:
    """Calculate one explainable daily recommendation and minimum stay."""

    now = now or datetime.now(timezone.utc)
    anchor = base_price * season_factor * weekday_factor
    usable = usable_competitor_prices(competitor_prices or [], now)
    market_median = weighted_median(usable) if len(usable) >= 3 else None
    market_benchmark = market_median * DIRECT_CONVERSION if market_median else None
    blended = 0.6 * market_benchmark + 0.4 * anchor if market_benchmark else anchor

    target = target_occupancy(max(0, (stay_date - today).days))
    pace_adjustment = max(-0.20, min(0.20, portfolio_occupancy - target)) if apply_booking_pace else 0.0
    forward_occupancy_adjustment = 0.0
    if forward_occupancy is not None:
        forward_occupancy_adjustment = max(-0.10, min(0.10, (forward_occupancy - 0.5) * 0.20))
    availability_adjustment = 0.0
    if competitor_availability is not None and usable:
        availability_adjustment = max(-0.05, min(0.05, (0.5 - competitor_availability) * 0.10))

    gap_factor, relaxed_stay = gap_adjustment(gap_length, gap_rules or {})
    before_bounds = blended * (
        1 + pace_adjustment + forward_occupancy_adjustment + availability_adjustment
    ) * gap_factor
    bounded = min(max_price, max(min_price, before_bounds))
    rounded = round_indonesian_rupiah(bounded, rounding_increment)
    final_price = round_indonesian_rupiah(override_price, rounding_increment) if override_price is not None else rounded
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
            "booking_pace_enabled": apply_booking_pace,
            "forward_occupancy": forward_occupancy,
            "forward_occupancy_adjustment": forward_occupancy_adjustment,
            "competitor_availability_adjustment": availability_adjustment,
            "orphan_gap_factor": gap_factor,
            "before_bounds": round(before_bounds, 2),
            "bounded_price": round(bounded, 2),
            "rounding_increment": rounding_increment,
            "hard_override": override_price is not None or override_minimum_stay is not None,
        },
    }
