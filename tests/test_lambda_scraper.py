from lambda_scraper import lambda_function


def event():
    """Return a minimal valid Lambda collection event."""

    return {
        "run_id": 7,
        "competitor_listing_id": 2,
        "external_listing_id": "123",
        "listing_url": "https://www.airbnb.com/rooms/123",
        "start_date": "2026-08-01",
        "end_date": "2026-08-01",
        "requested_dates": ["2026-08-01"],
    }


def test_placeholder_reports_source_not_configured(monkeypatch):
    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    result = lambda_function.lambda_handler(event(), None)
    assert result == {"run_id": 7, "status": "source_not_configured"}
    assert sent[0]["observations"] == []
    assert sent[0]["date_errors"] == []
    assert sent[0]["error"]


def test_date_error_produces_partial_status(monkeypatch):
    """Keep successful dates when the adapter reports a recoverable failure."""

    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    monkeypatch.setattr(
        lambda_function,
        "collect_listing_calendar",
        lambda _event: {
            "observations": [{"stay_date": "2026-08-01"}],
            "date_errors": [{
                "stay_date": "2026-08-02",
                "code": "quote_unavailable",
                "message": "No quote",
            }],
        },
    )
    payload = event()
    payload["end_date"] = "2026-08-02"
    payload["requested_dates"] = ["2026-08-01", "2026-08-02"]
    result = lambda_function.lambda_handler(payload, None)
    assert result["status"] == "partially_succeeded"
    assert sent[0]["status"] == "partially_succeeded"


def test_event_rejects_dates_outside_range():
    payload = event()
    payload["requested_dates"] = ["2026-08-02"]
    try:
        lambda_function.validate_event(payload)
    except ValueError as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("invalid requested date was accepted")


def test_incomplete_collector_result_becomes_global_failure(monkeypatch):
    """Report structurally incomplete adapter output as a global failure."""

    sent = []
    monkeypatch.setattr(lambda_function, "send_result", sent.append)
    monkeypatch.setattr(
        lambda_function,
        "collect_listing_calendar",
        lambda _event: {"observations": [], "date_errors": []},
    )
    result = lambda_function.lambda_handler(event(), None)
    assert result["status"] == "failed"
    assert sent[0]["observations"] == []
    assert sent[0]["date_errors"] == []
