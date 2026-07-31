from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CompetitorListing, CompetitorObservation, Run, RunKind, RunStatus


def validate_scrape_range(
    start_date: date, end_date: date, maximum_days: int
) -> int:
    """Validate an inclusive scrape range and return its number of days."""

    if end_date < start_date:
        raise ValueError("end_date must not precede start_date")
    count = (end_date - start_date).days + 1
    if count > maximum_days:
        raise ValueError(
            f"Date range exceeds configured maximum of {maximum_days} days"
        )
    return count


def requested_dates(start_date: date, end_date: date) -> list[date]:
    """Return every date in an inclusive collection range."""

    return [
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    ]


def pending_dates(
    db: Session,
    listing_id: int,
    start_date: date,
    end_date: date,
    force_refresh: bool,
) -> tuple[list[date], list[date]]:
    """Split requested dates into pending and recently collected dates."""

    dates = requested_dates(start_date, end_date)
    if force_refresh:
        return dates, []
    settings = get_settings()
    freshness_cutoff = datetime.now(timezone.utc) - timedelta(
        hours=settings.competitor_observation_fresh_hours
    )
    fresh_dates = set(
        db.scalars(
            select(CompetitorObservation.stay_date).where(
                CompetitorObservation.competitor_listing_id == listing_id,
                CompetitorObservation.stay_date.between(start_date, end_date),
                CompetitorObservation.scraped_at >= freshness_cutoff,
            )
        )
    )
    return (
        [item for item in dates if item not in fresh_dates],
        [item for item in dates if item in fresh_dates],
    )


def ensure_no_overlapping_run(
    db: Session, listing_id: int, start_date: date, end_date: date
) -> None:
    """Reject a collection range overlapping an active run for the listing."""

    active_runs = db.scalars(
        select(Run).where(
            Run.kind == RunKind.scrape,
            Run.status == RunStatus.running,
        )
    )
    for run in active_runs:
        summary = run.summary or {}
        if summary.get("competitor_listing_id") != listing_id:
            continue
        active_start = date.fromisoformat(summary["start_date"])
        active_end = date.fromisoformat(summary["end_date"])
        if start_date <= active_end and end_date >= active_start:
            raise HTTPException(
                status_code=409,
                detail="An overlapping competitor scrape is already running",
            )


def invoke_collector(run: Run, listing: CompetitorListing, dates: list[date]) -> None:
    """Invoke the configured Lambda asynchronously with normalized metadata."""

    settings = get_settings()
    if not settings.competitor_scrape_lambda_name:
        raise RuntimeError("COMPETITOR_SCRAPE_LAMBDA_NAME is not configured")
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required to invoke the collector") from exc
    payload = {
        "run_id": run.id,
        "competitor_listing_id": listing.id,
        "external_listing_id": listing.external_listing_id,
        "listing_url": listing.canonical_url,
        "start_date": run.summary["start_date"],
        "end_date": run.summary["end_date"],
        "requested_dates": [item.isoformat() for item in dates],
    }
    response = boto3.client("lambda", region_name=settings.aws_region).invoke(
        FunctionName=settings.competitor_scrape_lambda_name,
        InvocationType="Event",
        Payload=json.dumps(payload).encode(),
    )
    if response.get("StatusCode") != 202:
        raise RuntimeError("Lambda did not accept the asynchronous invocation")
