from datetime import date

import pytest
from pydantic import ValidationError

from app.pricing import DEFAULT_PRICING_CONFIGURATION, calculate_price, calculate_urgency_adjustment
from app.schemas import PricingConfiguration


def args(**overrides):
    value = dict(
        stay_date=date(2026, 8, 10), current_date=date(2026, 8, 1),
        price_anchor={"source_type": "airbnb_market_median", "source_price": 1_500_000, "source_metadata": {"competitor_count": 3}, "price_source": "current_market"},
        available_competitor_count=3, minimum_competitor_count=3,
        minimum_price=500_000, maximum_price=2_000_000, pricing_step=10_000,
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
    assert result["explanation"]["anchor_source"] == "airbnb_market_median"


def test_manual_override_bypasses_anchor_calculation():
    result = calculate_price(**args(manual_override=2_345_678, minimum_price=500_000, maximum_price=1_000_000))
    assert result["price"] == 2_345_678
    assert result["explanation"]["price_source"] == "manual_override"


def test_saved_hostex_fallback_anchor_is_reused_and_urgency_is_applied():
    result = calculate_price(**args(
        price_anchor={"source_type": "hostex_fallback", "source_price": 777_777, "source_metadata": {}, "price_source": "hostex_fallback"},
        available_competitor_count=0,
        configuration=DEFAULT_PRICING_CONFIGURATION,
    ))
    assert result["price"] == 740_000
    assert result["explanation"]["price_source"] == "hostex_fallback"
    assert result["explanation"]["urgency_adjustment"] == -.05


def test_manual_base_anchor_is_date_level_and_does_not_use_market_factors():
    result = calculate_price(**args(
        price_anchor={"source_type": "manual_base", "source_price": 1_234_000, "source_metadata": {}, "price_source": "manual_base"},
        available_competitor_count=0,
        configuration={**DEFAULT_PRICING_CONFIGURATION, "urgency_adjustment_enabled": False, "market_positioning_factor": .5},
    ))
    assert result["price"] == 1_230_000
    assert result["explanation"]["anchor_source"] == "manual_base"


def test_manual_property_base_does_not_need_an_anchor():
    result = calculate_price(**args(
        price_anchor=None,
        available_competitor_count=0,
        configuration={**DEFAULT_PRICING_CONFIGURATION, "base_price_mode": "manual", "manual_base_price": 1_234_000, "urgency_adjustment_enabled": False},
    ))
    assert result["price"] == 1_230_000


def test_no_anchor_in_market_mode_returns_no_recommendation():
    assert calculate_price(**args(price_anchor=None, available_competitor_count=0)) is None


def test_configuration_rejects_overlapping_or_excessive_rules_and_demand_fields():
    common = dict(base_price_mode="market_median", guest_to_host_price_factor=.839, market_positioning_factor=1, minimum_competitor_count=10, urgency_adjustment_enabled=True)
    with pytest.raises(ValidationError):
        PricingConfiguration(**common, urgency_adjustments=[{"minimum_days": 0, "maximum_days": 3, "adjustment": -.1}, {"minimum_days": 3, "maximum_days": 5, "adjustment": -.1}])
    with pytest.raises(ValidationError):
        PricingConfiguration(**common, urgency_adjustments=[{"minimum_days": i, "maximum_days": i, "adjustment": 0} for i in range(11)])
    with pytest.raises(ValidationError):
        PricingConfiguration(**common, urgency_adjustments=[], demand_adjustment_enabled=False)
