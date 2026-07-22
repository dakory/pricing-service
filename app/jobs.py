from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.hostex import HostexClient
from app.hostex_import import import_hostex
from app.models import Override, Property, Recommendation, Run, RunKind, RunStatus, Setting
from app.pricing import calculate_price

JOB_LOCK = 7_324_502


@contextmanager
def serialized_run(db: Session, kind: RunKind):
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


def optimize(db: Session, horizon_days: int = 365) -> int:
    today = datetime.now(get_settings().timezone).date()
    count = 0
    for prop in db.scalars(select(Property).where(Property.active.is_(True))):
        for offset in range(horizon_days):
            stay_date = today + timedelta(days=offset)
            override = active_override(db, prop.id, stay_date)
            result = calculate_price(
                stay_date=stay_date,
                today=today,
                base_price=float(prop.base_price),
                min_price=float(prop.min_price),
                max_price=float(prop.max_price),
                rounding_increment=prop.rounding_increment,
                season_factor=float(prop.season_factors.get(str(stay_date.month), 1)),
                weekday_factor=float(prop.weekday_factors.get(str(stay_date.weekday()), 1)),
                default_minimum_stay=int(prop.minimum_stay_rules.get("default", 1)),
                gap_rules=prop.orphan_gap_rules,
                override_price=float(override.price) if override and override.price is not None else None,
                override_minimum_stay=override.minimum_stay if override else None,
            )
            existing = db.scalar(
                select(Recommendation).where(
                    Recommendation.property_id == prop.id, Recommendation.stay_date == stay_date
                )
            )
            if existing:
                existing.recommended_price = result["price"]
                existing.minimum_stay = result["minimum_stay"]
                existing.explanation = result["explanation"]
                existing.calculated_at = datetime.now(timezone.utc)
            else:
                db.add(
                    Recommendation(
                        property_id=prop.id,
                        stay_date=stay_date,
                        recommended_price=result["price"],
                        minimum_stay=result["minimum_stay"],
                        explanation=result["explanation"],
                    )
                )
            count += 1
        db.commit()
    return count


def publishing_enabled(db: Session, today: date) -> bool:
    setting = db.get(Setting, "mode")
    if not setting or setting.value.get("mode") != "production":
        return False
    activation = setting.value.get("activation_date")
    return bool(activation and date.fromisoformat(activation) <= today)


async def publish(db: Session) -> int:
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
    with SessionLocal() as db, serialized_run(db, RunKind.optimize) as run:
        if run is None:
            return
        optimized = optimize(db)
        published = asyncio.run(publish(db))
        run.summary = {"optimized": optimized, "published": published}


def daily_hostex_import():
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
            try:
                return await import_hostex(db, client)
            finally:
                await client.close()

        run.summary = asyncio.run(execute())
