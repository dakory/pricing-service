# Collector adapter contract

Implement only `collect_listing_calendar(event)` in `lambda_function.py`.
The collector returns source facts and raw stay quotes. It must not calculate
the competitor nightly price or make pricing-engine decisions.

## Input

`requested_dates` is the exact set of check-in dates to collect. It can contain
gaps because observations newer than 24 hours are removed by the backend.

```json
{
  "run_id": 42,
  "competitor_listing_id": 7,
  "external_listing_id": "123456789",
  "listing_url": "https://www.airbnb.com/rooms/123456789",
  "start_date": "2026-08-01",
  "end_date": "2026-08-14",
  "requested_dates": ["2026-08-01", "2026-08-03"]
}
```

## Output

Return observations and recoverable date-specific errors:

```json
{
  "observations": [
    {
      "stay_date": "2026-08-01",
      "currency": "IDR",
      "available": true,
      "available_for_checkin": true,
      "min_nights": 3,
      "stay_quotes": [
        {
          "check_out_date": "2026-08-04",
          "stay_nights": 3,
          "total_price": "4500000",
          "accommodation_subtotal": "3900000",
          "cleaning_fee": "300000",
          "taxes": "300000",
          "other_excluded_fees": "0",
          "raw": {}
        }
      ],
      "scraped_at": "2026-07-30T12:34:56Z",
      "parser_version": "collector-v1"
    }
  ],
  "date_errors": [
    {
      "stay_date": "2026-08-03",
      "code": "quote_unavailable",
      "message": "Could not obtain a stay quote for this date"
    }
  ]
}
```

`total_price` is the complete quoted stay total. Set
`accommodation_subtotal` only when the source identifies it explicitly. Keep
unknown fees as `null`; never guess their values. `raw` may contain a small,
non-sensitive source fragment useful for auditing, but never tokens, cookies,
or full responses.

Available dates require at least one quote. An unavailable date has an empty
`stay_quotes` list. Quote check-out must equal check-in plus `stay_nights`.
Return no `price` or `price_method`: the backend derives and stores both.

The backend uses an identified accommodation subtotal when present. Otherwise
it subtracts identified cleaning fees, taxes, and other excluded fees from the
total. A one-night quote becomes an exact nightly price; otherwise the backend
uses the median accommodation subtotal per night among quotes matching
`min_nights`.

Every requested date must appear exactly once, either in `observations` or
`date_errors`. A recoverable error for one date must not discard valid dates.
The backend stores observations and dated errors atomically; error dates remain
eligible for the next run because they are not considered fresh.

Raise an exception for a global or structural failure, including an unknown
response shape, wrong listing, unknown currency, or a result whose integrity
cannot be established. Global failures must not return partial data. Do not
call the backend callback directly; the existing Lambda handler owns delivery
and terminal error reporting.
