from __future__ import annotations

from decimal import Decimal
from statistics import median

from app.schemas import CompetitorObservationInput, CompetitorStayQuoteInput


def accommodation_subtotal(quote: CompetitorStayQuoteInput) -> Decimal:
    """Return accommodation-only value from one raw stay quote."""

    if quote.accommodation_subtotal is not None:
        return quote.accommodation_subtotal
    excluded = sum(
        (
            quote.cleaning_fee or Decimal(0),
            quote.taxes or Decimal(0),
            quote.other_excluded_fees or Decimal(0),
        ),
        Decimal(0),
    )
    subtotal = quote.total_price - excluded
    if subtotal < 0:
        raise ValueError("Excluded stay fees exceed the total price")
    return subtotal


def normalize_competitor_price(
    observation: CompetitorObservationInput,
) -> tuple[Decimal | None, str]:
    """Calculate a comparable nightly price from raw minimum-stay quotes."""

    if not observation.available:
        return None, "unavailable"
    if not observation.stay_quotes:
        raise ValueError("Available observation has no stay quotes")
    one_night_quotes = [
        quote for quote in observation.stay_quotes if quote.stay_nights == 1
    ]
    if one_night_quotes:
        prices = [accommodation_subtotal(quote) for quote in one_night_quotes]
        return Decimal(str(median(prices))), "exact"
    minimum_nights = observation.min_nights
    minimum_stay_quotes = [
        quote
        for quote in observation.stay_quotes
        if minimum_nights is None or quote.stay_nights == minimum_nights
    ]
    if not minimum_stay_quotes:
        raise ValueError("No quote matches the date minimum stay")
    nightly_prices = [
        accommodation_subtotal(quote) / quote.stay_nights
        for quote in minimum_stay_quotes
    ]
    return Decimal(str(median(nightly_prices))), "minimum_stay_average"
