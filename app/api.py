from __future__ import annotations

import hmac
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import clear_session, create_session, require_csrf, require_session, verify_admin
from app.config import get_settings
from app.competitor_scrapes import (
    ensure_no_overlapping_run,
    invoke_collector,
    pending_dates,
    validate_scrape_range,
)
from app.competitors import sync_group_competitor_listings
from app.competitor_prices import normalize_competitor_price
from app.database import get_database_session
from app.hostex import HostexClient, HostexError
from app.hostex_import import import_hostex
from app.jobs import generate_price_recommendations, pricing_configuration, serialized_run
from app.models import AdminSession, CompetitorDateError, CompetitorListing, CompetitorObservation, CompetitorStayQuote, HostexCalendarDay, HostexListing, Override, PricingGroup, Property, Recommendation, Run, Setting
from app.models import RunKind, RunStatus
from app.pricing import merge_pricing_configuration
from app.schemas import CompetitorScrapeCallback, CompetitorScrapeCreate, ModeUpdate, OverrideCreate, PricingConfiguration, PricingConfigurationOverride, PricingGroupCreate, PricingGroupUpdate, PropertyCreate, PropertyRead, PropertyUpdate

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    """Validate administrator login credentials."""

    email: str
    password: str


@router.post("/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_database_session)):
    """Authenticate the administrator and create a browser session."""

    if not verify_admin(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    create_session(response, db)
    return {"authenticated": True, "email": payload.email}


@router.post("/auth/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response, db: Session = Depends(get_database_session), session: AdminSession = Depends(require_session)):
    """Delete the current administrator session and cookies."""

    db.delete(session)
    db.commit()
    clear_session(response)
    return {"authenticated": False}


@router.get("/auth/session")
def session_status(session: AdminSession = Depends(require_session)):
    """Return the current authenticated session status."""

    return {"authenticated": True, "expires_at": session.expires_at}


@router.get("/properties", response_model=list[PropertyRead], dependencies=[Depends(require_session)])
def list_properties(db: Session = Depends(get_database_session)):
    """List managed properties and their pricing policies."""

    return db.scalars(select(Property).order_by(Property.name)).all()


@router.get("/pricing-groups", dependencies=[Depends(require_session)])
def list_pricing_groups(db: Session = Depends(get_database_session)):
    """List pricing groups with competitor and inheritance configuration."""

    groups = db.scalars(select(PricingGroup).order_by(PricingGroup.name)).all()
    return [
        {
            "id": group.id,
            "name": group.name,
            "pricing_settings": group.pricing_settings,
            "competitor_urls": group.competitor_urls,
            "property_count": len(group.properties),
        }
        for group in groups
    ]


@router.post("/pricing-groups", dependencies=[Depends(require_csrf)])
def create_pricing_group(
    payload: PricingGroupCreate, db: Session = Depends(get_database_session)
):
    """Create a pricing group with validated configuration overrides."""

    overrides = PricingConfigurationOverride.model_validate(
        payload.pricing_settings
    ).model_dump(exclude_none=True, mode="json")
    PricingConfiguration.model_validate(
        merge_pricing_configuration(pricing_configuration(db), overrides)
    )
    item = PricingGroup(
        name=payload.name,
        pricing_settings=overrides,
        competitor_urls=list(dict.fromkeys(payload.competitor_urls)),
    )
    db.add(item)
    db.flush()
    try:
        sync_group_competitor_listings(db, item)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.patch("/pricing-groups/{pricing_group_id}", dependencies=[Depends(require_csrf)])
def update_pricing_group(
    pricing_group_id: int,
    payload: PricingGroupUpdate,
    db: Session = Depends(get_database_session),
):
    """Update one pricing group's competitors or inherited settings."""

    item = db.get(PricingGroup, pricing_group_id)
    if not item:
        raise HTTPException(404, "Pricing group not found")
    values = payload.model_dump(exclude_unset=True)
    if "pricing_settings" in values:
        overrides = PricingConfigurationOverride.model_validate(
            values["pricing_settings"] or {}
        ).model_dump(exclude_none=True, mode="json")
        PricingConfiguration.model_validate(
            merge_pricing_configuration(pricing_configuration(db), overrides)
        )
        values["pricing_settings"] = overrides
    if "competitor_urls" in values:
        values["competitor_urls"] = list(
            dict.fromkeys(values["competitor_urls"] or [])
        )
    for key, value in values.items():
        setattr(item, key, value)
    if "competitor_urls" in values:
        try:
            sync_group_competitor_listings(db, item)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    db.commit()
    return {"id": item.id}


@router.post("/properties", response_model=PropertyRead, dependencies=[Depends(require_csrf)])
def create_property(payload: PropertyCreate, db: Session = Depends(get_database_session)):
    """Create a managed property pricing policy."""

    values = payload.model_dump()
    if not db.get(PricingGroup, values["pricing_group_id"]):
        raise HTTPException(404, "Pricing group not found")
    overrides = PricingConfigurationOverride.model_validate(
        values.get("pricing_settings", {})
    ).model_dump(exclude_none=True, mode="json")
    PricingConfiguration.model_validate(
        merge_pricing_configuration(pricing_configuration(db), overrides)
    )
    values["pricing_settings"] = overrides
    item = Property(**values)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/properties/{property_id}", response_model=PropertyRead, dependencies=[Depends(require_csrf)])
def update_property(property_id: int, payload: PropertyUpdate, db: Session = Depends(get_database_session)):
    """Apply a validated partial property policy update."""

    item = db.get(Property, property_id)
    if not item:
        raise HTTPException(404, "Property not found")
    values = payload.model_dump(exclude_unset=True)
    if "pricing_group_id" in values and not db.get(
        PricingGroup, values["pricing_group_id"]
    ):
        raise HTTPException(404, "Pricing group not found")
    if "pricing_settings" in values:
        overrides = PricingConfigurationOverride.model_validate(
            values["pricing_settings"] or {}
        ).model_dump(exclude_none=True, mode="json")
        PricingConfiguration.model_validate(
            merge_pricing_configuration(pricing_configuration(db), overrides)
        )
        values["pricing_settings"] = overrides
    for key, value in values.items():
        setattr(item, key, value)
    if item.min_price > item.max_price:
        raise HTTPException(422, "price bounds must satisfy min <= max")
    db.commit()
    db.refresh(item)
    return item


@router.get("/calendar", dependencies=[Depends(require_session)])
def recommendation_calendar(
    property_id: int | None = None,
    start: date = Query(default_factory=date.today),
    end: date = Query(default_factory=lambda: date.today() + timedelta(days=365)),
    db: Session = Depends(get_database_session),
):
    """Return current and recommended prices with complete explanations."""

    if end < start or (end - start).days > 370:
        raise HTTPException(422, "Date range must be between 0 and 370 days")
    query = (
        select(Recommendation, Property.name)
        .join(Property)
        .where(Recommendation.stay_date.between(start, end))
        .order_by(Recommendation.stay_date, Property.name)
    )
    if property_id:
        query = query.where(Recommendation.property_id == property_id)
    rows = db.execute(query).all()
    return [
        {
            "property_id": item.property_id,
            "property_name": name,
            "date": item.stay_date,
            "actual_price": item.actual_price,
            "recommended_price": item.recommended_price,
            "published_price": item.published_price,
            "explanation": item.explanation,
            "difference": float(item.recommended_price) - float(item.actual_price) if item.actual_price else None,
            "difference_percentage": (
                (float(item.recommended_price) - float(item.actual_price)) / float(item.actual_price)
                if item.actual_price
                else None
            ),
            "warnings": item.explanation.get("warnings", []),
        }
        for item, name in rows
    ]


@router.post("/pricing/run", dependencies=[Depends(require_csrf)])
def run_shadow_pricing(db: Session = Depends(get_database_session)):
    """Generate recommendations without publishing any Hostex changes."""

    mode = db.get(Setting, "mode")
    if mode and mode.value.get("mode") != "shadow":
        raise HTTPException(409, "Manual pricing tests are only allowed in shadow mode")
    with serialized_run(db, RunKind.optimize) as run:
        if run is None:
            raise HTTPException(409, "Another serialized job is running")
        count = generate_price_recommendations(db)
        run.summary = {"optimized": count, "published": 0, "mode": "shadow"}
        return {"run_id": run.id, "optimized": count, "published": 0, "mode": "shadow"}


@router.post("/overrides", dependencies=[Depends(require_csrf)])
def create_override(payload: OverrideCreate, db: Session = Depends(get_database_session)):
    """Create a hard price date-range override."""

    if not db.get(Property, payload.property_id):
        raise HTTPException(404, "Property not found")
    item = Override(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.get("/overrides", dependencies=[Depends(require_session)])
def list_overrides(property_id: int | None = None, db: Session = Depends(get_database_session)):
    """List hard overrides, optionally filtered by property."""

    query = select(Override).order_by(Override.start_date, Override.created_at)
    if property_id:
        query = query.where(Override.property_id == property_id)
    return [
        {
            "id": item.id,
            "property_id": item.property_id,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "price": item.price,
            "reason": item.reason,
            "created_at": item.created_at,
        }
        for item in db.scalars(query)
    ]


@router.delete("/overrides/{override_id}", dependencies=[Depends(require_csrf)])
def delete_override(override_id: int, db: Session = Depends(get_database_session)):
    """Delete one hard override."""

    item = db.get(Override, override_id)
    if not item:
        raise HTTPException(404, "Override not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.get("/runs", dependencies=[Depends(require_session)])
def list_runs(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_database_session)):
    """List recent operational workflow runs."""

    items = db.scalars(select(Run).order_by(Run.started_at.desc()).limit(limit)).all()
    return [
        {
            "id": item.id,
            "kind": item.kind.value,
            "status": item.status.value,
            "started_at": item.started_at,
            "finished_at": item.finished_at,
            "summary": item.summary,
            "error": item.error,
        }
        for item in items
    ]


@router.get("/competitors", dependencies=[Depends(require_session)])
def list_competitors(db: Session = Depends(get_database_session)):
    """List normalized competitors with freshness and collection status."""

    rows = db.execute(
        select(CompetitorListing, PricingGroup.name)
        .join(PricingGroup)
        .order_by(PricingGroup.name, CompetitorListing.external_listing_id)
    ).all()
    return [
        {
            "id": item.id,
            "pricing_group_id": item.pricing_group_id,
            "pricing_group_name": group_name,
            "canonical_url": item.canonical_url,
            "external_listing_id": item.external_listing_id,
            "current_minimum_stay": item.current_minimum_stay,
            "last_scraped_at": item.last_scraped_at,
            "last_error": item.last_error,
        }
        for item, group_name in rows
    ]


@router.post("/competitor-scrapes", dependencies=[Depends(require_csrf)])
def create_competitor_scrape(
    payload: CompetitorScrapeCreate,
    db: Session = Depends(get_database_session),
):
    """Create and asynchronously invoke one granular competitor scrape."""

    settings = get_settings()
    try:
        validate_scrape_range(
            payload.start_date,
            payload.end_date,
            settings.competitor_scrape_max_days,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    listing = db.get(CompetitorListing, payload.competitor_listing_id)
    if not listing:
        raise HTTPException(404, "Competitor listing not found")
    ensure_no_overlapping_run(
        db, listing.id, payload.start_date, payload.end_date
    )
    dates, skipped = pending_dates(
        db,
        listing.id,
        payload.start_date,
        payload.end_date,
        payload.force_refresh,
    )
    summary = {
        "phase": "queued",
        "competitor_listing_id": listing.id,
        "external_listing_id": listing.external_listing_id,
        "start_date": payload.start_date.isoformat(),
        "end_date": payload.end_date.isoformat(),
        "requested_dates": [item.isoformat() for item in dates],
        "skipped_dates": [item.isoformat() for item in skipped],
        "force_refresh": payload.force_refresh,
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
        return {"run_id": run.id, "status": run.status.value, "summary": run.summary}
    run = Run(kind=RunKind.scrape, status=RunStatus.running, summary=summary)
    db.add(run)
    db.commit()
    try:
        invoke_collector(run, listing, dates)
    except Exception as exc:
        run.status = RunStatus.failed
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        run.summary = {**summary, "phase": "invocation_failed"}
        db.commit()
        raise HTTPException(502, "Collector invocation failed; see run history") from exc
    run.summary = {**summary, "phase": "collecting"}
    db.commit()
    return {"run_id": run.id, "status": run.status.value, "summary": run.summary}


@router.get(
    "/competitor-scrapes/{run_id}", dependencies=[Depends(require_session)]
)
def competitor_scrape_status(
    run_id: int, db: Session = Depends(get_database_session)
):
    """Return status and details for one competitor scrape run."""

    run = db.get(Run, run_id)
    if not run or run.kind != RunKind.scrape:
        raise HTTPException(404, "Competitor scrape run not found")
    return {
        "run_id": run.id,
        "status": run.status.value,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "summary": run.summary,
        "error": run.error,
    }


def require_competitor_callback(
    authorization: str | None = Header(default=None),
) -> None:
    """Authenticate the internal collector callback using a bearer token."""

    expected = get_settings().competitor_callback_token
    supplied = (
        authorization.removeprefix("Bearer ")
        if authorization and authorization.startswith("Bearer ")
        else ""
    )
    if not expected or not hmac.compare_digest(supplied, expected):
        raise HTTPException(401, "Invalid callback credentials")


@router.post(
    "/internal/competitor-observations",
    dependencies=[Depends(require_competitor_callback)],
)
def receive_competitor_observations(
    payload: CompetitorScrapeCallback,
    db: Session = Depends(get_database_session),
):
    """Atomically persist an authenticated asynchronous collector result."""

    run = db.get(Run, payload.run_id)
    if not run or run.kind != RunKind.scrape:
        raise HTTPException(404, "Competitor scrape run not found")
    summary = run.summary or {}
    listing = db.get(CompetitorListing, summary.get("competitor_listing_id"))
    if not listing or listing.external_listing_id != payload.external_listing_id:
        raise HTTPException(409, "Callback listing does not match its run")
    if (
        summary.get("start_date") != payload.start_date.isoformat()
        or summary.get("end_date") != payload.end_date.isoformat()
    ):
        raise HTTPException(409, "Callback range does not match its run")
    if run.status != RunStatus.running:
        return {"run_id": run.id, "status": run.status.value, "idempotent": True}
    expected_dates = set(summary.get("requested_dates", []))
    received_dates = {item.stay_date.isoformat() for item in payload.observations}
    error_dates = {item.stay_date.isoformat() for item in payload.date_errors}
    if payload.status in {"succeeded", "partially_succeeded"} and (
        received_dates | error_dates
    ) != expected_dates:
        raise HTTPException(
            422,
            "Callback must classify every requested date exactly once",
        )
    now = datetime.now(timezone.utc)
    if payload.status in {"failed", "source_not_configured"}:
        run.status = RunStatus.failed
        run.error = payload.error or payload.status
        run.finished_at = now
        run.summary = {
            **summary,
            "phase": "completed",
            "result_status": payload.status,
        }
        listing.last_error = run.error
        db.commit()
        return {"run_id": run.id, "status": run.status.value}
    observations = []
    quotes_by_observation: list[tuple[CompetitorObservation, list]] = []
    try:
        for item in payload.observations:
            normalized_price, price_method = normalize_competitor_price(item)
            observation = CompetitorObservation(
                competitor_listing_id=listing.id,
                scrape_run_id=run.id,
                stay_date=item.stay_date,
                price=normalized_price,
                available=item.available,
                available_for_checkin=item.available_for_checkin,
                minimum_stay=item.min_nights,
                currency=item.currency.upper(),
                scraped_at=item.scraped_at,
                parser_version=item.parser_version,
                price_method=price_method,
            )
            observations.append(observation)
            quotes_by_observation.append((observation, item.stay_quotes))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.add_all(observations)
    db.flush()
    db.add_all(
        [
            CompetitorStayQuote(
                competitor_observation_id=observation.id,
                check_out_date=quote.check_out_date,
                stay_nights=quote.stay_nights,
                total_price=quote.total_price,
                accommodation_subtotal=quote.accommodation_subtotal,
                cleaning_fee=quote.cleaning_fee,
                taxes=quote.taxes,
                other_excluded_fees=quote.other_excluded_fees,
                raw=quote.raw,
            )
            for observation, quotes in quotes_by_observation
            for quote in quotes
        ]
    )
    db.add_all(
        [
            CompetitorDateError(
                scrape_run_id=run.id,
                competitor_listing_id=listing.id,
                stay_date=item.stay_date,
                code=item.code,
                message=item.message,
            )
            for item in payload.date_errors
        ]
    )
    checkin_observations = sorted(
        (
            item
            for item in payload.observations
            if (
                item.stay_date >= date.today()
                and item.available_for_checkin
                and item.min_nights is not None
            )
        ),
        key=lambda item: item.stay_date,
    )
    if checkin_observations:
        listing.current_minimum_stay = checkin_observations[0].min_nights
    listing.last_scraped_at = max(item.scraped_at for item in payload.observations)
    date_error_count = len(payload.date_errors)
    listing.last_error = (
        f"{date_error_count} date(s) failed" if date_error_count else None
    )
    run.status = (
        RunStatus.partially_succeeded
        if date_error_count
        else RunStatus.succeeded
    )
    run.error = listing.last_error
    run.finished_at = now
    run.summary = {
        **summary,
        "phase": "completed",
        "result_status": run.status.value,
        "observation_count": len(observations),
        "date_error_count": date_error_count,
    }
    db.commit()
    return {"run_id": run.id, "status": run.status.value}


@router.get("/integrations/hostex", dependencies=[Depends(require_session)])
def hostex_status(db: Session = Depends(get_database_session)):
    """Return non-sensitive Hostex configuration and import status."""

    settings = get_settings()
    last_run = db.scalar(select(Run).where(Run.kind == RunKind.import_).order_by(Run.started_at.desc()).limit(1))
    return {
        "configured": bool(settings.hostex_access_token),
        "mode": "read_only",
        "last_import": None
        if not last_run
        else {
            "id": last_run.id,
            "status": last_run.status.value,
            "started_at": last_run.started_at,
            "finished_at": last_run.finished_at,
            "summary": last_run.summary,
            "error": last_run.error,
        },
    }


@router.get("/hostex/listings", dependencies=[Depends(require_session)])
def hostex_listings(db: Session = Depends(get_database_session)):
    """List imported Hostex channel listings and property mappings."""

    rows = db.execute(
        select(HostexListing, Property.name)
        .outerjoin(Property, HostexListing.property_id == Property.id)
        .order_by(Property.name, HostexListing.channel_type, HostexListing.listing_id)
    ).all()
    return [
        {
            "id": listing.id,
            "property_id": listing.property_id,
            "property_name": property_name,
            "listing_id": listing.listing_id,
            "channel_type": listing.channel_type,
            "readonly": listing.readonly,
            "pricing_ratio": listing.pricing_ratio,
            "imported_at": listing.imported_at,
        }
        for listing, property_name in rows
    ]


@router.get("/hostex/calendar", dependencies=[Depends(require_session)])
def hostex_calendar(
    listing_id: str,
    channel_type: str,
    start: date = Query(default_factory=date.today),
    end: date = Query(default_factory=lambda: date.today() + timedelta(days=31)),
    db: Session = Depends(get_database_session),
):
    """Return imported Hostex calendar days for one listing."""

    if end < start or (end - start).days > 370:
        raise HTTPException(422, "Date range must be between 0 and 370 days")
    rows = db.scalars(
        select(HostexCalendarDay)
        .where(
            HostexCalendarDay.listing_id == listing_id,
            HostexCalendarDay.channel_type == channel_type,
            HostexCalendarDay.stay_date.between(start, end),
        )
        .order_by(HostexCalendarDay.stay_date)
    ).all()
    return [
        {
            "date": row.stay_date,
            "price": row.price,
            "inventory": row.inventory,
            "minimum_stay": row.minimum_stay,
            "imported_at": row.imported_at,
        }
        for row in rows
    ]


@router.post("/imports/hostex", dependencies=[Depends(require_csrf)])
async def run_hostex_import(db: Session = Depends(get_database_session)):
    """Run a guarded read-only Hostex import on demand."""

    settings = get_settings()
    if not settings.hostex_access_token:
        raise HTTPException(409, "HOSTEX_ACCESS_TOKEN is not configured")
    running = db.scalar(
        select(Run).where(Run.kind == RunKind.import_, Run.status == RunStatus.running).limit(1)
    )
    if running:
        raise HTTPException(409, "A Hostex import is already running")
    run = Run(kind=RunKind.import_, status=RunStatus.running)
    db.add(run)
    db.commit()
    client = HostexClient(settings.hostex_access_token, settings.hostex_base_url)
    try:
        summary = await import_hostex(db, client)
        run.status = RunStatus.succeeded
        run.summary = summary
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"run_id": run.id, "status": run.status.value, "summary": summary}
    except HostexError as exc:
        db.rollback()
        run = db.get(Run, run.id)
        run.status = RunStatus.failed
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(502, "Hostex import failed; see run history") from exc
    finally:
        await client.close()


@router.get("/settings/mode", dependencies=[Depends(require_session)])
def get_mode(db: Session = Depends(get_database_session)):
    """Return the current shadow or production mode setting."""

    item = db.get(Setting, "mode")
    return item.value if item else {"mode": "shadow", "activation_date": None}


@router.put("/settings/mode", dependencies=[Depends(require_csrf)])
def set_mode(payload: ModeUpdate, db: Session = Depends(get_database_session)):
    """Persist a validated publishing-mode transition."""

    value = {"mode": payload.mode, "activation_date": payload.activation_date.isoformat() if payload.activation_date else None}
    item = db.get(Setting, "mode")
    if item:
        item.value = value
    else:
        db.add(Setting(key="mode", value=value))
    db.commit()
    return value


@router.get("/settings/pricing", dependencies=[Depends(require_session)])
def get_pricing_configuration(db: Session = Depends(get_database_session)):
    """Return the effective Pricing Engine v2 configuration."""

    return pricing_configuration(db)


@router.put("/settings/pricing", dependencies=[Depends(require_csrf)])
def set_pricing_configuration(
    payload: PricingConfiguration, db: Session = Depends(get_database_session)
):
    """Persist validated Pricing Engine v2 coefficients."""

    value = payload.model_dump(mode="json")
    item = db.get(Setting, "pricing_engine_v2")
    if item:
        item.value = value
    else:
        db.add(Setting(key="pricing_engine_v2", value=value))
    db.commit()
    return value
