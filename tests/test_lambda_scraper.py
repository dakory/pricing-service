"""Tests for the Airbnb competitor collector Lambda.

All network behavior is exercised through a fake transport (monkeypatched
``_fetch_json``); pytest never issues a real HTTP request to Airbnb.
"""

import json
import logging
from decimal import Decimal
from pathlib import Path

import pytest

from lambda_scraper import lambda_function

FIXTURES = Path(__file__).parent / "fixtures" / "airbnb"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


def calendar_event():
    return {
        "operation": "calendar",
        "run_id": 42,
        "competitor_listing_id": 7,
        "external_listing_id": "1721566348393412409",
        "listing_url": "https://www.airbnb.com/rooms/1721566348393412409",
        "start_date": "2026-08-01",
        "month_count": 12,
    }


def quotes_event():
    return {
        "operation": "quotes",
        "run_id": 42,
        "batch_id": 9,
        "competitor_listing_id": 7,
        "external_listing_id": "1721566348393412409",
        "quotes": [
            {
                "quote_id": "q_123",
                "check_in_date": "2026-09-09",
                "check_out_date": "2026-09-10",
            },
            {
                "quote_id": "q_124",
                "check_in_date": "2026-09-10",
                "check_out_date": "2026-09-11",
            },
        ],
    }


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Keep tests fast and deterministic: never actually sleep."""

    monkeypatch.setattr(lambda_function.time, "sleep", lambda *_: None)


def guard_network(monkeypatch):
    """Fail loudly if the transport ever tries to create a real session."""

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Real network access is forbidden in tests")

    monkeypatch.setattr(lambda_function, "_new_session", forbidden)


def stub_transport(monkeypatch, sequence):
    """Replace _fetch_json with a fake; the last response repeats."""

    calls = []

    def fetch(url, params, headers, timeout=10):
        calls.append(url)
        return sequence[min(len(calls) - 1, len(sequence) - 1)]

    monkeypatch.setattr(lambda_function, "_fetch_json", fetch)
    return calls


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def test_calendar_parser_minimal_fixture():
    days = lambda_function.parse_calendar(load_fixture("availability_calendar.json"))
    by_date = {day["stay_date"]: day for day in days}
    assert by_date["2026-07-01"] == {
        "stay_date": "2026-07-01",
        "bookable": False,
        "min_nights": None,
    }
    assert by_date["2026-08-01"] == {
        "stay_date": "2026-08-01",
        "bookable": False,
        "min_nights": None,
    }
    assert by_date["2026-08-02"] == {
        "stay_date": "2026-08-02",
        "bookable": True,
        "min_nights": 1,
    }
    assert by_date["2026-08-03"] == {
        "stay_date": "2026-08-03",
        "bookable": True,
        "min_nights": 1,
    }
    assert by_date["2026-08-04"] == {
        "stay_date": "2026-08-04",
        "bookable": False,
        "min_nights": None,
    }


def test_bookable_day_without_min_nights_is_structural_failure():
    payload = load_fixture("availability_calendar.json")
    august = payload["data"]["merlin"]["pdpAvailabilityCalendar"]["calendarMonths"][1]
    august["days"][2].pop("minNights")  # 2026-08-03 is bookable
    with pytest.raises(lambda_function.StructuralError):
        lambda_function.parse_calendar(payload)


def test_bookable_false_and_null_become_false():
    payload = load_fixture("availability_calendar.json")
    days = lambda_function.parse_calendar(payload)
    bookable_days = [day for day in days if day["bookable"]]
    assert [day["stay_date"] for day in bookable_days] == ["2026-08-02", "2026-08-03"]


def test_checkout_parser_extracts_total_from_amount_micros():
    total, currency = lambda_function.parse_checkout(load_fixture("stay_checkout.json"))
    assert total == "1700400"
    assert currency == "IDR"
    assert Decimal(total) == Decimal("1700400")


def test_smart_promotion_is_not_reapplied_over_total():
    payload = load_fixture("stay_checkout.json")
    breakdown = payload["data"]["presentation"]["stayCheckout"]["sections"][
        "temporaryQuickPayData"
    ]["bootstrapPayments"]["productPriceBreakdown"]
    for item in breakdown["priceBreakdown"]["priceItems"]:
        if item["type"] == "SMART_PROMOTION":
            item["total"]["amountMicros"] = "-999999999999"
    total, _ = lambda_function.parse_checkout(payload)
    assert total == "1700400"


def test_checkout_parser_rejects_non_ok_status():
    payload = load_fixture("stay_checkout.json")
    breakdown = payload["data"]["presentation"]["stayCheckout"]["sections"][
        "temporaryQuickPayData"
    ]["bootstrapPayments"]["productPriceBreakdown"]
    breakdown["status"]["statusCode"] = "PRICE_FAILURE"
    with pytest.raises(lambda_function.QuoteError):
        lambda_function.parse_checkout(payload)


def test_checkout_parser_rejects_non_idr_currency():
    payload = load_fixture("stay_checkout.json")
    breakdown = payload["data"]["presentation"]["stayCheckout"]["sections"][
        "temporaryQuickPayData"
    ]["bootstrapPayments"]["productPriceBreakdown"]
    breakdown["priceBreakdown"]["total"]["total"]["currency"] = "USD"
    with pytest.raises(lambda_function.QuoteError):
        lambda_function.parse_checkout(payload)


# ---------------------------------------------------------------------------
# Event validation
# ---------------------------------------------------------------------------


def test_calendar_event_validation():
    event = calendar_event()
    del event["start_date"]
    with pytest.raises(ValueError, match="start_date"):
        lambda_function.validate_calendar_event(event)
    event = calendar_event()
    event["start_date"] = "not-a-date"
    with pytest.raises(ValueError):
        lambda_function.validate_calendar_event(event)
    event = calendar_event()
    event["month_count"] = 0
    with pytest.raises(ValueError):
        lambda_function.validate_calendar_event(event)


def test_quotes_event_validation_rejects_duplicate_ids():
    event = quotes_event()
    event["quotes"][1]["quote_id"] = "q_123"
    with pytest.raises(ValueError, match="unique"):
        lambda_function.validate_quotes_event(event)


def test_quotes_event_validation_rejects_inverted_dates():
    event = quotes_event()
    event["quotes"][0]["check_in_date"] = "2026-09-11"
    with pytest.raises(ValueError, match="follow"):
        lambda_function.validate_quotes_event(event)


def test_quotes_event_validation_enforces_batch_limit(monkeypatch):
    monkeypatch.setattr(lambda_function, "QUOTE_BATCH_LIMIT", 1)
    with pytest.raises(ValueError, match="limit"):
        lambda_function.validate_quotes_event(quotes_event())


def test_quotes_event_validation_requires_fields():
    event = quotes_event()
    del event["batch_id"]
    with pytest.raises(ValueError, match="batch_id"):
        lambda_function.validate_quotes_event(event)


# ---------------------------------------------------------------------------
# Handler end-to-end via fake transport
# ---------------------------------------------------------------------------


def test_calendar_run_uses_fake_transport_and_succeeds(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    guard_network(monkeypatch)
    stub_transport(monkeypatch, [(200, load_fixture("availability_calendar.json"), {})])
    result = lambda_function.lambda_handler(calendar_event(), None)
    assert result == {"operation": "calendar", "status": "succeeded"}
    payload = sent[0]
    assert payload["operation"] == "calendar"
    assert payload["run_id"] == 42
    assert payload["external_listing_id"] == "1721566348393412409"
    assert payload["status"] == "succeeded"
    assert payload["parser_version"] == "airbnb-calendar-v1"
    assert payload["error"] is None
    days = {day["stay_date"]: day for day in payload["calendar_days"]}
    assert days["2026-08-03"] == {
        "stay_date": "2026-08-03",
        "bookable": True,
        "min_nights": 1,
    }


def test_partial_quote_batch_classifies_each_quote_once(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    checkout = load_fixture("stay_checkout.json")

    def fetch(url, params, headers, timeout=10):
        variables = json.loads(params["variables"])
        if variables["input"]["checkinDate"] == "2026-09-10":
            raise lambda_function.UpstreamError(status=None, message="boom")
        return 200, checkout, {}

    monkeypatch.setattr(lambda_function, "_fetch_json", fetch)
    result = lambda_function.lambda_handler(quotes_event(), None)
    assert result == {"operation": "quotes", "status": "partially_succeeded"}
    payload = sent[0]
    assert payload["status"] == "partially_succeeded"
    assert payload["batch_id"] == 9
    classified = {item["quote_id"] for item in payload["quotes"]} | {
        item["quote_id"] for item in payload["quote_errors"]
    }
    assert classified == {"q_123", "q_124"}
    assert len(payload["quotes"]) == 1
    quote = payload["quotes"][0]
    assert quote["quote_id"] == "q_123"
    assert quote["total_price"] == "1700400"
    assert quote["currency"] == "IDR"
    assert quote["adults"] == 4
    assert quote["parser_version"] == "airbnb-checkout-v1"
    assert len(payload["quote_errors"]) == 1
    assert payload["quote_errors"][0]["quote_id"] == "q_124"
    assert payload["quote_errors"][0]["code"] == "quote_request_failed"


def test_all_quotes_failing_is_a_failed_callback(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    stub_transport(monkeypatch, [(403, None, {})])
    result = lambda_function.lambda_handler(quotes_event(), None)
    assert result == {"operation": "quotes", "status": "failed"}
    payload = sent[0]
    assert payload["status"] == "failed"
    assert payload["quotes"] == []
    assert len(payload["quote_errors"]) == 2


def test_calendar_structural_failure_is_global(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    stub_transport(monkeypatch, [(200, {"data": {}}, {})])
    result = lambda_function.lambda_handler(calendar_event(), None)
    assert result == {"operation": "calendar", "status": "failed"}
    payload = sent[0]
    assert payload["status"] == "failed"
    assert payload["calendar_days"] == []
    assert payload["error"]


def test_global_failure_still_sends_callback(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)

    def fetch(url, params, headers, timeout=10):
        raise lambda_function.UpstreamError(status=None, message="network down")

    monkeypatch.setattr(lambda_function, "_fetch_json", fetch)
    result = lambda_function.lambda_handler(calendar_event(), None)
    assert result == {"operation": "calendar", "status": "failed"}
    payload = sent[0]
    assert payload["status"] == "failed"
    assert payload["calendar_days"] == []
    assert payload["error"]


def test_callback_is_sent_for_quotes_global_failure(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)

    def fetch(url, params, headers, timeout=10):
        raise lambda_function.UpstreamError(status=None, message="network down")

    monkeypatch.setattr(lambda_function, "_fetch_json", fetch)
    result = lambda_function.lambda_handler(quotes_event(), None)
    assert result == {"operation": "quotes", "status": "failed"}
    payload = sent[0]
    assert payload["status"] == "failed"
    assert len(payload["quote_errors"]) == 2


# ---------------------------------------------------------------------------
# Anti-bot hardening
# ---------------------------------------------------------------------------


def test_early_stop_after_two_consecutive_403s(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    calls = stub_transport(monkeypatch, [(403, None, {}), (403, None, {})])
    event = quotes_event()
    event["quotes"] = [
        {"quote_id": "q_1", "check_in_date": "2026-09-01", "check_out_date": "2026-09-02"},
        {"quote_id": "q_2", "check_in_date": "2026-09-02", "check_out_date": "2026-09-03"},
        {"quote_id": "q_3", "check_in_date": "2026-09-03", "check_out_date": "2026-09-04"},
        {"quote_id": "q_4", "check_in_date": "2026-09-04", "check_out_date": "2026-09-05"},
    ]
    result = lambda_function.lambda_handler(event, None)
    assert result == {"operation": "quotes", "status": "failed"}
    assert len(calls) == 2  # stopped after two 403 responses
    payload = sent[0]
    classified = {item["quote_id"] for item in payload["quote_errors"]}
    assert classified == {"q_1", "q_2", "q_3", "q_4"}
    assert payload["quotes"] == []


def test_429_retry_after_is_honored(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    calls = stub_transport(
        monkeypatch,
        [
            (429, None, {"retry-after": "1"}),
            (200, load_fixture("stay_checkout.json"), {}),
        ],
    )
    event = quotes_event()
    event["quotes"] = [event["quotes"][0]]
    result = lambda_function.lambda_handler(event, None)
    assert result == {"operation": "quotes", "status": "succeeded"}
    assert len(calls) == 2  # initial 429 then successful retry
    assert sent[0]["quotes"][0]["total_price"] == "1700400"


def test_transient_5xx_is_retried_once(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    calls = stub_transport(
        monkeypatch,
        [(503, None, {}), (200, load_fixture("stay_checkout.json"), {})],
    )
    event = quotes_event()
    event["quotes"] = [event["quotes"][0]]
    result = lambda_function.lambda_handler(event, None)
    assert result == {"operation": "quotes", "status": "succeeded"}
    assert len(calls) == 2


def test_transport_tripwire_fails_batch_early(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    calls = stub_transport(monkeypatch, [(503, None, {}), (503, None, {}), (503, None, {})])
    event = quotes_event()
    event["quotes"] = [
        {"quote_id": "q_1", "check_in_date": "2026-09-01", "check_out_date": "2026-09-02"},
        {"quote_id": "q_2", "check_in_date": "2026-09-02", "check_out_date": "2026-09-03"},
        {"quote_id": "q_3", "check_in_date": "2026-09-03", "check_out_date": "2026-09-04"},
        {"quote_id": "q_4", "check_in_date": "2026-09-04", "check_out_date": "2026-09-05"},
    ]
    lambda_function.lambda_handler(event, None)
    # Each 503 costs two calls (initial + one retry); three failed quotes then
    # trip the anomaly wire and the fourth is classified without a request.
    assert len(calls) == 6
    payload = sent[0]
    classified = {item["quote_id"] for item in payload["quote_errors"]}
    assert classified == {"q_1", "q_2", "q_3", "q_4"}
    assert payload["quotes"] == []


def test_kill_switch_returns_failed_without_requests(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    monkeypatch.setattr(
        lambda_function,
        "frontend_config",
        lambda: {**lambda_function.DEFAULT_FRONTEND_CONFIG, "collector_paused": True},
    )
    guard_network(monkeypatch)
    result = lambda_function.lambda_handler(calendar_event(), None)
    assert result == {"operation": "calendar", "status": "failed"}
    payload = sent[0]
    assert payload["status"] == "failed"
    assert payload["calendar_days"] == []
    assert "paused" in payload["error"]


def test_transport_impersonates_chrome120(monkeypatch):
    import curl_cffi.requests as cffi_requests

    captured = {}

    def fake_session(**kwargs):
        captured.update(kwargs)

        class Fake:
            def get(self, *_args, **_kwargs):
                raise AssertionError("fake session should not issue requests")

            def close(self):
                pass

        return Fake()

    monkeypatch.setattr(cffi_requests, "Session", fake_session)
    session = lambda_function._new_session()
    assert captured.get("impersonate") == "chrome120"
    assert session is not None


# ---------------------------------------------------------------------------
# Secrets hygiene
# ---------------------------------------------------------------------------


def test_no_secrets_in_logs_or_callbacks(monkeypatch, caplog):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    stub_transport(monkeypatch, [(200, load_fixture("stay_checkout.json"), {})])
    with caplog.at_level(logging.INFO):
        lambda_function.lambda_handler(quotes_event(), None)
    joined = caplog.text
    assert "d306zoyjsyarp7ifhu67rjxn52tv0t20" not in joined
    assert "49245087852b17c93d16b70c1e0067e1aea58f56" not in joined
    payload_json = json.dumps(sent[0])
    assert "d306zoyjsyarp7ifhu67rjxn52tv0t20" not in payload_json
    assert "x-airbnb-api-key" not in payload_json
    assert "amountMicros" not in payload_json
    assert "x-csrf-token" not in payload_json


def test_callback_payload_matches_backend_schema_keys(monkeypatch):
    """Calendar callback contains only the documented top-level keys."""

    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    stub_transport(monkeypatch, [(200, load_fixture("availability_calendar.json"), {})])
    lambda_function.lambda_handler(calendar_event(), None)
    payload = sent[0]
    assert set(payload) == {
        "operation",
        "run_id",
        "external_listing_id",
        "status",
        "calendar_days",
        "scraped_at",
        "parser_version",
        "error",
    }
    day = payload["calendar_days"][0]
    assert set(day) == {"stay_date", "bookable", "min_nights"}
