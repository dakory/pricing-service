from datetime import date, timedelta

import pytest

from app.pricing import (
    DEFAULT_PRICING_CONFIGURATION,
    calculate_demand_adjustment,
    calculate_price,
    calculate_urgency_adjustment,
)


def test_market_demand_and_urgency_formula():
    today = date(2026, 7, 30)
    result = calculate_price(
        stay_date=today + timedelta(days=5),
        current_date=today,
        available_competitor_prices=[1_000_000, 1_500_000, 2_000_000],
        unavailable_competitor_count=3,
        all_tracked_competitor_count=4,
        booked_pricing_group_property_count=2,
        all_pricing_group_property_count=3,
        minimum_price=500_000,
        maximum_price=3_000_000,
        pricing_step=50_000,
        configuration=DEFAULT_PRICING_CONFIGURATION,
    )

    explanation = result["explanation"]
    assert explanation["airbnb_guest_market_median"] == 1_500_000
    assert explanation["guest_to_host_price_factor"] == 0.839
    assert explanation["estimated_host_price_median"] == pytest.approx(1_258_500)
    assert explanation["competitor_unavailability"] == pytest.approx(0.75)
    assert explanation["pricing_group_occupancy"] == pytest.approx(2 / 3)
    assert explanation["demand_score"] == pytest.approx(0.725)
    assert explanation["demand_adjustment"] == pytest.approx(0.09)
    assert explanation["urgency_adjustment"] == -0.10
    assert explanation["raw_price"] == pytest.approx(1_245_915)
    assert result["price"] == 1_250_000


@pytest.mark.parametrize(
    ("days", "expected"),
    [(0, -0.15), (3, -0.15), (4, -0.10), (7, -0.10), (8, -0.05), (14, -0.05), (15, -0.02), (30, -0.02), (31, 0)],
)
def test_urgency_tiers(days, expected):
    assert calculate_urgency_adjustment(days, DEFAULT_PRICING_CONFIGURATION) == expected


def test_demand_adjustment_is_bounded():
    configuration = {
        **DEFAULT_PRICING_CONFIGURATION,
        "demand_adjustment_slope": 2,
    }
    assert calculate_demand_adjustment(0, configuration) == -0.20
    assert calculate_demand_adjustment(1, configuration) == 0.20


def test_bounds_rounding_and_override_order():
    today = date(2026, 7, 30)
    bounded = calculate_price(
        stay_date=today + timedelta(days=60),
        current_date=today,
        available_competitor_prices=[3_000_000],
        unavailable_competitor_count=0,
        all_tracked_competitor_count=1,
        booked_pricing_group_property_count=0,
        all_pricing_group_property_count=1,
        minimum_price=900_000,
        maximum_price=1_100_000,
        pricing_step=50_000,
        configuration=DEFAULT_PRICING_CONFIGURATION,
    )
    overridden = calculate_price(
        stay_date=today,
        current_date=today,
        available_competitor_prices=[1_000_000],
        unavailable_competitor_count=0,
        all_tracked_competitor_count=1,
        booked_pricing_group_property_count=0,
        all_pricing_group_property_count=1,
        minimum_price=900_000,
        maximum_price=1_100_000,
        pricing_step=50_000,
        configuration=DEFAULT_PRICING_CONFIGURATION,
        manual_override=1_234_567,
    )

    assert bounded["explanation"]["bounded_price"] == 1_100_000
    assert bounded["price"] == 1_100_000
    assert overridden["price"] == 1_234_567
    assert overridden["explanation"]["manual_override"] == 1_234_567


def test_available_competitor_price_is_required():
    with pytest.raises(ValueError, match="at least one"):
        calculate_price(
            stay_date=date.today(),
            current_date=date.today(),
            available_competitor_prices=[],
            unavailable_competitor_count=1,
            all_tracked_competitor_count=1,
            booked_pricing_group_property_count=0,
            all_pricing_group_property_count=1,
            minimum_price=1,
            maximum_price=2,
            pricing_step=1,
            configuration=DEFAULT_PRICING_CONFIGURATION,
        )


def test_market_offset_changes_the_median_base_price():
    configuration = {
        **DEFAULT_PRICING_CONFIGURATION,
        "market_price_adjustment": -0.10,
        "demand_adjustment_enabled": False,
        "urgency_adjustment_enabled": False,
    }
    result = calculate_price(
        stay_date=date(2026, 9, 1),
        current_date=date(2026, 7, 30),
        available_competitor_prices=[1_000_000, 1_500_000, 2_000_000],
        unavailable_competitor_count=0,
        all_tracked_competitor_count=3,
        booked_pricing_group_property_count=0,
        all_pricing_group_property_count=1,
        minimum_price=500_000,
        maximum_price=2_000_000,
        pricing_step=10_000,
        configuration=configuration,
    )

    assert result["explanation"]["base_price"] == pytest.approx(1_132_650)
    assert result["explanation"]["demand_adjustment"] == 0
    assert result["explanation"]["urgency_adjustment"] == 0
    assert result["price"] == 1_130_000


def test_manual_base_price_does_not_require_competitor_prices():
    configuration = {
        **DEFAULT_PRICING_CONFIGURATION,
        "base_price_mode": "manual",
        "manual_base_price": 1_234_000,
        "demand_adjustment_enabled": False,
        "urgency_adjustment_enabled": False,
    }
    result = calculate_price(
        stay_date=date(2026, 9, 1),
        current_date=date(2026, 7, 30),
        available_competitor_prices=[],
        unavailable_competitor_count=0,
        all_tracked_competitor_count=0,
        booked_pricing_group_property_count=0,
        all_pricing_group_property_count=1,
        minimum_price=500_000,
        maximum_price=2_000_000,
        pricing_step=1_000,
        configuration=configuration,
    )

    assert result["explanation"]["estimated_host_price_median"] is None
    assert result["explanation"]["base_price"] == 1_234_000
    assert result["price"] == 1_234_000
