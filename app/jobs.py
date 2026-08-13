from __future__ import annotations

import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import median

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.competitor_scrapes import start_collection_run
from app.database import SessionLocal
from app.hostex import HostexClient
from app.hostex_import import import_hostex
from app.models import CompetitorDateError, CompetitorListing, CompetitorObservation, CompetitorPriceTarget, CompetitorScrapeBatch, CompetitorStayQuote, HostexCalendarDay, HostexListing, Override, PriceAnchor, PricingGroup, Property, Recommendation, Reservation, Run, RunKind, RunStatus, Setting
from app.pricing import DEFAULT_PRICING_CONFIGURATION, calculate_price, merge_pricing_configuration

# PostgreSQL advisory-lock key shared by imports and pricing to serialize heavy jobs.
JOB_LOCK = 7_324_502


@contextmanager
def serialized_run(db: Session, kind: RunKind):
    """Record a job and prevent concurrent heavy work across worker processes."""

    postgres = db.bind.dialect.name == "postgresql"
    lock_connection = None
    acquired = True
    if postgres:
        # Session-level advisory locks belong to a physical connection. Keep a
        # dedicated connection checked out for the whole job so commits made by
        # the ORM session cannot return the lock owner to the connection pool.
        lock_connection = db.bind.connect()
        acquired = lock_connection.scalar(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": JOB_LOCK}
        )
    if not acquired:
        if lock_connection is not None:
            lock_connection.close()
        yield None
        return
    run = Run(kind=kind, status=RunStatus.running)
    db.add(run)
    db.commit()
    # Capture the primary key while the instance is definitely attached and
    # unexpired.  A failed flush can leave the session in a pending-rollback
    # state, making attribute access on ``run`` unsafe in the exception path.
    run_id = run.id
    try:
        yield run
        if run.status == RunStatus.running:
            run.status = RunStatus.succeeded
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        # Record failure using a fresh SQL statement after rollback.  This
        # avoids touching the expired ORM instance that caused the original
        # exception and guarantees that callers never see a run stuck at
        # ``running`` merely because its work failed.
        try:
            db.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(
                    status=RunStatus.failed,
                    error=str(exc),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
        except Exception:
            db.rollback()
        raise
    finally:
        if lock_connection is not None:
            try:
                lock_connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": JOB_LOCK}
                )
                lock_connection.commit()
            finally:
                lock_connection.close()


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


def load_overrides_by_date(
    db: Session, property_ids: list[int], start: date, end: date
) -> dict[tuple[int, date], Override]:
    """Load the newest applicable override for each property/date in one query."""

    if not property_ids:
        return {}
    overrides = db.scalars(
        select(Override)
        .where(
            Override.property_id.in_(property_ids),
            Override.start_date < end,
            Override.end_date >= start,
        )
        .order_by(Override.created_at.desc(), Override.id.desc())
    ).all()
    by_date: dict[tuple[int, date], Override] = {}
    for override in overrides:
        cursor = max(start, override.start_date)
        last_date = min(end - timedelta(days=1), override.end_date)
        while cursor <= last_date:
            by_date.setdefault((override.property_id, cursor), override)
            cursor += timedelta(days=1)
    return by_date


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
    property_overrides = dict(prop.pricing_settings or {}) if prop else {}
    if prop:
        global_values = (setting.value if setting else {})
        group_values = group.pricing_settings if group else {}
        if "minimum_price" not in property_overrides and "minimum_price" not in global_values and "minimum_price" not in group_values:
            property_overrides["minimum_price"] = float(prop.min_price)
        if "maximum_price" not in property_overrides and "maximum_price" not in global_values and "maximum_price" not in group_values:
            property_overrides["maximum_price"] = float(prop.max_price)
        if "rounding_increment" not in property_overrides and "rounding_increment" not in global_values and "rounding_increment" not in group_values:
            property_overrides["rounding_increment"] = prop.rounding_increment
    return merge_pricing_configuration(group_configuration, property_overrides)


def pricing_configuration_with_sources(
    db: Session, prop: Property
) -> dict[str, dict[str, object]]:
    """Return effective property settings together with their inheritance source."""

    setting = db.get(Setting, "pricing_engine_v2")
    global_overrides = setting.value if setting else {}
    group = prop.pricing_group
    property_overrides = dict(prop.pricing_settings or {})
    group_values = group.pricing_settings if group else {}
    if "minimum_price" not in property_overrides and "minimum_price" not in global_overrides and "minimum_price" not in group_values:
        property_overrides["minimum_price"] = float(prop.min_price)
    if "maximum_price" not in property_overrides and "maximum_price" not in global_overrides and "maximum_price" not in group_values:
        property_overrides["maximum_price"] = float(prop.max_price)
    if "rounding_increment" not in property_overrides and "rounding_increment" not in global_overrides and "rounding_increment" not in group_values:
        property_overrides["rounding_increment"] = prop.rounding_increment
    layers = [
        ("global", global_overrides),
        ("pricing_group", group.pricing_settings if group else {}),
        ("property", property_overrides),
    ]
    effective = DEFAULT_PRICING_CONFIGURATION.copy()
    sources = {key: "default" for key in effective}
    for source, overrides in layers:
        effective = merge_pricing_configuration(effective, overrides)
        for key, value in (overrides or {}).items():
            if value is not None:
                sources[key] = source
    return {key: {"value": value, "source": sources.get(key, "default")} for key, value in effective.items()}


@dataclass(frozen=True)
class CompetitorMarketObservation:
    """Combine latest availability with the latest successful dated price."""

    bookable: bool
    price: object | None


def latest_competitor_observations(
    db: Session, pricing_group: PricingGroup, start: date, horizon_end: date
) -> dict[date, dict[str, CompetitorMarketObservation]]:
    """Merge latest calendar availability and latest successful prices."""

    if not pricing_group.competitor_urls:
        return {}
    latest_calendar: dict[tuple[date, str], CompetitorObservation] = {}
    latest_price: dict[tuple[date, str], object] = {}
    partition = (
        CompetitorObservation.stay_date,
        CompetitorListing.canonical_url,
    )
    ranked_calendar = (
        select(
            CompetitorObservation.stay_date.label("stay_date"),
            CompetitorListing.canonical_url.label("canonical_url"),
            CompetitorObservation.bookable.label("bookable"),
            CompetitorObservation.price.label("price"),
            func.row_number()
            .over(partition_by=partition, order_by=CompetitorObservation.scraped_at.desc())
            .label("row_number"),
        )
        .join(CompetitorListing)
        .where(
            CompetitorListing.pricing_group_id == pricing_group.id,
            CompetitorListing.canonical_url.in_(pricing_group.competitor_urls),
            CompetitorObservation.stay_date >= start,
            CompetitorObservation.stay_date < horizon_end,
        )
        .subquery()
    )
    for row in db.execute(
        select(ranked_calendar).where(ranked_calendar.c.row_number == 1)
    ).mappings():
        key = (
            row["stay_date"],
            row["canonical_url"],
        )
        latest_calendar[key] = row

    ranked_prices = (
        select(
            CompetitorObservation.stay_date.label("stay_date"),
            CompetitorListing.canonical_url.label("canonical_url"),
            CompetitorObservation.price.label("price"),
            func.row_number()
            .over(partition_by=partition, order_by=CompetitorObservation.scraped_at.desc())
            .label("row_number"),
        )
        .join(CompetitorListing)
        .where(
            CompetitorListing.pricing_group_id == pricing_group.id,
            CompetitorListing.canonical_url.in_(pricing_group.competitor_urls),
            CompetitorObservation.stay_date >= start,
            CompetitorObservation.stay_date < horizon_end,
            CompetitorObservation.price.is_not(None),
        )
        .subquery()
    )
    for row in db.execute(
        select(ranked_prices).where(ranked_prices.c.row_number == 1)
    ).mappings():
        latest_price[(row["stay_date"], row["canonical_url"])] = row["price"]

    latest: dict[date, dict[str, CompetitorMarketObservation]] = {}
    for (stay_date, url), observation in latest_calendar.items():
        latest.setdefault(stay_date, {})[url] = CompetitorMarketObservation(
            bookable=observation["bookable"],
            price=latest_price.get((stay_date, url)),
        )
    return latest


def generate_price_recommendations(
    db: Session, horizon_days: int = 365, today: date | None = None
) -> int:
    """Generate and persist Pricing Engine v3 recommendations for free dates."""

    settings = get_settings()
    today = today or datetime.now(settings.timezone).date()
    horizon_end = today + timedelta(days=horizon_days)
    properties = list(db.scalars(select(Property).where(Property.active.is_(True))))
    overrides = load_overrides_by_date(
        db, [prop.id for prop in properties], today, horizon_end
    )
    availability = {
        prop.id: property_availability(db, prop, today, horizon_days)
        for prop in properties
    }
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
        saved_anchors = {
            item.stay_date: item
            for item in db.scalars(
                select(PriceAnchor).where(
                    PriceAnchor.property_id == prop.id,
                    PriceAnchor.stay_date >= today,
                    PriceAnchor.stay_date < horizon_end,
                )
            ).all()
        }
        minimum_competitor_count = int(
            configuration["minimum_competitor_count"]
        )
        if configuration.get("suggest_prices") is False:
            continue
        stale = imported_at is None or imported_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(hours=36)
        for offset in range(horizon_days):
            stay_date = today + timedelta(days=offset)
            if stay_date in unavailable:
                continue
            by_url = observations.get(stay_date, {})
            available_prices = [
                float(observation.price)
                for observation in by_url.values()
                if observation.bookable and observation.price is not None
            ]
            override = overrides.get((prop.id, stay_date))
            current = calendar.get(stay_date)
            anchor = saved_anchors.get(stay_date)
            if (
                configuration["base_price_mode"] == "market_median"
                and override is None
                and (anchor is None or anchor.source_type != "manual_base")
                and len(available_prices) >= minimum_competitor_count
            ):
                raw_median = float(median(available_prices))
                now = datetime.now(timezone.utc)
                if anchor is None:
                    anchor = PriceAnchor(
                        property_id=prop.id,
                        stay_date=stay_date,
                        source_type="airbnb_market_median",
                        source_price=raw_median,
                        currency="IDR",
                        source_metadata={"competitor_count": len(available_prices)},
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(anchor)
                    saved_anchors[stay_date] = anchor
                else:
                    anchor.source_type = "airbnb_market_median"
                    anchor.source_price = raw_median
                    anchor.source_metadata = {"competitor_count": len(available_prices)}
                    anchor.updated_at = now
            elif (
                configuration["base_price_mode"] == "market_median"
                and override is None
                and anchor is None
                and current is not None
                and current.price is not None
            ):
                now = datetime.now(timezone.utc)
                anchor = PriceAnchor(
                    property_id=prop.id,
                    stay_date=stay_date,
                    source_type="hostex_fallback",
                    source_price=current.price,
                    currency="IDR",
                    source_metadata={"hostex_imported_at": imported_at.isoformat() if imported_at else None},
                    created_at=now,
                    updated_at=now,
                )
                db.add(anchor)
                saved_anchors[stay_date] = anchor
            anchor_payload = None
            if anchor is not None and (
                configuration["base_price_mode"] == "market_median"
                or anchor.source_type == "manual_base"
            ):
                anchor_payload = {
                    "source_type": anchor.source_type,
                    "source_price": float(anchor.source_price),
                    "source_metadata": anchor.source_metadata or {},
                    "price_source": (
                        "current_market"
                        if anchor.source_type == "airbnb_market_median"
                        and len(available_prices) >= minimum_competitor_count
                        else anchor.source_type
                    ),
                }
            result = calculate_price(
                stay_date=stay_date,
                current_date=today,
                price_anchor=anchor_payload,
                available_competitor_count=len(available_prices),
                minimum_competitor_count=minimum_competitor_count,
                minimum_price=float(configuration["minimum_price"]),
                maximum_price=float(configuration["maximum_price"]),
                pricing_step=int(configuration["rounding_increment"]),
                configuration=configuration,
                manual_override=float(override.price) if override else None,
            )
            if result is None:
                continue
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
            if result["explanation"].get("final_price") in (
                float(prop.min_price),
                float(prop.max_price),
            ):
                warnings.append("price_at_bound")
            result["explanation"].update(
                {
                    "minimum_price": float(configuration["minimum_price"]),
                    "maximum_price": float(configuration["maximum_price"]),
                    "current_inventory": current.inventory if current else None,
                    "hostex_imported_at": imported_at.isoformat() if imported_at else None,
                    "change_percentage": change_pct,
                    "warnings": warnings,
                }
            )
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
    """Return whether publishing is available in the single application mode."""

    return True


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
                        "start_date": row.stay_date.isoformat(),
                        "end_date": row.stay_date.isoformat(),
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


def scheduled_competitor_collection(collection_mode: str) -> dict[str, int]:
    """Queue mode-specific competitor runs for every configured listing."""

    settings = get_settings()
    result = {"started": 0, "skipped": 0, "failed": 0}
    if not settings.competitor_scrape_lambda_name:
        return result
    today = datetime.now(settings.timezone).date()
    if collection_mode == "precise":
        start_date = today
        end_date = today + timedelta(days=settings.competitor_precise_horizon_days)
    elif collection_mode == "rough":
        start_date = today + timedelta(
            days=settings.competitor_precise_horizon_days + 1
        )
        end_date = today + timedelta(days=364)
    else:
        raise ValueError(f"Unknown competitor collection mode: {collection_mode}")
    with SessionLocal() as db:
        listings = list(db.scalars(select(CompetitorListing)))
        for listing in listings:
            try:
                run = start_collection_run(
                    db,
                    listing,
                    start_date,
                    end_date,
                    collection_mode=collection_mode,
                )
                key = "skipped" if run.status == RunStatus.skipped else "started"
                result[key] += 1
            except Exception:
                db.rollback()
                result["failed"] += 1
    return result


def cleanup_competitor_scrape_history(
    db: Session, retention_days: int, now: datetime | None = None
) -> int:
    """Delete old scrape artifacts while retaining dated observations."""

    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=retention_days)
    old_run_ids = select(Run.id).where(
        Run.kind == RunKind.scrape,
        Run.started_at < cutoff,
        Run.status != RunStatus.running,
    )
    deleted = 0
    for model in (
        CompetitorDateError,
        CompetitorPriceTarget,
        CompetitorStayQuote,
        CompetitorScrapeBatch,
    ):
        result = db.execute(
            delete(model).where(model.scrape_run_id.in_(old_run_ids))
        )
        deleted += result.rowcount or 0
    # Observations are retained for pricing, but no longer need to point at a
    # run whose detailed artifacts have been removed.
    db.execute(
        update(CompetitorObservation)
        .where(CompetitorObservation.scrape_run_id.in_(old_run_ids))
        .values(scrape_run_id=None)
    )
    deleted += db.execute(delete(Run).where(Run.id.in_(old_run_ids))).rowcount or 0
    db.commit()
    return deleted


def daily_competitor_collection() -> dict[str, int]:
    """Queue daily calendar and precise-price collection runs."""

    result = scheduled_competitor_collection("precise")
    settings = get_settings()
    with SessionLocal() as db:
        result["pruned"] = cleanup_competitor_scrape_history(
            db, settings.competitor_scrape_retention_days
        )
    return result


def monthly_competitor_collection() -> dict[str, int]:
    """Queue monthly rough-price collection runs."""

    return scheduled_competitor_collection("rough")
