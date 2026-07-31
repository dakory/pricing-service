from decimal import Decimal

from app.competitor_prices import normalize_competitor_price
from app.schemas import CompetitorObservationInput


def observation(**changes):
    """Build one valid raw competitor observation."""

    values = {
        "stay_date": "2026-08-01",
        "currency": "IDR",
        "available": True,
        "available_for_checkin": True,
        "min_nights": 3,
        "stay_quotes": [{
            "check_out_date": "2026-08-04",
            "stay_nights": 3,
            "total_price": "3900000",
            "cleaning_fee": "300000",
            "taxes": "300000",
            "other_excluded_fees": "0",
        }],
        "scraped_at": "2026-07-30T12:00:00Z",
        "parser_version": "fixture-v1",
    }
    values.update(changes)
    return CompetitorObservationInput.model_validate(values)


def test_backend_calculates_minimum_stay_average_without_fees():
    price, method = normalize_competitor_price(observation())
    assert price == Decimal("1100000")
    assert method == "minimum_stay_average"


def test_identified_accommodation_subtotal_takes_precedence():
    item = observation(stay_quotes=[{
        "check_out_date": "2026-08-04",
        "stay_nights": 3,
        "total_price": "4500000",
        "accommodation_subtotal": "3000000",
        "cleaning_fee": "900000",
        "taxes": "600000",
    }])
    assert normalize_competitor_price(item) == (
        Decimal("1000000"),
        "minimum_stay_average",
    )


def test_one_night_quote_is_an_exact_nightly_price():
    item = observation(
        min_nights=1,
        stay_quotes=[{
            "check_out_date": "2026-08-02",
            "stay_nights": 1,
            "total_price": "1250000",
            "cleaning_fee": "250000",
        }],
    )
    assert normalize_competitor_price(item) == (Decimal("1000000"), "exact")


def test_unavailable_date_has_no_normalized_price():
    item = observation(
        available=False,
        available_for_checkin=False,
        min_nights=None,
        stay_quotes=[],
    )
    assert normalize_competitor_price(item) == (None, "unavailable")
