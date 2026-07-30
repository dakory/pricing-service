from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.hostex import HostexClient
from app.hostex_import import import_hostex
from app.models import CompetitorObservation, HostexCalendarDay, HostexListing, Override, PricingGroup, Property, Recommendation, Reservation, Run, RunKind, RunStatus, Setting
from app.pricing import DEFAULT_PRICING_CONFIGURATION, calculate_price, merge_pricing_configuration

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
    """Return the newest manual price override covering a property date."""

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


def pricing_configuration(
    db: Session,
    prop: Property | None = None,
    pricing_group: PricingGroup | None = None,
) -> dict:
    """Merge system, pricing-group, and property configuration levels."""

    setting = db.get(Setting, "pricing_engine_v2")
    global_configuration = merge_pricing_configuration(
        DEFAULT_PRICING_CONFIGURATION,
        setting.value if setting else {},
    )
    group = pricing_group or (prop.pricing_group if prop else None)
    group_configuration = merge_pricing_configuration(
        global_configuration, group.pricing_settings if group else {}
    )
    return merge_pricing_configuration(
        group_configuration, prop.pricing_settings if prop else {}
    )


def latest_competitor_observations(
    db: Session, pricing_group: PricingGroup, start: date, horizon_end: date
) -> dict[date, dict[str, CompetitorObservation]]:
    """Group the latest prepared observation by stay date and competitor URL."""

    if not pricing_group.competitor_urls:
        return {}
    observations = db.scalars(
        select(CompetitorObservation)
        .where(
            CompetitorObservation.pricing_group_id == pricing_group.id,
            CompetitorObservation.url.in_(pricing_group.competitor_urls),
            CompetitorObservation.stay_date >= start,
            CompetitorObservation.stay_date < horizon_end,
        )
        .order_by(CompetitorObservation.scraped_at.desc())
    ).all()
    latest: dict[date, dict[str, CompetitorObservation]] = {}
    for observation in observations:
        latest.setdefault(observation.stay_date, {}).setdefault(
            observation.url, observation
        )
    return latest


def generate_price_recommendations(
    db: Session, horizon_days: int = 365, today: date | None = None
) -> int:
    """Generate and persist Pricing Engine v2 recommendations for free dates."""

    settings = get_settings()
    today = today or datetime.now(settings.timezone).date()
    horizon_end = today + timedelta(days=horizon_days)
    properties = list(db.scalars(select(Property).where(Property.active.is_(True))))
    availability = {
        prop.id: property_availability(db, prop, today, horizon_days)
        for prop in properties
    }
    properties_by_group: dict[int, list[Property]] = {}
    for prop in properties:
        properties_by_group.setdefault(prop.pricing_group_id, []).append(prop)
    db.execute(
        delete(Recommendation).where(
            Recommendation.stay_date >= today,
            Recommendation.stay_date < horizon_end,
        )
    )
    count = 0
    for prop in properties:
        configuration = pricing_configuration(db, prop)
        calendar, unavailable, imported_at = availability[prop.id]
        observations = latest_competitor_observations(
            db, prop.pricing_group, today, horizon_end
        )
        group_properties = properties_by_group[prop.pricing_group_id]
        stale = imported_at is None or imported_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(hours=36)
        for offset in range(horizon_days):
            stay_date = today + timedelta(days=offset)
            if stay_date in unavailable:
                continue
            by_url = observations.get(stay_date, {})
            available_prices = [
                float(observation.price)
                for observation in by_url.values()
                if observation.available and observation.price is not None
            ]
            if (
                configuration["base_price_mode"] == "market_median"
                and not available_prices
            ):
                continue
            override = active_override(db, prop.id, stay_date)
            current = calendar.get(stay_date)
            booked_property_count = sum(
                stay_date in availability[group_property.id][1]
                for group_property in group_properties
            )
            result = calculate_price(
                stay_date=stay_date,
                current_date=today,
                available_competitor_prices=available_prices,
                unavailable_competitor_count=sum(
                    not observation.available for observation in by_url.values()
                ),
                all_tracked_competitor_count=len(
                    prop.pricing_group.competitor_urls
                ),
                booked_pricing_group_property_count=booked_property_count,
                all_pricing_group_property_count=len(group_properties),
                minimum_price=float(prop.min_price),
                maximum_price=float(prop.max_price),
                pricing_step=prop.rounding_increment,
                configuration=configuration,
                manual_override=float(override.price) if override else None,
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
                    "minimum_price": float(prop.min_price),
                    "maximum_price": float(prop.max_price),
                    "current_inventory": current.inventory if current else None,
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
                existing.explanation = result["explanation"]
                existing.calculated_at = datetime.now(timezone.utc)
            else:
                db.add(
                    Recommendation(
                        property_id=prop.id,
                        stay_date=stay_date,
                        actual_price=current.price if current else None,
                        recommended_price=result["price"],
                        explanation=result["explanation"],
                    )
                )
            count += 1
        db.commit()
    return count


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
                    }
                    for row in batch
                ]
                await client.publish_prices(prop.hostex_listing_id, entries)
                now = datetime.now(timezone.utc)
                for row in batch:
                    row.published_price = row.recommended_price
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
