from datetime import date, datetime, timedelta, timezone

import pytest

from app.pricing import Comp, calculate_price, target_occupancy


@pytest.mark.parametrize(
    ("days", "expected"),
    [(2, 0.95), (7, 0.85), (14, 0.70), (28, 0.45), (45, 0.25), (10, 0.7857142857)],
)
def test_target_curve(days, expected):
    assert target_occupancy(days) == pytest.approx(expected)


def test_market_blending_and_direct_conversion():
    now = datetime.now(timezone.utc)
    comps = [Comp(price=value, available=True, observed_at=now) for value in [1_000_000, 1_200_000, 1_400_000]]
    result = calculate_price(
        stay_date=date.today() + timedelta(days=28),
        today=date.today(),
        base_price=1_000_000,
        min_price=500_000,
        max_price=2_000_000,
        rounding_increment=10_000,
        portfolio_occupancy=0.45,
        comps=comps,
        now=now,
    )
    assert result["explanation"]["market_benchmark"] == pytest.approx(1_006_800)
    assert result["explanation"]["blended_price"] == pytest.approx(1_004_080)
    assert result["price"] == 1_000_000


def test_stale_collection_omits_all_competitor_factors():
    now = datetime.now(timezone.utc)
    comps = [Comp(price=2_000_000, available=True, observed_at=now - timedelta(days=11))] * 3
    result = calculate_price(
        stay_date=date.today() + timedelta(days=28),
        today=date.today(),
        base_price=1_000_000,
        min_price=500_000,
        max_price=2_000_000,
        rounding_increment=50_000,
        portfolio_occupancy=0.45,
        comps=comps,
        competitor_availability=0,
        now=now,
    )
    assert result["explanation"]["usable_comp_count"] == 0
    assert result["explanation"]["competitor_availability_adjustment"] == 0


def test_imputed_unavailable_comp_expires_after_30_days():
    now = datetime.now(timezone.utc)
    comp = Comp(
        price=0,
        available=False,
        observed_at=now,
        last_available_price=1_000_000,
        last_available_at=now - timedelta(days=31),
    )
    result = calculate_price(
        stay_date=date.today(),
        today=date.today(),
        base_price=1_000_000,
        min_price=500_000,
        max_price=2_000_000,
        rounding_increment=50_000,
        comps=[comp, comp, comp],
        now=now,
    )
    assert result["explanation"]["usable_comp_count"] == 0


def test_caps_gap_bounds_rounding_and_hard_override():
    result = calculate_price(
        stay_date=date.today() + timedelta(days=45),
        today=date.today(),
        base_price=1_000_000,
        min_price=900_000,
        max_price=1_100_000,
        rounding_increment=50_000,
        portfolio_occupancy=1.0,
        gap_length=2,
        gap_rules={"max_gap": 3, "price_factor": 0.9, "relax_minimum_stay": True},
        default_minimum_stay=5,
        override_price=1_234_000,
        override_minimum_stay=4,
    )
    assert result["explanation"]["booking_pace_adjustment"] == 0.2
    assert result["explanation"]["bounded_price"] == 1_080_000
    assert result["price"] == 1_250_000
    assert result["minimum_stay"] == 4
    assert result["explanation"]["hard_override"] is True

