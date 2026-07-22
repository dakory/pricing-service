from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.hostex import HostexClient
from app.hostex_import import import_hostex
from app.models import HostexCalendarDay, HostexListing, Override, Property, Recommendation, Reservation, Run, RunKind, RunStatus, Setting
from app.pricing import calculate_price

# PostgreSQL advisory-lock key shared by imports and pricing to serialize heavy jobs.
JOB_LOCK = 7_324_502


@contextmanager
def serialized_run(db: Session, kind: RunKind):
    """Record a job and prevent concurrent heavy work across worker processes."""

    postgres = db.bind.dialect.name == "postgresql"
    acquired = True
    if postgres:
        acquired = db.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": JOB_LOCK})
    if not acquired:
        yield None
        return
    run = Run(kind=kind, status=RunStatus.running)
    db.add(run)
    db.commit()
    try:
        yield run
        if run.status == RunStatus.running:
            run.status = RunStatus.succeeded
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        run_id = run.id
        db.rollback()
        run = db.get(Run, run_id)
        run.status = RunStatus.failed
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise
    finally:
        if postgres:
            db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": JOB_LOCK})
            db.commit()


def active_override(db: Session, property_id: int, stay_date: date) -> Override | None:
    """Return the newest hard override that covers a property date."""

    return db.scalar(
        select(Override)
        .where(
            Override.property_id == property_id,
            Override.start_date <= stay_date,
            Override.end_date >= stay_date,
        )
        .order_by(Override.created_at.desc())
        .limit(1)
    )


def property_availability(db: Session, prop: Property, start: date, days: int) -> tuple[dict, set[date], datetime | None]:
    """Combine BookingSite inventory and reservations into unavailable dates."""

    listing = db.scalar(
        select(HostexListing).where(
            HostexListing.property_id == prop.id,
            HostexListing.channel_type == "booking_site",
        )
    )
    if not listing:
        return {}, set(), None
    calendar = db.scalars(
        select(HostexCalendarDay).where(
            HostexCalendarDay.listing_id == listing.listing_id,
            HostexCalendarDay.channel_type == "booking_site",
            HostexCalendarDay.stay_date >= start,
            HostexCalendarDay.stay_date < start + timedelta(days=days),
        )
    ).all()
    by_date = {row.stay_date: row for row in calendar}
    unavailable = {row.stay_date for row in calendar if row.inventory is not None and row.inventory <= 0}
    reservations = db.scalars(
        select(Reservation).where(
            Reservation.property_id == prop.id,
            Reservation.status.notin_(["cancelled", "denied", "timeout"]),
            Reservation.check_out > start,
            Reservation.check_in < start + timedelta(days=days),
        )
    ).all()
    for reservation in reservations:
        cursor = max(start, reservation.check_in)
        while cursor < min(start + timedelta(days=days), reservation.check_out):
            unavailable.add(cursor)
            cursor += timedelta(days=1)
    latest = max((row.imported_at for row in calendar), default=None)
    return by_date, unavailable, latest


def rolling_occupancy(stay_date: date, unavailable: set[date], horizon_end: date, window: int = 30) -> float:
    """Calculate forward occupancy within the configured rolling window."""

    end = min(horizon_end, stay_date + timedelta(days=window))
    total = max(1, (end - stay_date).days)
    return sum(stay_date + timedelta(days=offset) in unavailable for offset in range(total)) / total


def orphan_gap_length(stay_date: date, unavailable: set[date], horizon_start: date, horizon_end: date) -> int | None:
    """Return the bounded available gap containing a date, when one exists."""

    if stay_date in unavailable:
        return None
    left = stay_date
    while left > horizon_start and left - timedelta(days=1) not in unavailable:
        left -= timedelta(days=1)
    right = stay_date
    while right + timedelta(days=1) < horizon_end and right + timedelta(days=1) not in unavailable:
        right += timedelta(days=1)
    bounded_left = left > horizon_start or left - timedelta(days=1) in unavailable
    bounded_right = right + timedelta(days=1) >= horizon_end or right + timedelta(days=1) in unavailable
    return (right - left).days + 1 if bounded_left and bounded_right else None


def generate_price_recommendations(
    db: Session, horizon_days: int = 365, today: date | None = None
) -> int:
    """Generate and persist baseline shadow recommendations for active properties."""

    settings = get_settings()
    today = today or datetime.now(settings.timezone).date()
    horizon_end = today + timedelta(days=horizon_days)
    count = 0
    for prop in db.scalars(select(Property).where(Property.active.is_(True))):
        calendar, unavailable, imported_at = property_availability(db, prop, today, horizon_days)
        stale = imported_at is None or imported_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(hours=36)
        for offset in range(horizon_days):
            stay_date = today + timedelta(days=offset)
            override = active_override(db, prop.id, stay_date)
            current = calendar.get(stay_date)
            gap_length = orphan_gap_length(stay_date, unavailable, today, horizon_end)
            occupancy = rolling_occupancy(stay_date, unavailable, horizon_end)
            result = calculate_price(
                stay_date=stay_date,
                today=today,
                base_price=float(prop.base_price),
                min_price=float(prop.min_price),
                max_price=float(prop.max_price),
                rounding_increment=prop.rounding_increment,
                season_factor=float(prop.season_factors.get(str(stay_date.month), 1)),
                weekday_factor=float(prop.weekday_factors.get(str(stay_date.weekday()), 1)),
                apply_booking_pace=False,
                forward_occupancy=occupancy,
                gap_length=gap_length,
                default_minimum_stay=int(prop.minimum_stay_rules.get("default", 1)),
                gap_rules=prop.orphan_gap_rules,
                override_price=float(override.price) if override and override.price is not None else None,
                override_minimum_stay=override.minimum_stay if override else None,
            )
            warnings = []
            if stale:
                warnings.append("stale_hostex_import" if imported_at else "missing_hostex_calendar")
            if current is None:
                warnings.append("missing_current_price")
            change_pct = None
            if current and current.price:
                change_pct = (result["price"] - float(current.price)) / float(current.price)
                if abs(change_pct) >= 0.20:
                    warnings.append("large_price_change")
            if result["explanation"]["bounded_price"] in (float(prop.min_price), float(prop.max_price)):
                warnings.append("price_at_bound")
            result["explanation"].update(
                {
                    "engine_version": "baseline-v1",
                    "canonical_base_price": float(prop.base_price),
                    "minimum_price": float(prop.min_price),
                    "maximum_price": float(prop.max_price),
                    "season_factor": float(prop.season_factors.get(str(stay_date.month), 1)),
                    "weekday_factor": float(prop.weekday_factors.get(str(stay_date.weekday()), 1)),
                    "orphan_gap_length": gap_length,
                    "current_inventory": current.inventory if current else None,
                    "current_minimum_stay": current.minimum_stay if current else None,
                    "default_minimum_stay": int(prop.minimum_stay_rules.get("default", 1)),
                    "final_minimum_stay": result["minimum_stay"],
                    "final_recommended_price": result["price"],
                    "hostex_imported_at": imported_at.isoformat() if imported_at else None,
                    "change_percentage": change_pct,
                    "warnings": warnings,
                }
            )
            existing = db.scalar(
                select(Recommendation).where(
                    Recommendation.property_id == prop.id, Recommendation.stay_date == stay_date
                )
            )
            if existing:
                existing.actual_price = current.price if current else None
                existing.recommended_price = result["price"]
                existing.minimum_stay = result["minimum_stay"]
                existing.explanation = result["explanation"]
                existing.calculated_at = datetime.now(timezone.utc)
            else:
                db.add(
                    Recommendation(
                        property_id=prop.id,
                        stay_date=stay_date,
                        actual_price=current.price if current else None,
                        recommended_price=result["price"],
                        minimum_stay=result["minimum_stay"],
                        explanation=result["explanation"],
                    )
                )
            count += 1
        db.commit()
    return count


def configure_shadow_defaults(db: Session) -> list[dict]:
    """Infer conservative editable policies from current BookingSite prices."""

    configured = []
    for prop in db.scalars(select(Property).order_by(Property.name)):
        prices = db.scalars(
            select(HostexCalendarDay.price)
            .join(
                HostexListing,
                (HostexCalendarDay.listing_id == HostexListing.listing_id)
                & (HostexCalendarDay.channel_type == HostexListing.channel_type),
            )
            .where(
                HostexListing.property_id == prop.id,
                HostexListing.channel_type == "booking_site",
                HostexCalendarDay.price.is_not(None),
            )
        ).all()
        if not prices:
            configured.append({"property_id": prop.id, "name": prop.name, "configured": False})
            continue
        ordered = sorted(int(price) for price in prices)
        base = ordered[len(ordered) // 2]
        prop.base_price = round(base / 50_000) * 50_000
        prop.min_price = round(base * 0.70 / 50_000) * 50_000
        prop.max_price = round(base * 1.60 / 50_000) * 50_000
        prop.rounding_increment = 50_000
        prop.weekday_factors = {str(day): 1.0 for day in range(7)}
        prop.season_factors = {str(month): 1.0 for month in range(1, 13)}
        prop.minimum_stay_rules = {"default": 2}
        prop.orphan_gap_rules = {"max_gap": 3, "price_factor": 0.9, "relax_minimum_stay": True}
        prop.active = True
        configured.append(
            {
                "property_id": prop.id,
                "name": prop.name,
                "configured": True,
                "base_price": prop.base_price,
                "min_price": prop.min_price,
                "max_price": prop.max_price,
            }
        )
    mode = db.get(Setting, "mode")
    value = {"mode": "shadow", "activation_date": None}
    if mode:
        mode.value = value
    else:
        db.add(Setting(key="mode", value=value))
    db.commit()
    return configured


def publishing_enabled(db: Session, today: date) -> bool:
    """Return whether production mode has reached its activation date."""

    setting = db.get(Setting, "mode")
    if not setting or setting.value.get("mode") != "production":
        return False
    activation = setting.value.get("activation_date")
    return bool(activation and date.fromisoformat(activation) <= today)


async def publish_recommendations(db: Session) -> int:
    """Publish active recommendations when all production gates are satisfied."""

    settings = get_settings()
    today = datetime.now(settings.timezone).date()
    if not publishing_enabled(db, today):
        return 0
    if not settings.hostex_access_token:
        raise RuntimeError("HOSTEX_ACCESS_TOKEN is required for production publishing")
    client = HostexClient(settings.hostex_access_token, settings.hostex_base_url)
    published = 0
    try:
        for prop in db.scalars(select(Property).where(Property.active.is_(True))):
            rows = db.scalars(
                select(Recommendation).where(
                    Recommendation.property_id == prop.id,
                    Recommendation.stay_date >= today,
                    Recommendation.stay_date < today + timedelta(days=365),
                )
            ).all()
            for batch_start in range(0, len(rows), 100):
                batch = rows[batch_start : batch_start + 100]
                entries = [
                    {
                        "date": row.stay_date.isoformat(),
                        "price": int(row.recommended_price),
                        "minStay": row.minimum_stay,
                    }
                    for row in batch
                ]
                await client.publish_prices(prop.hostex_listing_id, entries)
                now = datetime.now(timezone.utc)
                for row in batch:
                    row.published_price = row.recommended_price
                    row.published_minimum_stay = row.minimum_stay
                    row.published_at = now
                db.commit()
                published += len(batch)
    finally:
        await client.close()
    return published


def daily_pricing_run():
    """Run the scheduled pricing calculation and gated publication workflow."""

    with SessionLocal() as db, serialized_run(db, RunKind.optimize) as run:
        if run is None:
            return
        optimized = generate_price_recommendations(db)
        published = asyncio.run(publish_recommendations(db))
        run.summary = {"optimized": optimized, "published": published}


def daily_hostex_import():
    """Run the scheduled read-only Hostex import under the shared job lock."""

    settings = get_settings()
    with SessionLocal() as db, serialized_run(db, RunKind.import_) as run:
        if run is None:
            return
        if not settings.hostex_access_token:
            run.status = RunStatus.skipped
            run.summary = {"reason": "HOSTEX_ACCESS_TOKEN is not configured"}
            return
        client = HostexClient(settings.hostex_access_token, settings.hostex_base_url)

        async def execute():
            """Run the import and always release the Hostex HTTP client."""

            try:
                return await import_hostex(db, client)
            finally:
                await client.close()

        run.summary = asyncio.run(execute())
