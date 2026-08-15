from __future__ import annotations

import hmac
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    clear_session,
    create_session,
    require_csrf,
    require_session,
    verify_admin,
)
from app.config import get_settings
from app.competitor_scrapes import (
    collection_mode_for_date,
    create_quote_plan,
    finalize_run,
    invoke_quote_batches,
    start_group_collection_run,
    quote_identity,
    start_collection_run,
    validate_scrape_range,
)
from app.competitors import sync_group_competitor_listings
from app.database import get_database_session
from app.hostex import HostexClient, HostexError
from app.hostex_import import import_booking_site_calendars, import_hostex
from app.jobs import (
    generate_price_recommendations,
    pricing_configuration,
    publish_recommendations,
    pricing_configuration_with_sources,
    serialized_run,
)
from app.models import (
    AdminSession,
    CompetitorDateError,
    CompetitorListing,
    CompetitorObservation,
    CompetitorPriceTarget,
    CompetitorScrapeBatch,
    CompetitorStayQuote,
    HostexCalendarDay,
    HostexListing,
    Override,
    PriceAnchor,
    PriceAssignment,
    PricingGroup,
    Property,
    Recommendation,
    Run,
    RunKind,
    RunStatus,
    Setting,
)
from app.pricing import merge_pricing_configuration
from app.schemas import (
    CompetitorCalendarCallback,
    CompetitorQuoteBatchCallback,
    CompetitorScrapeCreate,
    OverrideCreate,
    PriceAnchorCreate,
    PriceAssignmentCreate,
    PricingConfiguration,
    PricingConfigurationOverride,
    PricingGroupCreate,
    PricingGroupUpdate,
    PropertyCreate,
    PropertyRead,
    PropertyUpdate,
)

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
        raw_settings = values["pricing_settings"] or {}
        # An explicit null setting removes an override and restores inheritance
        # from the parent configuration level.
        existing_settings = dict(item.pricing_settings or {})
        for key, value in raw_settings.items():
            if value is None:
                existing_settings.pop(key, None)
            else:
                existing_settings[key] = value
        overrides = PricingConfigurationOverride.model_validate(
            existing_settings
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
        raw_settings = values["pricing_settings"] or {}
        existing_settings = dict(item.pricing_settings or {})
        for key, value in raw_settings.items():
            if value is None:
                existing_settings.pop(key, None)
            else:
                existing_settings[key] = value
        overrides = PricingConfigurationOverride.model_validate(
            existing_settings
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


@router.get("/pricing-calendar", dependencies=[Depends(require_session)])
def pricing_calendar(
    start: date = Query(default_factory=date.today),
    end: date | None = None,
    db: Session = Depends(get_database_session),
):
    """Return the complete BookingSite calendar used by the redesigned dashboard."""

    end = end or (start + timedelta(days=43))
    if end < start or (end - start).days > 59:
        raise HTTPException(422, "Date range must be between 0 and 59 days")

    properties = db.scalars(
        select(Property).where(Property.active.is_(True)).order_by(Property.name)
    ).all()
    property_ids = [item.id for item in properties]
    if not property_ids:
        return {"start": start, "end": end, "properties": [], "days": []}

    calendars = db.scalars(
        select(HostexCalendarDay).where(
            HostexCalendarDay.property_id.in_(property_ids),
            HostexCalendarDay.channel_type == "booking_site",
            HostexCalendarDay.stay_date.between(start, end),
        )
    ).all()
    recommendations = db.scalars(
        select(Recommendation).where(
            Recommendation.property_id.in_(property_ids),
            Recommendation.stay_date.between(start, end),
        )
    ).all()
    overrides = db.scalars(
        select(Override).where(
            Override.property_id.in_(property_ids),
            Override.start_date <= end,
            Override.end_date >= start,
        )
    ).all()
    anchors = db.scalars(
        select(PriceAnchor).where(
            PriceAnchor.property_id.in_(property_ids),
            PriceAnchor.stay_date.between(start, end),
        )
    ).all()
    assignments = db.scalars(
        select(PriceAssignment).where(
            PriceAssignment.property_id.in_(property_ids),
            PriceAssignment.stay_date.between(start, end),
        )
    ).all()
    calendar_by_key = {(row.property_id, row.stay_date): row for row in calendars}
    recommendation_by_key = {(row.property_id, row.stay_date): row for row in recommendations}
    anchor_by_key = {(row.property_id, row.stay_date): row for row in anchors}
    assignment_by_key = {(row.property_id, row.stay_date): row for row in assignments}
    overrides_by_property = {}
    for override in overrides:
        overrides_by_property.setdefault(override.property_id, []).append(override)

    days = []
    cursor = start
    while cursor <= end:
        for property_item in properties:
            key = (property_item.id, cursor)
            calendar = calendar_by_key.get(key)
            recommendation = recommendation_by_key.get(key)
            override = next(
                (item for item in overrides_by_property.get(property_item.id, [])
                 if item.start_date <= cursor <= item.end_date),
                None,
            )
            anchor = anchor_by_key.get(key)
            assignment = assignment_by_key.get(key)
            current_price = calendar.price if calendar else None
            available = bool(calendar and (calendar.inventory is None or calendar.inventory > 0))
            recommended_price = recommendation.recommended_price if recommendation else None
            difference = (
                recommended_price - current_price
                if recommended_price is not None and current_price is not None
                else None
            )
            days.append({
                "property_id": property_item.id,
                "property_name": property_item.name,
                "pricing_group_id": property_item.pricing_group_id,
                "pricing_group_name": property_item.pricing_group.name if property_item.pricing_group else f"Pricing group {property_item.pricing_group_id}",
                "stay_date": cursor,
                "available": available,
                "inventory": calendar.inventory if calendar else None,
                "minimum_stay": calendar.minimum_stay if calendar else None,
                "current_price": current_price,
                "recommended_price": recommended_price,
                "published_price": recommendation.published_price if recommendation else None,
                "difference": difference,
                "difference_percentage": (
                    difference / current_price
                    if difference is not None and current_price
                    else None
                ),
                "override": None if override is None else {
                    "id": override.id,
                    "price": override.price,
                    "start_date": override.start_date,
                    "end_date": override.end_date,
                    "reason": override.reason,
                    "suggest_prices": override.suggest_prices,
                },
                "anchor": None if anchor is None else {
                    "id": anchor.id,
                    "source_type": anchor.source_type,
                    "source_price": anchor.source_price,
                    "suggest_prices": anchor.suggest_prices,
                },
                "assignment": None if assignment is None else {
                    "id": assignment.id,
                    "price": assignment.price,
                    "suggest_prices": assignment.suggest_prices,
                    "reason": assignment.reason,
                    "created_at": assignment.created_at,
                    "updated_at": assignment.updated_at,
                },
                "warnings": recommendation.explanation.get("warnings", []) if recommendation else [],
                "explanation": recommendation.explanation if recommendation else {},
            })
        cursor += timedelta(days=1)

    return {
        "start": start,
        "end": end,
        "properties": [
            {
                "id": item.id,
                "name": item.name,
                "pricing_group_id": item.pricing_group_id,
                "pricing_group_name": item.pricing_group.name if item.pricing_group else f"Pricing group {item.pricing_group_id}",
                "booking_site_listing_id": item.booking_site_listing_id,
                "thumbnail_url": item.thumbnail_url,
            }
            for item in properties
        ],
        "days": days,
    }


@router.post("/pricing/run", dependencies=[Depends(require_csrf)])
def run_pricing(db: Session = Depends(get_database_session)):
    """Generate pricing recommendations without publishing Hostex changes."""
    with serialized_run(db, RunKind.optimize) as run:
        if run is None:
            raise HTTPException(409, "Another serialized job is running")
        count = generate_price_recommendations(db)
        run.summary = {"optimized": count, "published": 0}
        return {"run_id": run.id, "optimized": count, "published": 0}


@router.post("/pricing/publish", dependencies=[Depends(require_csrf)])
async def publish_pricing(db: Session = Depends(get_database_session)):
    """Publish current recommendations after the dashboard confirmation step."""

    settings = get_settings()
    if not settings.hostex_access_token:
        raise HTTPException(409, "HOSTEX_ACCESS_TOKEN is not configured")
    with serialized_run(db, RunKind.publish) as run:
        if run is None:
            raise HTTPException(409, "Another serialized job is running")
        try:
            published = await publish_recommendations(db)
            run.summary = {"published": published}
            return {"run_id": run.id, "published": published}
        except HostexError as exc:
            raise HTTPException(502, "Hostex publishing failed; see Activity") from exc


@router.post("/overrides", dependencies=[Depends(require_csrf)])
def create_override(payload: OverrideCreate, db: Session = Depends(get_database_session)):
    """Create a hard price date-range override."""

    if not db.get(Property, payload.property_id):
        raise HTTPException(404, "Property not found")
    values = payload.model_dump()
    values.pop("suggest_prices", None)
    values.pop("start_date", None)
    values.pop("end_date", None)
    available_days = db.scalars(
        select(HostexCalendarDay).where(
            HostexCalendarDay.property_id == payload.property_id,
            HostexCalendarDay.channel_type == "booking_site",
            HostexCalendarDay.stay_date.between(payload.start_date, payload.end_date),
        )
    ).all()
    available = [row.stay_date for row in available_days if row.inventory is None or row.inventory > 0]
    for stay_date in available:
        db.add(Override(**values, start_date=stay_date, end_date=stay_date, suggest_prices=False))
        existing = db.scalar(select(PriceAssignment).where(PriceAssignment.property_id == payload.property_id, PriceAssignment.stay_date == stay_date))
        if existing:
            existing.price = payload.price
            existing.suggest_prices = False
            existing.reason = payload.reason
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.add(PriceAssignment(property_id=payload.property_id, stay_date=stay_date, price=payload.price, suggest_prices=False, reason=payload.reason, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
    db.commit()
    return {"count": len(available), "skipped_unavailable": (payload.end_date - payload.start_date).days + 1 - len(available)}


@router.post("/price-assignments", dependencies=[Depends(require_csrf)])
def create_price_assignment(
    payload: PriceAssignmentCreate, db: Session = Depends(get_database_session)
):
    """Create or replace one unified assignment for every available date in a range."""

    if not db.get(Property, payload.property_id):
        raise HTTPException(404, "Property not found")
    now = datetime.now(timezone.utc)
    cursor = payload.start_date
    count = 0
    skipped = 0
    while cursor <= payload.end_date:
        calendar = db.scalar(select(HostexCalendarDay).where(
            HostexCalendarDay.property_id == payload.property_id,
            HostexCalendarDay.channel_type == "booking_site",
            HostexCalendarDay.stay_date == cursor,
        ))
        if calendar is None or (calendar.inventory is not None and calendar.inventory <= 0):
            skipped += 1
            cursor += timedelta(days=1)
            continue
        item = db.scalar(select(PriceAssignment).where(
            PriceAssignment.property_id == payload.property_id,
            PriceAssignment.stay_date == cursor,
        ))
        if item:
            item.price = payload.price
            item.suggest_prices = payload.suggest_prices
            item.reason = payload.reason
            item.updated_at = now
        else:
            db.add(PriceAssignment(
                property_id=payload.property_id,
                stay_date=cursor,
                price=payload.price,
                suggest_prices=payload.suggest_prices,
                reason=payload.reason,
                created_at=now,
                updated_at=now,
            ))
        # Keep legacy tables from shadowing the unified assignment during rollout.
        for legacy_override in db.scalars(select(Override).where(Override.property_id == payload.property_id, Override.start_date <= cursor, Override.end_date >= cursor)).all():
            db.delete(legacy_override)
        for legacy_anchor in db.scalars(select(PriceAnchor).where(PriceAnchor.property_id == payload.property_id, PriceAnchor.stay_date == cursor)).all():
            db.delete(legacy_anchor)
        count += 1
        cursor += timedelta(days=1)
    db.commit()
    return {"count": count, "skipped_unavailable": skipped}


@router.get("/price-assignments", dependencies=[Depends(require_session)])
def list_price_assignments(property_id: int | None = None, db: Session = Depends(get_database_session)):
    """List unified date-level assignments."""

    query = select(PriceAssignment).order_by(PriceAssignment.stay_date)
    if property_id:
        query = query.where(PriceAssignment.property_id == property_id)
    return [{
        "id": item.id, "property_id": item.property_id, "stay_date": item.stay_date,
        "price": item.price, "suggest_prices": item.suggest_prices, "reason": item.reason,
        "created_at": item.created_at, "updated_at": item.updated_at,
    } for item in db.scalars(query)]


@router.patch("/price-assignments/{assignment_id}", dependencies=[Depends(require_csrf)])
def update_price_assignment(assignment_id: int, payload: PriceAssignmentCreate, db: Session = Depends(get_database_session)):
    """Update a single date-level assignment."""

    item = db.get(PriceAssignment, assignment_id)
    if not item or item.property_id != payload.property_id or payload.start_date != payload.end_date:
        raise HTTPException(404, "Price assignment not found")
    item.stay_date = payload.start_date
    item.price = payload.price
    item.suggest_prices = payload.suggest_prices
    item.reason = payload.reason
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": item.id, "updated": True}


@router.delete("/price-assignments/{assignment_id}", dependencies=[Depends(require_csrf)])
def delete_price_assignment(assignment_id: int, db: Session = Depends(get_database_session)):
    """Remove one date-level assignment and restore normal pricing behavior."""

    item = db.get(PriceAssignment, assignment_id)
    if not item:
        raise HTTPException(404, "Price assignment not found")
    for legacy_override in db.scalars(select(Override).where(Override.property_id == item.property_id, Override.start_date <= item.stay_date, Override.end_date >= item.stay_date)).all():
        db.delete(legacy_override)
    for legacy_anchor in db.scalars(select(PriceAnchor).where(PriceAnchor.property_id == item.property_id, PriceAnchor.stay_date == item.stay_date)).all():
        db.delete(legacy_anchor)
    db.delete(item)
    db.commit()
    return Response(status_code=204)


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
            "suggest_prices": item.suggest_prices,
        }
        for item in db.scalars(query)
    ]


@router.delete("/overrides/{override_id}", dependencies=[Depends(require_csrf)])
def delete_override(override_id: int, db: Session = Depends(get_database_session)):
    """Delete one hard override."""

    item = db.get(Override, override_id)
    if not item:
        raise HTTPException(404, "Override not found")
    assignment = db.scalar(select(PriceAssignment).where(PriceAssignment.property_id == item.property_id, PriceAssignment.stay_date == item.start_date))
    if assignment and not assignment.suggest_prices:
        db.delete(assignment)
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.post("/price-anchors", dependencies=[Depends(require_csrf)])
def create_manual_price_anchor(
    payload: PriceAnchorCreate, db: Session = Depends(get_database_session)
):
    """Create or replace manual base anchors for every date in a range."""

    if not db.get(Property, payload.property_id):
        raise HTTPException(404, "Property not found")
    now = datetime.now(timezone.utc)
    cursor = payload.start_date
    count = 0
    while cursor <= payload.end_date:
        item = db.scalar(
            select(PriceAnchor).where(
                PriceAnchor.property_id == payload.property_id,
                PriceAnchor.stay_date == cursor,
            )
        )
        metadata = {"reason": payload.reason}
        calendar = db.scalar(
            select(HostexCalendarDay).where(
                HostexCalendarDay.property_id == payload.property_id,
                HostexCalendarDay.channel_type == "booking_site",
                HostexCalendarDay.stay_date == cursor,
            )
        )
        if calendar is None or (calendar.inventory is not None and calendar.inventory <= 0):
            cursor += timedelta(days=1)
            continue
        if item:
            item.source_type = "manual_base"
            item.source_price = payload.price
            item.currency = "IDR"
            item.source_metadata = metadata
            item.suggest_prices = payload.suggest_prices
            item.updated_at = now
        else:
            db.add(
                PriceAnchor(
                    property_id=payload.property_id,
                    stay_date=cursor,
                    source_type="manual_base",
                    source_price=payload.price,
                    currency="IDR",
                    source_metadata=metadata,
                    suggest_prices=payload.suggest_prices,
                    created_at=now,
                    updated_at=now,
                )
            )
        assignment = db.scalar(select(PriceAssignment).where(PriceAssignment.property_id == payload.property_id, PriceAssignment.stay_date == cursor))
        if assignment:
            assignment.price = payload.price
            assignment.suggest_prices = True
            assignment.reason = payload.reason
            assignment.updated_at = now
        else:
            db.add(PriceAssignment(property_id=payload.property_id, stay_date=cursor, price=payload.price, suggest_prices=True, reason=payload.reason, created_at=now, updated_at=now))
        count += 1
        cursor += timedelta(days=1)
    db.commit()
    return {"count": count}


@router.get("/price-anchors", dependencies=[Depends(require_session)])
def list_price_anchors(
    property_id: int | None = None, db: Session = Depends(get_database_session)
):
    """List persisted date-level price anchors."""

    query = select(PriceAnchor).order_by(PriceAnchor.stay_date)
    if property_id:
        query = query.where(PriceAnchor.property_id == property_id)
    return [
        {
            "id": item.id,
            "property_id": item.property_id,
            "stay_date": item.stay_date,
            "source_type": item.source_type,
            "source_price": item.source_price,
            "currency": item.currency,
            "source_metadata": item.source_metadata,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "suggest_prices": item.suggest_prices,
        }
        for item in db.scalars(query)
    ]


@router.delete("/price-anchors/{anchor_id}", dependencies=[Depends(require_csrf)])
def delete_price_anchor(anchor_id: int, db: Session = Depends(get_database_session)):
    """Delete one date-level anchor so market fallback can be recalculated."""

    item = db.get(PriceAnchor, anchor_id)
    if not item:
        raise HTTPException(404, "Price anchor not found")
    assignment = db.scalar(select(PriceAssignment).where(PriceAssignment.property_id == item.property_id, PriceAssignment.stay_date == item.stay_date))
    if assignment and assignment.suggest_prices:
        db.delete(assignment)
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


@router.get("/runs/{run_id}", dependencies=[Depends(require_session)])
def get_run(run_id: int, db: Session = Depends(get_database_session)):
    """Return one operational run for Activity polling."""

    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {
        "id": run.id,
        "kind": run.kind.value,
        "status": run.status.value,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "summary": run.summary,
        "error": run.error,
    }


@router.get("/competitors", dependencies=[Depends(require_session)])
def list_competitors(db: Session = Depends(get_database_session)):
    """List normalized competitors with freshness and collection status."""

    rows = db.execute(
        select(CompetitorListing, PricingGroup.name)
        .join(PricingGroup)
        .order_by(PricingGroup.name, CompetitorListing.external_listing_id)
    ).all()
    result = []
    for item, group_name in rows:
        latest = db.scalar(
            select(CompetitorObservation)
            .where(CompetitorObservation.competitor_listing_id == item.id)
            .order_by(CompetitorObservation.scraped_at.desc())
            .limit(1)
        )
        result.append({
            "id": item.id,
            "pricing_group_id": item.pricing_group_id,
            "pricing_group_name": group_name,
            "canonical_url": item.canonical_url,
            "external_listing_id": item.external_listing_id,
            "current_minimum_stay": item.current_minimum_stay,
            "last_scraped_at": item.last_scraped_at,
            "last_error": item.last_error,
            "last_collection_mode": latest.collection_mode if latest else None,
            "last_price_method": latest.price_method if latest else None,
        })
    return result


@router.post("/competitor-scrapes", dependencies=[Depends(require_csrf)])
def create_competitor_scrape(
    payload: CompetitorScrapeCreate,
    db: Session = Depends(get_database_session),
):
    """Create one scrape run for every competitor in a pricing group."""

    settings = get_settings()
    try:
        validate_scrape_range(
            payload.start_date,
            payload.end_date,
            settings.competitor_scrape_max_days,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        if payload.pricing_group_id is not None:
            group = db.get(PricingGroup, payload.pricing_group_id)
            if not group:
                raise HTTPException(404, "Pricing group not found")
            listings = db.scalars(
                select(CompetitorListing)
                .where(CompetitorListing.pricing_group_id == group.id)
                .order_by(CompetitorListing.id)
            ).all()
            if not listings:
                raise HTTPException(422, "Pricing group has no competitor listings")
            run = start_group_collection_run(
                db,
                group.id,
                listings,
                payload.start_date,
                payload.end_date,
                force_refresh=payload.force_refresh,
                collection_mode=payload.collection_mode,
            )
        else:
            # Keep the old request shape for API clients during the transition.
            listing = db.get(CompetitorListing, payload.competitor_listing_id)
            if not listing:
                raise HTTPException(404, "Competitor listing not found")
            run = start_collection_run(
                db,
                listing,
                payload.start_date,
                payload.end_date,
                force_refresh=payload.force_refresh,
                collection_mode=payload.collection_mode,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Collector invocation failed; see run history") from exc
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
    batches = db.scalars(
        select(CompetitorScrapeBatch).where(
            CompetitorScrapeBatch.scrape_run_id == run.id
        )
    ).all()
    return {
        "run_id": run.id,
        "status": run.status.value,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "summary": run.summary,
        "error": run.error,
        "batches": [
            {
                "id": item.id,
                "operation": item.operation,
                "status": item.status,
                "attempt": item.attempt,
                "expected_quote_count": len(item.expected_quote_ids or []),
                "error": item.error,
            }
            for item in batches
        ],
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


def _competitor_run_listing(
    db: Session, run_id: int, external_listing_id: str
) -> tuple[Run, CompetitorListing]:
    """Load and authenticate callback ownership against persisted run metadata."""

    run = db.get(Run, run_id)
    if not run or run.kind != RunKind.scrape:
        raise HTTPException(404, "Competitor scrape run not found")
    summary = run.summary or {}
    listing_ids = summary.get("competitor_listing_ids")
    if listing_ids is None:
        listing_ids = [summary.get("competitor_listing_id")]
    listing = db.scalar(
        select(CompetitorListing).where(
            CompetitorListing.id.in_([item for item in listing_ids if item is not None]),
            CompetitorListing.external_listing_id == external_listing_id,
        )
    )
    if not listing:
        raise HTTPException(409, "Callback listing does not match its run")
    return run, listing


@router.post(
    "/internal/competitor-calendar",
    dependencies=[Depends(require_competitor_callback)],
)
def receive_competitor_calendar(
    payload: CompetitorCalendarCallback,
    db: Session = Depends(get_database_session),
):
    """Persist a complete calendar and launch backend-planned quote batches."""

    run, listing = _competitor_run_listing(
        db, payload.run_id, payload.external_listing_id
    )
    batch = db.scalar(
        select(CompetitorScrapeBatch).where(
            CompetitorScrapeBatch.scrape_run_id == run.id,
            CompetitorScrapeBatch.operation == "calendar",
            CompetitorScrapeBatch.competitor_listing_id == listing.id,
        )
    )
    if not batch:
        raise HTTPException(409, "Calendar batch is missing")
    if batch.status in {"succeeded", "failed"}:
        return {"run_id": run.id, "status": run.status.value, "idempotent": True}
    now = datetime.now(timezone.utc)
    if payload.status != "succeeded":
        batch.status = "failed"
        batch.error = payload.error or payload.status
        batch.finished_at = now
        run.status = RunStatus.failed
        run.error = batch.error
        run.finished_at = now
        run.summary = {**(run.summary or {}), "phase": "completed"}
        listing.last_error = batch.error
        db.commit()
        return {"run_id": run.id, "status": run.status.value}

    ordered = sorted(payload.calendar_days, key=lambda item: item.stay_date)
    if any(
        right.stay_date != left.stay_date + timedelta(days=1)
        for left, right in zip(ordered, ordered[1:])
    ):
        raise HTTPException(422, "Calendar callback must contain a continuous range")
    requested_values = (run.summary or {}).get("requested_dates_by_listing", {}).get(
        str(listing.id), (run.summary or {}).get("requested_dates", [])
    )
    requested = {date.fromisoformat(item) for item in requested_values}
    returned = {item.stay_date for item in ordered}
    if not requested.issubset(returned):
        raise HTTPException(422, "Calendar does not cover every requested date")

    calendar = {
        item.stay_date: (item.bookable, item.min_nights) for item in ordered
    }
    observations = [
        CompetitorObservation(
            competitor_listing_id=listing.id,
            scrape_run_id=run.id,
            stay_date=item.stay_date,
            price=None,
            bookable=item.bookable,
            minimum_stay=item.min_nights,
            currency="IDR",
            scraped_at=payload.scraped_at,
            parser_version=payload.parser_version,
            price_method="pending" if item.bookable else "unavailable",
            collection_mode=collection_mode_for_date(item.stay_date),
        )
        for item in ordered
    ]
    db.add_all(observations)
    batch.status = "succeeded"
    batch.finished_at = now
    batches = create_quote_plan(db, run, listing, calendar)
    business_today = datetime.now(get_settings().timezone).date()
    future_days = [
        item for item in ordered if item.stay_date >= business_today
    ]
    if future_days:
        listing.current_minimum_stay = next(
            (
                item.min_nights
                for item in future_days
                if item.bookable and item.min_nights is not None
            ),
            None,
        )
    run.summary = {
        **(run.summary or {}),
        "phase": "quotes" if batches else "calculating",
        "calendar_day_count": len(ordered),
        "price_target_count": len(requested),
        "quote_batch_count": len(batches),
    }
    db.commit()
    if not batches:
        finalize_run(db, run, listing)
    else:
        try:
            invoke_quote_batches(batches, run, listing)
            for item in batches:
                item.status = "running"
            db.commit()
        except Exception as exc:
            for item in batches:
                if item.status == "queued":
                    item.status = "failed"
                    item.error = str(exc)
                    item.finished_at = now
            db.commit()
            finalize_run(db, run, listing)
    return {"run_id": run.id, "status": run.status.value}


@router.post(
    "/internal/competitor-quotes",
    dependencies=[Depends(require_competitor_callback)],
)
def receive_competitor_quotes(
    payload: CompetitorQuoteBatchCallback,
    db: Session = Depends(get_database_session),
):
    """Atomically persist one quote batch and finalize when all batches finish."""

    run, listing = _competitor_run_listing(
        db, payload.run_id, payload.external_listing_id
    )
    batch = db.get(CompetitorScrapeBatch, payload.batch_id)
    if not batch or batch.scrape_run_id != run.id or batch.operation != "quotes":
        raise HTTPException(409, "Quote batch does not match its run")
    if batch.status in {"succeeded", "partially_succeeded", "failed"}:
        return {"run_id": run.id, "status": run.status.value, "idempotent": True}
    expected = set(batch.expected_quote_ids or [])
    received = {item.quote_id for item in payload.quotes}
    errors = {item.quote_id for item in payload.quote_errors}
    if received | errors != expected:
        raise HTTPException(422, "Callback must classify every expected quote ID")
    for item in payload.quotes:
        if item.currency.upper() != "IDR" or item.adults != get_settings().competitor_quote_adults:
            raise HTTPException(422, "Quote currency or guest count is invalid")
        if item.quote_id != quote_identity(
            run.id, listing.id, item.check_in_date, item.check_out_date
        ):
            raise HTTPException(422, "Quote identity does not match its interval")
    db.add_all(
        [
            CompetitorStayQuote(
                scrape_run_id=run.id,
                competitor_listing_id=listing.id,
                quote_id=item.quote_id,
                check_in_date=item.check_in_date,
                check_out_date=item.check_out_date,
                adults=item.adults,
                currency=item.currency.upper(),
                total_price=item.total_price,
                scraped_at=item.scraped_at,
                parser_version=item.parser_version,
                raw=item.raw,
            )
            for item in payload.quotes
        ]
    )
    targets = db.scalars(
        select(CompetitorPriceTarget).where(
            CompetitorPriceTarget.scrape_run_id == run.id
        )
    ).all()
    for quote_error in payload.quote_errors:
        for target in targets:
            if quote_error.quote_id not in (target.quote_ids or []):
                continue
            existing = db.scalar(
                select(CompetitorDateError).where(
                    CompetitorDateError.scrape_run_id == run.id,
                    CompetitorDateError.competitor_listing_id == listing.id,
                    CompetitorDateError.stay_date == target.stay_date,
                )
            )
            if existing is None:
                db.add(
                    CompetitorDateError(
                        scrape_run_id=run.id,
                        competitor_listing_id=listing.id,
                        stay_date=target.stay_date,
                        code=quote_error.code,
                        message=quote_error.message,
                    )
                )
    batch.status = payload.status
    batch.error = payload.error or (
        f"{len(payload.quote_errors)} quote(s) failed"
        if payload.quote_errors
        else None
    )
    batch.finished_at = datetime.now(timezone.utc)
    db.commit()
    finalize_run(db, run, listing)
    return {"run_id": run.id, "status": run.status.value}


@router.post(
    "/internal/competitor-observations",
    dependencies=[Depends(require_competitor_callback)],
)
def receive_competitor_callback(
    payload: CompetitorCalendarCallback | CompetitorQuoteBatchCallback,
    db: Session = Depends(get_database_session),
):
    """Dispatch the existing unified callback URL by operation."""

    if isinstance(payload, CompetitorCalendarCallback):
        return receive_competitor_calendar(payload, db)
    return receive_competitor_quotes(payload, db)


@router.get("/integrations/hostex", dependencies=[Depends(require_session)])
def hostex_status(db: Session = Depends(get_database_session)):
    """Return Hostex import timestamps, last attempt, and daily schedule."""

    settings = get_settings()
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(settings.timezone)
    next_import = local_now.replace(hour=4, minute=0, second=0, microsecond=0)
    if next_import <= local_now:
        next_import += timedelta(days=1)
    last_run = db.scalar(
        select(Run)
        .where(Run.kind == RunKind.import_)
        .order_by(Run.started_at.desc())
        .limit(1)
    )
    last_success = db.scalar(
        select(Run)
        .where(
            Run.kind == RunKind.import_,
            Run.status == RunStatus.succeeded,
        )
        .order_by(Run.finished_at.desc())
        .limit(1)
    )
    successful_at = last_success.finished_at if last_success else None
    if successful_at is not None and successful_at.tzinfo is None:
        successful_at = successful_at.replace(tzinfo=timezone.utc)
    return {
        "configured": bool(settings.hostex_access_token),
        "mode": "read_only",
        "last_successful_import_at": successful_at,
        "schedule": {
            "enabled": True,
            "description": "Daily at 04:00 WITA",
            "timezone": settings.business_timezone,
            "next_import_at": next_import,
        },
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
    client = HostexClient(settings.hostex_access_token, settings.hostex_base_url)
    try:
        with serialized_run(db, RunKind.import_) as run:
            if run is None:
                raise HTTPException(409, "Another serialized job is running")
            summary = await import_hostex(db, client)
            run.summary = summary
            run_id = run.id
        return {"run_id": run_id, "status": "succeeded", "summary": summary}
    except HostexError as exc:
        raise HTTPException(502, "Hostex import failed; see run history") from exc
    finally:
        await client.close()


@router.post("/imports/hostex/booking-site", dependencies=[Depends(require_csrf)])
async def run_booking_site_import(
    start: date = Query(default_factory=date.today),
    end: date | None = None,
    db: Session = Depends(get_database_session),
):
    """Refresh only BookingSite calendars for the dashboard action."""

    settings = get_settings()
    if not settings.hostex_access_token:
        raise HTTPException(409, "HOSTEX_ACCESS_TOKEN is not configured")
    end = end or (start + timedelta(days=365))
    if end < start or (end - start).days > 365:
        raise HTTPException(422, "Date range must be between 0 and 365 days")
    client = HostexClient(settings.hostex_access_token, settings.hostex_base_url)
    try:
        with serialized_run(db, RunKind.import_) as run:
            if run is None:
                raise HTTPException(409, "Another serialized job is running")
            try:
                summary = await import_booking_site_calendars(
                    db, client, start_date=start, end_date=end
                )
                run.summary = summary
                run.status = RunStatus.succeeded
                run.finished_at = datetime.now(timezone.utc)
            except Exception as exc:
                run.status = RunStatus.failed
                run.error = str(exc)[:1000]
                run.finished_at = datetime.now(timezone.utc)
                db.commit()
                raise
            return {"run_id": run.id, "status": "succeeded", "summary": summary}
    except HostexError as exc:
        raise HTTPException(502, "BookingSite import failed; see run history") from exc
    finally:
        await client.close()


@router.get("/settings/pricing", dependencies=[Depends(require_session)])
def get_pricing_configuration(db: Session = Depends(get_database_session)):
    """Return the effective Pricing Engine v3 configuration."""

    return pricing_configuration(db)


@router.get("/settings/pricing/effective/{property_id}", dependencies=[Depends(require_session)])
def get_effective_pricing_configuration(property_id: int, db: Session = Depends(get_database_session)):
    """Return property settings with the source of every inherited value."""

    property_item = db.get(Property, property_id)
    if not property_item:
        raise HTTPException(404, "Property not found")
    return pricing_configuration_with_sources(db, property_item)


@router.put("/settings/pricing", dependencies=[Depends(require_csrf)])
def set_pricing_configuration(
    payload: PricingConfiguration, db: Session = Depends(get_database_session)
):
    """Persist validated Pricing Engine v3 settings."""

    value = payload.model_dump(mode="json")
    item = db.get(Setting, "pricing_engine_v2")
    if item:
        item.value = value
    else:
        db.add(Setting(key="pricing_engine_v2", value=value))
    db.commit()
    return value
