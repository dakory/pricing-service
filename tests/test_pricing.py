from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.pricing import DEFAULT_PRICING_CONFIGURATION, calculate_price, calculate_urgency_adjustment
from app.schemas import PricingConfiguration


def args(**overrides):
    value = dict(
        stay_date=date(2026, 8, 10), current_date=date(2026, 8, 1),
        competitor_prices=[1_000_000, 1_500_000, 2_000_000], saved_market_price=None,
        current_price=900_000, minimum_competitor_count=3, minimum_price=500_000,
        maximum_price=2_000_000, pricing_step=10_000,
        configuration=dict(DEFAULT_PRICING_CONFIGURATION, urgency_adjustment_enabled=False),
    )
    value.update(overrides)
    return value


@pytest.mark.parametrize("days, expected", [(0, -.15), (3, -.15), (4, -.10), (7, -.10), (8, -.05), (14, -.05), (15, -.02), (30, -.02), (31, 0)])
def test_urgency_ranges_are_inclusive(days, expected):
    assert calculate_urgency_adjustment(days, DEFAULT_PRICING_CONFIGURATION) == expected


def test_market_conversion_positioning_and_rounding_then_clamp():
    result = calculate_price(**args(configuration={**DEFAULT_PRICING_CONFIGURATION, "market_positioning_factor": .9, "urgency_adjustment_enabled": False}))
    assert result["explanation"]["airbnb_guest_market_median"] == 1_500_000
    assert result["explanation"]["estimated_host_price_median"] == pytest.approx(1_258_500)
    assert result["explanation"]["base_price"] == pytest.approx(1_132_650)
    assert result["price"] == 1_130_000
    assert result["explanation"]["engine_version"] == "v3"


def test_manual_override_bypasses_rounding_and_bounds():
    result = calculate_price(**args(manual_override=2_345_678, minimum_price=500_000, maximum_price=1_000_000))
    assert result["price"] == 2_345_678
    assert result["explanation"]["price_source"] == "manual_override"


def test_market_falls_back_to_saved_then_current_price_then_none():
    saved = calculate_price(**args(competitor_prices=[1_000_000], minimum_competitor_count=3, saved_market_price=1_200_000))
    assert saved["explanation"]["price_source"] == "saved_market"
    current = calculate_price(**args(competitor_prices=[], minimum_competitor_count=3, saved_market_price=None, current_price=777_777))
    assert current["price"] == 777_777
    assert current["explanation"]["price_source"] == "current_hostex_price"
    assert calculate_price(**args(competitor_prices=[], minimum_competitor_count=3, saved_market_price=None, current_price=None)) is None


def test_manual_base_does_not_need_market():
    result = calculate_price(**args(competitor_prices=[], current_price=None, configuration={**DEFAULT_PRICING_CONFIGURATION, "base_price_mode": "manual", "manual_base_price": 1_234_000, "urgency_adjustment_enabled": False}))
    assert result["price"] == 1_230_000
    assert result["explanation"]["price_source"] == "manual_base"


def test_urgency_gaps_and_disabled_rules_are_zero():
    assert calculate_urgency_adjustment(5, {**DEFAULT_PRICING_CONFIGURATION, "urgency_adjustments": [{"minimum_days": 0, "maximum_days": 3, "adjustment": -.2}]}) == 0
    assert calculate_urgency_adjustment(1, {**DEFAULT_PRICING_CONFIGURATION, "urgency_adjustment_enabled": False}) == 0


def test_rounding_precedes_clamp():
    result = calculate_price(**args(competitor_prices=[1_234_567], minimum_competitor_count=1, minimum_price=1_000_000, maximum_price=1_500_000, pricing_step=100_000, configuration={**DEFAULT_PRICING_CONFIGURATION, "guest_to_host_price_factor": 1.0, "urgency_adjustment_enabled": False}))
    assert result["explanation"]["rounded_price"] == 1_200_000
    assert result["price"] == 1_200_000


def test_configuration_rejects_overlapping_or_excessive_rules_and_demand_fields():
    common = dict(base_price_mode="market_median", guest_to_host_price_factor=.839, market_positioning_factor=1, minimum_competitor_count=10, urgency_adjustment_enabled=True)
    with pytest.raises(ValidationError):
        PricingConfiguration(**common, urgency_adjustments=[{"minimum_days": 0, "maximum_days": 3, "adjustment": -.1}, {"minimum_days": 3, "maximum_days": 5, "adjustment": -.1}])
    with pytest.raises(ValidationError):
        PricingConfiguration(**common, urgency_adjustments=[{"minimum_days": i, "maximum_days": i, "adjustment": 0} for i in range(11)])
    with pytest.raises(ValidationError):
        PricingConfiguration(**common, urgency_adjustments=[], demand_adjustment_enabled=False)
