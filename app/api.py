from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import clear_session, create_session, require_csrf, require_session, verify_admin
from app.config import get_settings
from app.database import get_database_session
from app.hostex import HostexClient, HostexError
from app.hostex_import import import_hostex
from app.jobs import configure_shadow_defaults, generate_price_recommendations, serialized_run
from app.models import AdminSession, HostexCalendarDay, HostexListing, Override, Property, Recommendation, Run, Setting
from app.models import RunKind, RunStatus
from app.schemas import ModeUpdate, OverrideCreate, PropertyCreate, PropertyRead, PropertyUpdate

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


@router.post("/properties", response_model=PropertyRead, dependencies=[Depends(require_csrf)])
def create_property(payload: PropertyCreate, db: Session = Depends(get_database_session)):
    """Create a managed property pricing policy."""

    item = Property(**payload.model_dump())
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
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    if not item.min_price <= item.base_price <= item.max_price:
        raise HTTPException(422, "price bounds must satisfy min <= base <= max")
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
            "minimum_stay": item.minimum_stay,
            "published_minimum_stay": item.published_minimum_stay,
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


@router.post("/pricing/bootstrap", dependencies=[Depends(require_csrf)])
def bootstrap_pricing(db: Session = Depends(get_database_session)):
    """Infer conservative shadow policies from imported BookingSite prices."""

    return {"mode": "shadow", "properties": configure_shadow_defaults(db)}


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
    """Create a hard price or minimum-stay date-range override."""

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
            "minimum_stay": item.minimum_stay,
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
