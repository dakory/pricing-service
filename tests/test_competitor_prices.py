from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.competitor_scrapes import calculate_target_price, plan_target


def calendar(start: date, count: int, minimum_stay: int = 2):
    """Return a continuous bookable calendar mapping."""

    from datetime import timedelta

    return {
        start + timedelta(days=offset): (True, minimum_stay)
        for offset in range(count)
    }


def target(method: str, quote_ids: list[str], minimum_stay: int = 2):
    """Build the attributes required by the pure price calculator."""

    return SimpleNamespace(
        price_method=method,
        quote_ids=quote_ids,
        minimum_stay=minimum_stay,
    )


def quotes(**values):
    """Build quote rows keyed by identity."""

    return {
        key: SimpleNamespace(total_price=Decimal(str(value)))
        for key, value in values.items()
    }


def test_single_night_uses_the_guest_total():
    assert calculate_target_price(
        target("single_night", ["one"], 1), quotes(one="1700400")
    ) == (Decimal("1700400"), "single_night")


def test_quote_difference_calculates_the_added_target_night():
    rows = quotes(long="6100000", short="4500000")
    assert calculate_target_price(
        target("quote_difference_left", ["long", "short"]), rows
    ) == (Decimal("1600000"), "quote_difference_left")
    assert calculate_target_price(
        target("quote_difference_right", ["long", "short"]), rows
    ) == (Decimal("1600000"), "quote_difference_right")


def test_minimum_stay_average_uses_decimal_arithmetic():
    assert calculate_target_price(
        target("minimum_stay_average", ["stay"], 3),
        quotes(stay="5100001"),
    ) == (Decimal("5100001") / Decimal(3), "minimum_stay_average")


def test_non_positive_quote_difference_without_fallback_is_rejected():
    with pytest.raises(ValueError, match="fallback"):
        calculate_target_price(
            target("quote_difference_left", ["long", "short"]),
            quotes(long="100", short="100"),
        )


def test_precise_plan_uses_left_then_right_then_average():
    stay_date = date(2026, 8, 10)
    left_calendar = calendar(date(2026, 8, 8), 5)
    method, intervals = plan_target(7, 2, stay_date, left_calendar, "precise")
    assert method == "quote_difference_left"
    assert [(item[1], item[2]) for item in intervals] == [
        (date(2026, 8, 8), date(2026, 8, 11)),
        (date(2026, 8, 8), date(2026, 8, 10)),
        (date(2026, 8, 10), date(2026, 8, 12)),
    ]

    right_calendar = calendar(date(2026, 8, 10), 4)
    method, intervals = plan_target(7, 2, stay_date, right_calendar, "precise")
    assert method == "quote_difference_right"
    assert [(item[1], item[2]) for item in intervals] == [
        (date(2026, 8, 10), date(2026, 8, 13)),
        (date(2026, 8, 11), date(2026, 8, 13)),
        (date(2026, 8, 10), date(2026, 8, 12)),
    ]

    fallback_calendar = calendar(date(2026, 8, 10), 2)
    method, intervals = plan_target(
        7, 2, stay_date, fallback_calendar, "precise"
    )
    assert method == "minimum_stay_average"
    assert (intervals[0][1], intervals[0][2]) == (
        date(2026, 8, 10),
        date(2026, 8, 12),
    )


def test_rough_plan_never_requests_difference_pairs():
    stay_date = date(2026, 11, 10)
    method, intervals = plan_target(
        7, 2, stay_date, calendar(stay_date, 3), "rough"
    )
    assert method == "minimum_stay_average"
    assert len(intervals) == 1


def test_precise_difference_falls_back_to_minimum_stay_average():
    price, method = calculate_target_price(
        target("quote_difference_left", ["long", "short", "fallback"], 2),
        quotes(long="6100000", fallback="5000000"),
    )
    assert price == Decimal("2500000")
    assert method == "minimum_stay_average"


def test_average_plan_does_not_treat_checkin_bookability_as_nightly_availability():
    stay_date = date(2026, 8, 10)
    method, intervals = plan_target(
        7, 2, stay_date, {stay_date: (True, 3)}, "rough"
    )
    assert method == "minimum_stay_average"
    assert (intervals[0][1], intervals[0][2]) == (
        stay_date,
        date(2026, 8, 13),
    )
