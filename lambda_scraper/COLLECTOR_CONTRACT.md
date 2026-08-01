# Collector adapter contract

The collector Lambda implements two operations: `calendar` (one request for the
full horizon) and `quotes` (sequential stay-checkout requests, one per interval).
The Lambda extracts source facts only. It never chooses a precise/rough method,
builds intervals, or calculates a nightly price — those belong to the backend.

## Input: calendar

```json
{
  "operation": "calendar",
  "run_id": 42,
  "competitor_listing_id": 7,
  "external_listing_id": "1721566348393412409",
  "listing_url": "https://www.airbnb.com/rooms/1721566348393412409",
  "start_date": "2026-08-01",
  "month_count": 12
}
```

One `GET /api/v3/PdpAvailabilityCalendar/{sha}` request is issued with the
persisted-query SHA, API key, client version and static headers from
`tests/fixtures/airbnb/availability_calendar_request.json`. `count` comes from
`month_count`; `month/year` from `start_date`; `listingId` from the event.

## Output: calendar callback

```json
{
  "operation": "calendar",
  "run_id": 42,
  "external_listing_id": "1721566348393412409",
  "status": "succeeded",
  "calendar_days": [
    { "stay_date": "2026-08-03", "bookable": true, "min_nights": 1 }
  ],
  "scraped_at": "2026-08-01T05:00:00Z",
  "parser_version": "airbnb-calendar-v1",
  "error": null
}
```

Mapping per day: `stay_date = calendarDate`; `bookable` is `true` only when the
source field is exactly `true` (`false` and `null` become `false`); `min_nights`
is the source `minNights` for bookable dates and `null` otherwise. A bookable day
without a valid `minNights >= 1`, duplicate dates, or an unknown/truncated
envelope is a structural failure of the whole calendar result — a partial
calendar is never returned. Unavailable days are still returned.

## Input: quotes

```json
{
  "operation": "quotes",
  "run_id": 42,
  "batch_id": 9,
  "competitor_listing_id": 7,
  "external_listing_id": "1721566348393412409",
  "quotes": [
    { "quote_id": "q_123", "check_in_date": "2026-09-09", "check_out_date": "2026-09-10" }
  ]
}
```

The batch is validated (checkout after check-in, unique IDs, size at most
`AIRBNB_QUOTE_BATCH_LIMIT`, default 8) and each quote is fetched with its own
`GET /api/v3/stayCheckout/{sha}` request, strictly sequentially, with a fresh
session per request. Production guest counts are always `4 adults / 0 children /
0 infants / 0 pets` with `guestCurrencyOverride=IDR`; `productId` is
`base64("StayListing:" + external_listing_id)`.

## Output: quote callback

```json
{
  "operation": "quotes",
  "run_id": 42,
  "batch_id": 9,
  "external_listing_id": "1721566348393412409",
  "status": "partially_succeeded",
  "quotes": [
    {
      "quote_id": "q_123",
      "check_in_date": "2026-09-09",
      "check_out_date": "2026-09-10",
      "adults": 4,
      "total_price": "1700400",
      "currency": "IDR",
      "scraped_at": "2026-08-01T05:01:00Z",
      "parser_version": "airbnb-checkout-v1"
    }
  ],
  "quote_errors": [
    { "quote_id": "q_124", "code": "quote_request_failed", "message": "Upstream quote request failed" }
  ],
  "error": null
}
```

A quote succeeds only when
`data.presentation.stayCheckout.sections.temporaryQuickPayData.bootstrapPayments.productPriceBreakdown.status.statusCode`
is `OK`. The price is `priceBreakdown.total.total.amountMicros / 1_000_000`
(Decimal, string) and the adjacent currency must be strictly `IDR`.
`SMART_PROMOTION`, taxes and fees are never re-applied over `TOTAL`. Unknown
structure, non-OK status, wrong currency or a non-positive total are
quote-scoped errors. Every input `quote_id` appears exactly once in `quotes` or
`quote_errors`; an error on one quote never discards the batch's successes.

## Failure semantics

- calendar: 403 / 429 / transport / structural → global `failed` callback with
  empty `calendar_days`;
- quotes: 403 / 429 / transport / structural per checkout → `quote_errors`
  entry; all-failed batches use status `failed`;
- after 2 consecutive 403s the batch stops early and the remainder is classified
  as errors; ≥ 3 transient failures trip an anomaly wire with the same behavior;
- a `collector_paused: true` config flag returns `failed` without any request.

## Anti-bot posture

- No proxy pools; the Lambda's own AWS networking provides the source IP.
- Every request uses a brand-new `curl_cffi` session with
  `impersonate="chrome120"`, closed immediately after use.
- `sleep(uniform(1.8, 3.8))` between consecutive quote requests.
- One retry only for transport / 429 / 5xx within the 50 s deadline budget;
  403 and structural problems are never retried.

## Runtime configuration

API key, client version, persisted-query SHAs, endpoint paths and the kill-switch
flag are loaded once per invocation from the SSM parameter named by
`AIRBNB_FRONTEND_CONFIG_PARAMETER` (JSON, `SecureString`). An empty object
(`{}`) uses the fixture values baked into the image, so the collector works
out of the box and operators can rotate Airbnb parameters without redeploying.

Callbacks are delivered by the Lambda handler itself to `BACKEND_CALLBACK_URL`
with the bearer token from `BACKEND_CALLBACK_TOKEN_PARAMETER`; the event can
never override either. API keys, payment tokens, headers and full upstream
responses are never included in callbacks or logs.
