"""Airbnb competitor collector Lambda.

Implements the two documented operations:

- ``calendar``: one PdpAvailabilityCalendar request per run, parsed into minimal
  calendar days (stay_date / bookable / min_nights).
- ``quotes``: one stayCheckout request per backend-planned quote, strictly
  sequential, returning raw stay totals.

Anti-bot posture (no proxy pools):

- every request uses a brand-new ``curl_cffi`` session impersonating a desktop
  Chrome (``impersonate="chrome120"``) and is closed immediately after use;
- quote requests are processed strictly sequentially with a randomized
  ``sleep(uniform(1.8, 3.8))`` between consecutive requests;
- the Lambda only extracts source facts: the backend owns interval building,
  price-method selection, and all price arithmetic.

Runtime-configurable frontend parameters (API key, client version, persisted-query
SHAs, endpoint paths, kill switch) are loaded once per invocation from SSM so
Airbnb can rotate them without a Lambda redeploy. The callback URL and bearer
token come from environment / SSM and can never be overridden by the event.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import random
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Any

import curl_cffi.requests

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

PARSER_CALENDAR = "airbnb-calendar-v1"
PARSER_CHECKOUT = "airbnb-checkout-v1"
QUOTE_ADULTS = 4

# Safety ceiling for backend-created batches. The backend may choose any lower
# size, so normal batch tuning has a single configuration source.
QUOTE_BATCH_LIMIT = 8
REQUEST_TIMEOUT = float(os.environ.get("AIRBNB_REQUEST_TIMEOUT", "8"))
DEADLINE_BUDGET = float(os.environ.get("AIRBNB_DEADLINE_BUDGET", "50"))
SLEEP_MIN = float(os.environ.get("AIRBNB_SLEEP_MIN", "1.8"))
SLEEP_MAX = float(os.environ.get("AIRBNB_SLEEP_MAX", "3.8"))

# Seeded from the captured request fixtures; overridable per invocation through
# the SSM parameter named by AIRBNB_FRONTEND_CONFIG_PARAMETER.
DEFAULT_FRONTEND_CONFIG: dict[str, Any] = {
    "calendar_path": "/api/v3/PdpAvailabilityCalendar/",
    "checkout_path": "/api/v3/stayCheckout/",
    "calendar_sha": "be60714ead0a30db42ce6471ddad6a8f3855df0ed400b79282dd0bb8cecdf201",
    "checkout_sha": "3992556db8376e5e23529a8ebe5ed375ac32bc12b0753a838e7fde93380f06ba",
    "api_key": "d306zoyjsyarp7ifhu67rjxn52tv0t20",
    "client_version": "49245087852b17c93d16b70c1e0067e1aea58f56",
    "collector_paused": False,
}

TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


class UpstreamError(RuntimeError):
    """A transport-level or HTTP-level failure from the upstream source."""

    def __init__(self, status: int | None = None, message: str = ""):
        self.status = status
        if message:
            super().__init__(message)
        elif status is not None:
            super().__init__(f"Upstream request failed (HTTP {status})")
        else:
            super().__init__("Upstream request failed")


class StructuralError(RuntimeError):
    """The calendar response no longer matches the documented structure."""


class QuoteError(RuntimeError):
    """A checkout quote could not be produced (recoverable, quote-scoped)."""

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


# ---------------------------------------------------------------------------
# Configuration and callback delivery
# ---------------------------------------------------------------------------


def frontend_config() -> dict[str, Any]:
    """Load runtime-configurable Airbnb frontend parameters once per invocation.

    Deliberately not cached across invocations so SSM rotations and the kill
    switch take effect on the very next Lambda invocation.
    """

    config = dict(DEFAULT_FRONTEND_CONFIG)
    parameter_name = os.environ.get("AIRBNB_FRONTEND_CONFIG_PARAMETER", "")
    if not parameter_name:
        return config
    try:
        import boto3

        response = boto3.client("ssm").get_parameter(
            Name=parameter_name, WithDecryption=True
        )
        loaded = json.loads(response["Parameter"]["Value"])
    except Exception as exc:
        LOGGER.warning("Could not load Airbnb frontend config from SSM: %s", exc)
        return config
    if not isinstance(loaded, dict):
        LOGGER.warning("Airbnb frontend config is not a JSON object; using defaults")
        return config
    for key, value in loaded.items():
        if key in config and value is not None:
            config[key] = value
    config["collector_paused"] = bool(
        loaded.get("collector_paused", config["collector_paused"])
    )
    return config


@lru_cache(maxsize=1)
def callback_token() -> str:
    """Load and cache the callback bearer token from Parameter Store."""

    import boto3

    parameter_name = os.environ["BACKEND_CALLBACK_TOKEN_PARAMETER"]
    response = boto3.client("ssm").get_parameter(
        Name=parameter_name, WithDecryption=True
    )
    return response["Parameter"]["Value"]


def send_result(payload: dict[str, Any]) -> None:
    """POST one authenticated result to the backend callback endpoint."""

    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    request = Request(
        os.environ["BACKEND_CALLBACK_URL"],
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {callback_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Backend callback returned {response.status}")
    except (HTTPError, URLError) as exc:
        raise RuntimeError("Backend callback failed") from exc


# ---------------------------------------------------------------------------
# HTTP transport: one request, one brand-new chrome120-impersonating session
# ---------------------------------------------------------------------------


def _new_session():
    """Open a fresh session impersonating a desktop Chrome 120 browser."""

    return curl_cffi.requests.Session(impersonate="chrome120")


def _fetch_json(
    url: str, params: dict[str, str], headers: dict[str, str], timeout: float
) -> tuple[int | None, Any, dict[str, str]]:
    """GET once with a dedicated session; return (status, body, headers)."""

    session = _new_session()
    started = time.monotonic()
    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        response_headers = {
            key.lower(): value for key, value in response.headers.items()
        }
        status = response.status_code
        body = None
        if response.content:
            try:
                body = response.json()
            except ValueError:
                body = None
        LOGGER.info(
            "Upstream %s -> %s in %.1fs",
            url.split("?", 1)[0],
            status,
            time.monotonic() - started,
        )
        return status, body, response_headers
    except curl_cffi.requests.errors.RequestsError as exc:
        raise UpstreamError(status=None, message="Upstream transport failure") from exc
    finally:
        session.close()


def _retry_delay(response_headers: dict[str, str] | None) -> float:
    """Respect Retry-After on 429 (capped), otherwise jittered backoff."""

    value = (response_headers or {}).get("retry-after")
    if value is not None:
        try:
            seconds = int(value)
            return min(max(seconds, 0), 2.0)
        except (TypeError, ValueError):
            pass
    return random.uniform(0.5, 1.5)


def _get_with_retry(
    url: str,
    params: dict[str, str],
    headers: dict[str, str],
    deadline: float,
) -> tuple[int | None, Any]:
    """GET with at most one retry for transient failures within the deadline.

    Never retries 403 (a ban signal) or structural problems; transport errors,
    429 and 5xx get exactly one retry while the deadline budget allows it.
    """

    for attempt in (1, 2):
        if time.monotonic() >= deadline:
            raise UpstreamError(status=None, message="Deadline exceeded")
        try:
            status, body, response_headers = _fetch_json(
                url, params, headers, timeout=REQUEST_TIMEOUT
            )
        except UpstreamError as exc:
            if attempt == 1 and time.monotonic() + 1.5 < deadline:
                time.sleep(random.uniform(0.5, 1.5))
                continue
            raise
        if status in TRANSIENT_STATUSES and attempt == 1:
            delay = _retry_delay(response_headers)
            if time.monotonic() + delay < deadline:
                time.sleep(delay)
                continue
        return status, body
    raise UpstreamError(status=None, message="Request failed after retries")


# ---------------------------------------------------------------------------
# Request building
# ---------------------------------------------------------------------------


def _random_id(length: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(alphabet) for _ in range(length))


def _random_hex(length: int) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def _referer(listing_id: str, check_in: date, check_out: date) -> str:
    return (
        f"https://www.airbnb.com/rooms/{listing_id}"
        f"?source_impression_id=p3_{random.randint(1000000000, 9999999999)}"
        f"&check_in={check_in.isoformat()}&guests=4&adults=4"
        f"&check_out={check_out.isoformat()}&currency=IDR"
    )


def _airbnb_headers(
    config: dict[str, Any], *, referer: str, prefetch: bool = False
) -> dict[str, str]:
    """The captured x-airbnb-* business header set with fresh per-request IDs.

    Browser headers (User-Agent, sec-ch-ua, ...) are intentionally left to
    curl_cffi's chrome120 impersonation so they stay consistent with the TLS
    fingerprint.
    """

    headers = {
        "content-type": "application/json",
        "ect": "4g",
        "referer": referer,
        "x-airbnb-api-key": config["api_key"],
        "x-airbnb-client-trace-id": _random_id(26),
        "x-airbnb-graphql-platform": "web",
        "x-airbnb-graphql-platform-client": "minimalist-niobe",
        "x-airbnb-network-log-link": "0002a451" + _random_hex(18),
        "x-airbnb-supports-airlock-v2": "true",
        "x-client-request-id": "1w" + _random_id(24),
        "x-client-version": config["client_version"],
        "x-csrf-token": "",
        "x-csrf-without-token": "1",
    }
    if prefetch:
        headers["x-airbnb-prefetch"] = "true"
    return headers


def _calendar_request(
    event: dict[str, Any], config: dict[str, Any]
) -> tuple[str, dict[str, str], dict[str, str]]:
    """Build the single PdpAvailabilityCalendar request for one run."""

    start = date.fromisoformat(event["start_date"])
    month_count = int(event.get("month_count") or 12)
    listing_id = event["external_listing_id"]
    sha = config["calendar_sha"]
    url = f"https://www.airbnb.com{config['calendar_path']}{sha}"
    variables = {
        "request": {
            "count": month_count,
            "listingId": listing_id,
            "month": start.month,
            "year": start.year,
            "returnPropertyLevelCalendarIfApplicable": False,
        }
    }
    extensions = {"persistedQuery": {"version": 1, "sha256Hash": sha}}
    params = {
        "operationName": "PdpAvailabilityCalendar",
        "locale": "en",
        "currency": "IDR",
        "variables": json.dumps(variables),
        "extensions": json.dumps(extensions),
    }
    headers = _airbnb_headers(
        config, referer=_referer(listing_id, start, start + timedelta(days=1))
    )
    return url, params, headers


def _checkout_request(
    config: dict[str, Any], listing_id: str, check_in: date, check_out: date
) -> tuple[str, dict[str, str], dict[str, str]]:
    """Build one stayCheckout request for a single quote interval."""

    sha = config["checkout_sha"]
    url = f"https://www.airbnb.com{config['checkout_path']}{sha}"
    product_id = base64.b64encode(f"StayListing:{listing_id}".encode()).decode()
    variables = {
        "input": {
            "businessTravel": {"workTrip": False},
            "checkinDate": check_in.isoformat(),
            "checkoutDate": check_out.isoformat(),
            "guestCounts": {
                "numberOfAdults": QUOTE_ADULTS,
                "numberOfChildren": 0,
                "numberOfInfants": 0,
                "numberOfPets": 0,
            },
            "guestCurrencyOverride": "IDR",
            "listingDetail": {},
            "lux": {},
            "metadata": {"internalFlags": ["LAUNCH_LOGIN_PHONE_AUTH"]},
            "org": {},
            "productId": product_id,
            "addOn": {
                "carbonOffsetParams": {"isSelected": False},
                "guestDonationParams": {"isSelected": False},
            },
            "quickPayData": None,
        }
    }
    extensions = {"persistedQuery": {"version": 1, "sha256Hash": sha}}
    params = {
        "operationName": "stayCheckout",
        "locale": "en",
        "currency": "IDR",
        "variables": json.dumps(variables),
        "extensions": json.dumps(extensions),
    }
    headers = _airbnb_headers(
        config, referer=_referer(listing_id, check_in, check_out), prefetch=True
    )
    return url, params, headers


# ---------------------------------------------------------------------------
# Parsers (fail closed on unknown structures)
# ---------------------------------------------------------------------------


def parse_calendar(payload: Any) -> list[dict[str, Any]]:
    """Parse calendarMonths[].days[] into minimal day records.

    Raises StructuralError (global failure) for any unknown or truncated
    envelope, duplicate dates, invalid dates, or a bookable day without a valid
    minNights.
    """

    if not isinstance(payload, dict):
        raise StructuralError("Calendar response is not an object")
    try:
        months = payload["data"]["merlin"]["pdpAvailabilityCalendar"][
            "calendarMonths"
        ]
    except (KeyError, TypeError) as exc:
        raise StructuralError("Unknown Airbnb calendar response structure") from exc
    if not isinstance(months, list):
        raise StructuralError("Unknown Airbnb calendar response structure")

    days_by_date: dict[str, dict[str, Any]] = {}
    for month in months:
        if not isinstance(month, dict):
            raise StructuralError("Unknown Airbnb calendar response structure")
        month_days = month.get("days")
        if not isinstance(month_days, list):
            raise StructuralError("Unknown Airbnb calendar response structure")
        for day in month_days:
            if not isinstance(day, dict):
                raise StructuralError("Unknown Airbnb calendar response structure")
            stay_date = day.get("calendarDate")
            if not isinstance(stay_date, str):
                raise StructuralError("Calendar day is missing a date")
            try:
                date.fromisoformat(stay_date)
            except ValueError as exc:
                raise StructuralError("Calendar day has an invalid date") from exc
            if stay_date in days_by_date:
                raise StructuralError("Calendar response contains duplicate dates")
            bookable = day.get("bookable") is True
            min_nights = day.get("minNights")
            if bookable and (not isinstance(min_nights, int) or min_nights < 1):
                raise StructuralError(
                    "Bookable calendar day is missing a valid minNights"
                )
            days_by_date[stay_date] = {
                "stay_date": stay_date,
                "bookable": bookable,
                "min_nights": min_nights if bookable else None,
            }
    return [days_by_date[key] for key in sorted(days_by_date)]


def parse_checkout(payload: Any) -> tuple[str, str]:
    """Extract the TOTAL guest amount as an IDR string from a stayCheckout.

    Returns (total_price, currency). Raises QuoteError (quote-scoped) for an
    unknown structure, a non-OK status, a non-IDR currency, or a non-positive
    total. SMART_PROMOTION and other price items are never re-applied: TOTAL is
    already the usable guest amount.
    """

    if not isinstance(payload, dict):
        raise QuoteError("Upstream quote response is not an object")
    try:
        breakdown = payload["data"]["presentation"]["stayCheckout"]["sections"][
            "temporaryQuickPayData"
        ]["bootstrapPayments"]["productPriceBreakdown"]
        status_code = breakdown["status"]["statusCode"]
        total = breakdown["priceBreakdown"]["total"]["total"]
        amount_micros = total["amountMicros"]
        currency = total["currency"]
    except (KeyError, TypeError) as exc:
        raise QuoteError("Unknown Airbnb checkout response structure") from exc
    if status_code != "OK":
        raise QuoteError(
            f"Airbnb checkout status is {status_code}", retryable=True
        )
    if currency != "IDR":
        raise QuoteError(f"Unexpected checkout currency: {currency}")
    try:
        micros = Decimal(str(amount_micros))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise QuoteError("Invalid checkout amountMicros") from exc
    total_price = micros / Decimal("1_000_000")
    if total_price <= 0:
        raise QuoteError("Checkout total is not positive")
    return str(total_price), currency


# ---------------------------------------------------------------------------
# Event validation
# ---------------------------------------------------------------------------


def validate_calendar_event(event: dict[str, Any]) -> None:
    """Validate identifiers and requested dates for the calendar stage."""

    required = {
        "run_id",
        "competitor_listing_id",
        "external_listing_id",
        "listing_url",
        "start_date",
    }
    missing = sorted(required - event.keys())
    if missing:
        raise ValueError(f"Missing calendar event fields: {', '.join(missing)}")
    try:
        date.fromisoformat(event["start_date"])
    except (TypeError, ValueError) as exc:
        raise ValueError("start_date must be an ISO date") from exc
    month_count = event.get("month_count", 12)
    if (
        not isinstance(month_count, int)
        or isinstance(month_count, bool)
        or month_count < 1
    ):
        raise ValueError("month_count must be a positive integer")


def validate_quotes_event(event: dict[str, Any]) -> None:
    """Validate a quote batch: unique IDs, ordered dates, bounded size."""

    required = {
        "run_id",
        "batch_id",
        "competitor_listing_id",
        "external_listing_id",
        "quotes",
    }
    missing = sorted(required - event.keys())
    if missing:
        raise ValueError(f"Missing quotes event fields: {', '.join(missing)}")
    quotes = event["quotes"]
    if not isinstance(quotes, list) or not quotes:
        raise ValueError("quotes must be a non-empty list")
    if len(quotes) > QUOTE_BATCH_LIMIT:
        raise ValueError(f"Quote batch exceeds the configured limit of {QUOTE_BATCH_LIMIT}")
    quote_ids: list[str] = []
    for item in quotes:
        if not isinstance(item, dict):
            raise ValueError("Each quote must be an object")
        quote_id = item.get("quote_id")
        if not isinstance(quote_id, str) or not quote_id:
            raise ValueError("Each quote requires a quote_id")
        quote_ids.append(quote_id)
        try:
            check_in = date.fromisoformat(item["check_in_date"])
            check_out = date.fromisoformat(item["check_out_date"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Quote dates must be ISO dates") from exc
        if check_out <= check_in:
            raise ValueError("check_out_date must follow check_in_date")
    if len(quote_ids) != len(set(quote_ids)):
        raise ValueError("Quote IDs must be unique")


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def run_calendar(event: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect the full calendar horizon with a single request."""

    validate_calendar_event(event)
    url, params, headers = _calendar_request(event, config)
    deadline = time.monotonic() + DEADLINE_BUDGET
    status, body = _get_with_retry(url, params, headers, deadline)
    if status != 200 or body is None:
        raise StructuralError(f"Calendar request failed (HTTP {status})")
    return parse_calendar(body)


def _quote_error(quote_id: str, code: str, message: str) -> dict[str, str]:
    return {"quote_id": quote_id, "code": code, "message": message}


def _parse_checkout_with_retry(
    url: str,
    params: dict[str, str],
    headers: dict[str, str],
    deadline: float,
    initial_body: Any,
) -> tuple[str, str]:
    """Retry one recognized HTTP-200 checkout rejection with jitter."""

    try:
        return parse_checkout(initial_body)
    except QuoteError as exc:
        if not exc.retryable:
            raise
        delay = random.uniform(0.5, 1.5)
        if time.monotonic() + delay >= deadline:
            raise
        time.sleep(delay)
        status, body = _get_with_retry(url, params, headers, deadline)
        if status != 200 or body is None:
            raise UpstreamError(status=status)
        return parse_checkout(body)


def run_quotes(event: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Collect one batch of stay quotes, strictly sequentially."""

    validate_quotes_event(event)
    requested = event["quotes"]
    deadline = time.monotonic() + DEADLINE_BUDGET
    quotes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    consecutive_403 = 0
    transport_failures = 0
    total = len(requested)

    for index, item in enumerate(requested):
        quote_id = item["quote_id"]
        if time.monotonic() >= deadline:
            for remaining in requested[index:]:
                errors.append(
                    _quote_error(
                        remaining["quote_id"],
                        "quote_request_failed",
                        "Lambda deadline reached",
                    )
                )
            break
        try:
            check_in = date.fromisoformat(item["check_in_date"])
            check_out = date.fromisoformat(item["check_out_date"])
            url, params, headers = _checkout_request(
                config, event["external_listing_id"], check_in, check_out
            )
            started = time.monotonic()
            status, body = _get_with_retry(url, params, headers, deadline)
            LOGGER.info(
                "Quote %s: HTTP %s in %.1fs", quote_id, status, time.monotonic() - started
            )
            if status == 403:
                consecutive_403 += 1
                errors.append(
                    _quote_error(
                        quote_id,
                        "quote_request_failed",
                        "Airbnb rejected the request (HTTP 403)",
                    )
                )
                if consecutive_403 >= 2:
                    for remaining in requested[index + 1 :]:
                        errors.append(
                            _quote_error(
                                remaining["quote_id"],
                                "quote_request_failed",
                                "Stopped after repeated 403 responses",
                            )
                        )
                    break
                continue
            consecutive_403 = 0
            if status != 200 or body is None:
                if status in TRANSIENT_STATUSES:
                    transport_failures += 1
                errors.append(
                    _quote_error(
                        quote_id,
                        "quote_request_failed",
                        f"Upstream quote request failed (HTTP {status})",
                    )
                )
                if transport_failures >= 3:
                    for remaining in requested[index + 1 :]:
                        errors.append(
                            _quote_error(
                                remaining["quote_id"],
                                "quote_request_failed",
                                "Stopped after repeated transport failures",
                            )
                        )
                    break
                continue
            total_price, currency = _parse_checkout_with_retry(
                url, params, headers, deadline, body
            )
            quotes.append(
                {
                    "quote_id": quote_id,
                    "check_in_date": item["check_in_date"],
                    "check_out_date": item["check_out_date"],
                    "adults": QUOTE_ADULTS,
                    "total_price": total_price,
                    "currency": currency,
                    "scraped_at": _now_utc(),
                    "parser_version": PARSER_CHECKOUT,
                }
            )
        except UpstreamError:
            transport_failures += 1
            consecutive_403 = 0
            errors.append(
                _quote_error(quote_id, "quote_request_failed", "Upstream quote request failed")
            )
            if transport_failures >= 3:
                for remaining in requested[index + 1 :]:
                    errors.append(
                        _quote_error(
                            remaining["quote_id"],
                            "quote_request_failed",
                            "Stopped after repeated transport failures",
                        )
                    )
                break
        except QuoteError as exc:
            consecutive_403 = 0
            errors.append(_quote_error(quote_id, "checkout_rejected", str(exc)))
        except ValueError as exc:
            consecutive_403 = 0
            errors.append(_quote_error(quote_id, "quote_request_failed", str(exc)))
        if index < total - 1:
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    if quotes and errors:
        status = "partially_succeeded"
    elif quotes:
        status = "succeeded"
    else:
        status = "failed"
    return {
        "operation": "quotes",
        "run_id": event["run_id"],
        "batch_id": event["batch_id"],
        "external_listing_id": event["external_listing_id"],
        "status": status,
        "quotes": quotes,
        "quote_errors": errors,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _failure_payload(
    event: dict[str, Any], message: str, error_code: str = "quote_request_failed"
) -> dict[str, Any]:
    """Build a typed failed callback for a known operation."""

    operation = event.get("operation")
    if operation == "calendar":
        return {
            "operation": "calendar",
            "run_id": event.get("run_id"),
            "external_listing_id": event.get("external_listing_id"),
            "status": "failed",
            "calendar_days": [],
            "scraped_at": _now_utc(),
            "parser_version": PARSER_CALENDAR,
            "error": message,
        }
    if operation == "quotes":
        quotes = event.get("quotes") or []
        return {
            "operation": "quotes",
            "run_id": event.get("run_id"),
            "batch_id": event.get("batch_id"),
            "external_listing_id": event.get("external_listing_id"),
            "status": "failed",
            "quotes": [],
            "quote_errors": [
                _quote_error(item["quote_id"], error_code, message)
                for item in quotes
                if isinstance(item, dict) and item.get("quote_id")
            ],
            "error": message,
        }
    raise ValueError(f"Cannot build a failure callback for operation {operation!r}")


def lambda_handler(event: dict[str, Any] | None, _context: Any) -> dict[str, Any]:
    """Validate a run, collect source facts, and report its terminal result."""

    event = event or {}
    operation = event.get("operation")
    config = frontend_config()
    if config.get("collector_paused"):
        payload = _failure_payload(event, "Collector paused by operator", "collector_paused")
        send_result(payload)
        LOGGER.warning("Collector paused by operator; sent failed callback for %s", operation)
        return {"operation": operation, "status": payload["status"]}
    started = time.monotonic()
    try:
        if operation == "calendar":
            days = run_calendar(event, config)
            payload = {
                "operation": "calendar",
                "run_id": event["run_id"],
                "external_listing_id": event["external_listing_id"],
                "status": "succeeded",
                "calendar_days": days,
                "scraped_at": _now_utc(),
                "parser_version": PARSER_CALENDAR,
                "error": None,
            }
        elif operation == "quotes":
            payload = run_quotes(event, config)
        else:
            raise ValueError(f"Unknown operation: {operation!r}")
    except Exception as exc:
        LOGGER.exception("Collector failed for operation %s", operation)
        payload = _failure_payload(event, str(exc) or "Collector failed")
    send_result(payload)
    LOGGER.info(
        "Completed %s in %.1fs with status %s",
        operation,
        time.monotonic() - started,
        payload.get("status"),
    )
    return {"operation": operation, "status": payload["status"]}
