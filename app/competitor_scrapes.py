from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    CompetitorDateError,
    CompetitorListing,
    CompetitorObservation,
    CompetitorPriceTarget,
    CompetitorScrapeBatch,
    CompetitorStayQuote,
    Run,
    RunKind,
    RunStatus,
)


TERMINAL_BATCH_STATUSES = {"succeeded", "partially_succeeded", "failed"}


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


def collection_mode_for_date(stay_date: date, today: date | None = None) -> str:
    """Choose precise or rough collection using the configured WITA horizon."""

    settings = get_settings()
    today = today or datetime.now(settings.timezone).date()
    return (
        "precise"
        if stay_date <= today + timedelta(days=settings.competitor_precise_horizon_days)
        else "rough"
    )


def pending_dates(
    db: Session,
    listing_id: int,
    start_date: date,
    end_date: date,
    force_refresh: bool,
    collection_mode: str | None = None,
    now: datetime | None = None,
) -> tuple[list[date], list[date]]:
    """Split price targets using mode-aware freshness rules."""

    dates = requested_dates(start_date, end_date)
    if force_refresh:
        return dates, []
    settings = get_settings()
    now = now or datetime.now(timezone.utc)
    observations = db.scalars(
        select(CompetitorObservation)
        .where(
            CompetitorObservation.competitor_listing_id == listing_id,
            CompetitorObservation.stay_date.between(start_date, end_date),
        )
        .order_by(CompetitorObservation.scraped_at.desc())
    ).all()
    rows_by_date: dict[date, list[CompetitorObservation]] = {}
    for observation in observations:
        rows_by_date.setdefault(observation.stay_date, []).append(observation)
    fresh_dates: set[date] = set()
    for stay_date in dates:
        dated_rows = rows_by_date.get(stay_date, [])
        latest_calendar = dated_rows[0] if dated_rows else None
        mode = collection_mode or collection_mode_for_date(stay_date)
        if not latest_calendar:
            continue
        age_limit = (
            timedelta(hours=settings.competitor_observation_fresh_hours)
            if mode == "precise"
            else timedelta(days=settings.competitor_rough_fresh_days)
        )
        observation = (
            latest_calendar
            if not latest_calendar.bookable
            else next(
                (
                    item
                    for item in dated_rows
                    if item.collection_mode == mode and item.price is not None
                ),
                None,
            )
        )
        if observation is None or (
            observation.bookable and observation.collection_mode != mode
        ):
            continue
        scraped_at = observation.scraped_at
        if scraped_at.tzinfo is None:
            scraped_at = scraped_at.replace(tzinfo=timezone.utc)
        if scraped_at >= now - age_limit:
            fresh_dates.add(stay_date)
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


def invoke_lambda(event: dict) -> None:
    """Invoke the configured collector Lambda asynchronously."""

    settings = get_settings()
    if not settings.competitor_scrape_lambda_name:
        raise RuntimeError("COMPETITOR_SCRAPE_LAMBDA_NAME is not configured")
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required to invoke the collector") from exc
    response = boto3.client("lambda", region_name=settings.aws_region).invoke(
        FunctionName=settings.competitor_scrape_lambda_name,
        InvocationType="Event",
        Payload=json.dumps(event).encode(),
    )
    if response.get("StatusCode") != 202:
        raise RuntimeError("Lambda did not accept the asynchronous invocation")


def invoke_calendar(run: Run, listing: CompetitorListing) -> None:
    """Invoke the calendar stage for one run."""

    invoke_lambda(
        {
            "operation": "calendar",
            "run_id": run.id,
            "competitor_listing_id": listing.id,
            "external_listing_id": listing.external_listing_id,
            "listing_url": listing.canonical_url,
            "start_date": run.summary["start_date"],
            "month_count": 12,
        }
    )


def start_collection_run(
    db: Session,
    listing: CompetitorListing,
    start_date: date,
    end_date: date,
    *,
    force_refresh: bool = False,
    collection_mode: str | None = None,
) -> Run:
    """Create and invoke one calendar-first collection run."""

    ensure_no_overlapping_run(db, listing.id, start_date, end_date)
    dates, skipped = pending_dates(
        db,
        listing.id,
        start_date,
        end_date,
        force_refresh,
        collection_mode,
    )
    summary = {
        "phase": "calendar_queued",
        "competitor_listing_id": listing.id,
        "external_listing_id": listing.external_listing_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "requested_dates": [item.isoformat() for item in dates],
        "skipped_dates": [item.isoformat() for item in skipped],
        "force_refresh": force_refresh,
        "collection_mode": collection_mode,
    }
    if not dates:
        run = Run(
            kind=RunKind.scrape,
            status=RunStatus.skipped,
            summary={**summary, "phase": "completed", "reason": "all_dates_fresh"},
            finished_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()
        return run
    run = Run(kind=RunKind.scrape, status=RunStatus.running, summary=summary)
    db.add(run)
    db.flush()
    calendar_batch = CompetitorScrapeBatch(
        scrape_run_id=run.id,
        competitor_listing_id=listing.id,
        operation="calendar",
        status="queued",
        expected_quote_ids=[],
    )
    db.add(calendar_batch)
    db.commit()
    try:
        invoke_calendar(run, listing)
    except Exception as exc:
        calendar_batch.status = "failed"
        calendar_batch.error = str(exc)
        calendar_batch.finished_at = datetime.now(timezone.utc)
        run.status = RunStatus.failed
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        run.summary = {**summary, "phase": "invocation_failed"}
        db.commit()
        raise
    calendar_batch.status = "running"
    run.summary = {**summary, "phase": "calendar"}
    db.commit()
    return run


def _continuous_bookable(
    calendar: dict[date, tuple[bool, int | None]], start: date, end: date
) -> bool:
    """Return whether every paid night in a half-open interval is bookable."""

    cursor = start
    while cursor < end:
        if not calendar.get(cursor, (False, None))[0]:
            return False
        cursor += timedelta(days=1)
    return True


def quote_identity(
    run_id: int, listing_id: int, check_in: date, check_out: date
) -> str:
    """Build a stable compact identity for one run-scoped quote interval."""

    adults = get_settings().competitor_quote_adults
    value = f"{run_id}:{listing_id}:{check_in}:{check_out}:{adults}:IDR"
    return f"q_{hashlib.sha256(value.encode()).hexdigest()[:24]}"


def plan_target(
    run_id: int,
    listing_id: int,
    stay_date: date,
    calendar: dict[date, tuple[bool, int | None]],
    mode: str,
) -> tuple[str, list[tuple[str, date, date]]]:
    """Choose one deterministic method and its deduplicable quote intervals."""

    bookable, minimum_stay = calendar.get(stay_date, (False, None))
    if not bookable or minimum_stay is None:
        return "unavailable", []

    def quote(check_in: date, check_out: date) -> tuple[str, date, date]:
        return (
            quote_identity(run_id, listing_id, check_in, check_out),
            check_in,
            check_out,
        )

    if minimum_stay == 1:
        return "single_night", [quote(stay_date, stay_date + timedelta(days=1))]

    average_quote = quote(
        stay_date, stay_date + timedelta(days=minimum_stay)
    )

    if mode == "precise":
        left_start = stay_date - timedelta(days=minimum_stay)
        if _continuous_bookable(
            calendar, left_start, stay_date + timedelta(days=1)
        ):
            return "quote_difference_left", [
                quote(left_start, stay_date + timedelta(days=1)),
                quote(left_start, stay_date),
                average_quote,
            ]
        right_end = stay_date + timedelta(days=minimum_stay + 1)
        if _continuous_bookable(calendar, stay_date, right_end):
            return "quote_difference_right", [
                quote(stay_date, right_end),
                quote(stay_date + timedelta(days=1), right_end),
                average_quote,
            ]

    # Calendar `bookable` describes whether a stay can start on that date; it
    # is not a reliable paid-night availability flag. Let stayCheckout decide
    # whether the target's minimum-stay interval can actually be quoted.
    return "minimum_stay_average", [average_quote]


def create_quote_plan(
    db: Session,
    run: Run,
    listing: CompetitorListing,
    calendar: dict[date, tuple[bool, int | None]],
) -> list[CompetitorScrapeBatch]:
    """Persist price targets, deduplicate intervals, and create quote batches."""

    summary = run.summary or {}
    explicit_mode = summary.get("collection_mode")
    intervals: dict[str, tuple[date, date]] = {}
    targets: list[CompetitorPriceTarget] = []
    for value in summary.get("requested_dates", []):
        stay_date = date.fromisoformat(value)
        mode = explicit_mode or collection_mode_for_date(stay_date)
        method, planned_quotes = plan_target(
            run.id, listing.id, stay_date, calendar, mode
        )
        for quote_id, check_in, check_out in planned_quotes:
            intervals[quote_id] = (check_in, check_out)
        target = CompetitorPriceTarget(
            scrape_run_id=run.id,
            competitor_listing_id=listing.id,
            stay_date=stay_date,
            minimum_stay=calendar.get(stay_date, (False, None))[1],
            collection_mode=mode,
            price_method=method,
            quote_ids=[item[0] for item in planned_quotes],
            status="completed" if not planned_quotes else "pending",
        )
        targets.append(target)
    db.add_all(targets)
    db.flush()

    interval_items = list(intervals.items())
    batch_size = get_settings().competitor_quote_batch_size
    batches: list[CompetitorScrapeBatch] = []
    for offset in range(0, len(interval_items), batch_size):
        batch_items = interval_items[offset : offset + batch_size]
        batch = CompetitorScrapeBatch(
            scrape_run_id=run.id,
            competitor_listing_id=listing.id,
            operation="quotes",
            status="queued",
            expected_quote_ids=[item[0] for item in batch_items],
            quote_requests=[
                {
                    "quote_id": quote_id,
                    "check_in_date": check_in.isoformat(),
                    "check_out_date": check_out.isoformat(),
                }
                for quote_id, (check_in, check_out) in batch_items
            ],
        )
        db.add(batch)
        db.flush()
        batches.append(batch)
    return batches


def invoke_quote_batches(
    batches: Iterable[CompetitorScrapeBatch],
    run: Run,
    listing: CompetitorListing,
) -> None:
    """Invoke all persisted quote batches after the calendar transaction."""

    for batch in batches:
        invoke_lambda(
            {
                "operation": "quotes",
                "run_id": run.id,
                "batch_id": batch.id,
                "competitor_listing_id": listing.id,
                "external_listing_id": listing.external_listing_id,
                "quotes": batch.quote_requests,
            }
        )


def calculate_target_price(
    target: CompetitorPriceTarget, quotes: dict[str, CompetitorStayQuote]
) -> tuple[Decimal | None, str]:
    """Calculate one target and return the method that actually succeeded."""

    if target.price_method == "unavailable":
        return None, "unavailable"
    if target.price_method == "price_unavailable":
        raise ValueError("No continuous minimum-stay interval is available")
    if target.price_method == "single_night":
        try:
            return quotes[target.quote_ids[0]].total_price, "single_night"
        except KeyError as exc:
            raise ValueError("The single-night quote is unavailable") from exc
    if target.price_method in {
        "quote_difference_left",
        "quote_difference_right",
    }:
        try:
            result = (
                quotes[target.quote_ids[0]].total_price
                - quotes[target.quote_ids[1]].total_price
            )
        except KeyError:
            result = None
        if result is not None and result > 0:
            return result, target.price_method
        if len(target.quote_ids) < 3 or not target.minimum_stay:
            raise ValueError("Quote difference and minimum-stay fallback are unavailable")
        try:
            fallback_total = quotes[target.quote_ids[2]].total_price
        except KeyError as exc:
            raise ValueError(
                "Quote difference and minimum-stay fallback are unavailable"
            ) from exc
        return (
            fallback_total / Decimal(target.minimum_stay),
            "minimum_stay_average",
        )
    if target.price_method == "minimum_stay_average":
        if not target.minimum_stay:
            raise ValueError("Average price requires minimum stay")
        try:
            total = quotes[target.quote_ids[0]].total_price
        except KeyError as exc:
            raise ValueError("The minimum-stay quote is unavailable") from exc
        return total / Decimal(target.minimum_stay), "minimum_stay_average"
    raise ValueError(f"Unknown price method: {target.price_method}")


def finalize_run(db: Session, run: Run, listing: CompetitorListing) -> None:
    """Calculate all targets after every quote batch reaches a terminal state."""

    batches = db.scalars(
        select(CompetitorScrapeBatch).where(
            CompetitorScrapeBatch.scrape_run_id == run.id,
            CompetitorScrapeBatch.operation == "quotes",
        )
    ).all()
    if any(batch.status not in TERMINAL_BATCH_STATUSES for batch in batches):
        return
    run.summary = {**(run.summary or {}), "phase": "calculating"}
    targets = db.scalars(
        select(CompetitorPriceTarget).where(
            CompetitorPriceTarget.scrape_run_id == run.id
        )
    ).all()
    quote_rows = db.scalars(
        select(CompetitorStayQuote).where(
            CompetitorStayQuote.scrape_run_id == run.id
        )
    ).all()
    quotes = {item.quote_id: item for item in quote_rows}
    errors = 0
    for target in targets:
        observation = db.scalar(
            select(CompetitorObservation).where(
                CompetitorObservation.scrape_run_id == run.id,
                CompetitorObservation.competitor_listing_id == listing.id,
                CompetitorObservation.stay_date == target.stay_date,
            )
        )
        if observation is None:
            target.status = "failed"
            target.error = "Calendar observation is missing"
            errors += 1
            continue
        try:
            observation.price, actual_method = calculate_target_price(target, quotes)
            observation.price_method = actual_method
            target.price_method = actual_method
            observation.collection_mode = target.collection_mode
            target.status = "completed"
        except ValueError as exc:
            target.status = "failed"
            target.error = str(exc)
            observation.price = None
            observation.price_method = "price_unavailable"
            existing_error = db.scalar(
                select(CompetitorDateError).where(
                    CompetitorDateError.scrape_run_id == run.id,
                    CompetitorDateError.competitor_listing_id == listing.id,
                    CompetitorDateError.stay_date == target.stay_date,
                )
            )
            if existing_error is None:
                db.add(
                    CompetitorDateError(
                        scrape_run_id=run.id,
                        competitor_listing_id=listing.id,
                        stay_date=target.stay_date,
                        code="price_calculation_failed",
                        message=str(exc),
                    )
                )
            errors += 1
    now = datetime.now(timezone.utc)
    listing.last_scraped_at = now
    listing.last_error = f"{errors} date(s) failed" if errors else None
    run.status = RunStatus.partially_succeeded if errors else RunStatus.succeeded
    run.error = listing.last_error
    run.finished_at = now
    run.summary = {
        **(run.summary or {}),
        "phase": "completed",
        "result_status": run.status.value,
        "calendar_day_count": db.query(CompetitorObservation).filter_by(
            scrape_run_id=run.id
        ).count(),
        "price_target_count": len(targets),
        "quote_count": len(quote_rows),
        "quote_batch_count": len(batches),
        "date_error_count": errors,
    }
    db.commit()
