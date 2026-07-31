from __future__ import annotations

import json
import logging
import os
from datetime import date
from functools import lru_cache
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class SourceNotConfiguredError(RuntimeError):
    """Signal that no authorized competitor data source is installed."""


def collect_listing_calendar(event: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Collect raw observations and recoverable date errors."""

    raise SourceNotConfiguredError(
        "No authorized competitor collection adapter is configured"
    )


@lru_cache(maxsize=1)
def callback_token() -> str:
    """Load and cache the callback bearer token from Parameter Store."""

    import boto3

    parameter_name = os.environ["BACKEND_CALLBACK_TOKEN_PARAMETER"]
    response = boto3.client("ssm").get_parameter(
        Name=parameter_name, WithDecryption=True
    )
    return response["Parameter"]["Value"]


def validate_event(event: dict[str, Any]) -> None:
    """Validate identifiers and requested dates before invoking an adapter."""

    required = {
        "run_id",
        "competitor_listing_id",
        "external_listing_id",
        "listing_url",
        "start_date",
        "end_date",
        "requested_dates",
    }
    missing = sorted(required - event.keys())
    if missing:
        raise ValueError(f"Missing event fields: {', '.join(missing)}")
    start_date = date.fromisoformat(event["start_date"])
    end_date = date.fromisoformat(event["end_date"])
    if end_date < start_date:
        raise ValueError("end_date must not precede start_date")
    requested = [date.fromisoformat(item) for item in event["requested_dates"]]
    if not requested or len(requested) != len(set(requested)):
        raise ValueError("requested_dates must be non-empty and unique")
    if any(item < start_date or item > end_date for item in requested):
        raise ValueError("requested date is outside the declared range")


def validate_collector_result(
    event: dict[str, Any], result: dict[str, list[dict[str, Any]]]
) -> None:
    """Require each requested date to be classified exactly once."""

    if set(result) != {"observations", "date_errors"}:
        raise ValueError("Collector result has an unknown structure")
    observation_dates = [
        item.get("stay_date") for item in result["observations"]
    ]
    error_dates = [item.get("stay_date") for item in result["date_errors"]]
    returned_dates = observation_dates + error_dates
    if None in returned_dates or len(returned_dates) != len(set(returned_dates)):
        raise ValueError("Collector result has missing or duplicate dates")
    if set(returned_dates) != set(event["requested_dates"]):
        raise ValueError("Collector result does not classify every requested date")


def send_result(payload: dict[str, Any]) -> None:
    """POST one authenticated result to the backend callback endpoint."""

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


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Validate a run, call the adapter, and report its terminal result."""

    validate_event(event)
    common = {
        "run_id": event["run_id"],
        "external_listing_id": event["external_listing_id"],
        "start_date": event["start_date"],
        "end_date": event["end_date"],
    }
    LOGGER.info(
        "Starting competitor run %s for %s (%s requested dates)",
        event["run_id"],
        event["external_listing_id"],
        len(event["requested_dates"]),
    )
    try:
        result = collect_listing_calendar(event)
        validate_collector_result(event, result)
        observations = result["observations"]
        date_errors = result["date_errors"]
        payload = {
            **common,
            "status": (
                "partially_succeeded" if date_errors else "succeeded"
            ),
            "observations": observations,
            "date_errors": date_errors,
            "error": None,
        }
    except SourceNotConfiguredError as exc:
        payload = {
            **common,
            "status": "source_not_configured",
            "observations": [],
            "date_errors": [],
            "error": str(exc),
        }
    except Exception:
        LOGGER.exception("Competitor collector failed for run %s", event["run_id"])
        payload = {
            **common,
            "status": "failed",
            "observations": [],
            "date_errors": [],
            "error": "Competitor collector failed",
        }
    send_result(payload)
    LOGGER.info(
        "Completed competitor run %s with status %s",
        event["run_id"],
        payload["status"],
    )
    return {"run_id": event["run_id"], "status": payload["status"]}
