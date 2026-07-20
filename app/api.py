from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.auth import clear_session, create_session, digest, require_csrf, require_session, verify_admin
from app.database import get_db
from app.models import AdminSession, Override, Property, Recommendation, Run, Setting
from app.schemas import ModeUpdate, OverrideCreate, PropertyCreate, PropertyRead, PropertyUpdate

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if not verify_admin(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    create_session(response, db)
    return {"authenticated": True, "email": payload.email}


@router.post("/auth/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response, db: Session = Depends(get_db), session: AdminSession = Depends(require_session)):
    db.delete(session)
    db.commit()
    clear_session(response)
    return {"authenticated": False}


@router.get("/auth/session")
def session_status(session: AdminSession = Depends(require_session)):
    return {"authenticated": True, "expires_at": session.expires_at}


@router.get("/properties", response_model=list[PropertyRead], dependencies=[Depends(require_session)])
def properties(db: Session = Depends(get_db)):
    return db.scalars(select(Property).order_by(Property.name)).all()


@router.post("/properties", response_model=PropertyRead, dependencies=[Depends(require_csrf)])
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    item = Property(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/properties/{property_id}", response_model=PropertyRead, dependencies=[Depends(require_csrf)])
def update_property(property_id: int, payload: PropertyUpdate, db: Session = Depends(get_db)):
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
def calendar(
    property_id: int | None = None,
    start: date = Query(default_factory=date.today),
    end: date = Query(default_factory=lambda: date.today() + timedelta(days=365)),
    db: Session = Depends(get_db),
):
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
        }
        for item, name in rows
    ]


@router.post("/overrides", dependencies=[Depends(require_csrf)])
def create_override(payload: OverrideCreate, db: Session = Depends(get_db)):
    if not db.get(Property, payload.property_id):
        raise HTTPException(404, "Property not found")
    item = Override(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.delete("/overrides/{override_id}", dependencies=[Depends(require_csrf)])
def delete_override(override_id: int, db: Session = Depends(get_db)):
    item = db.get(Override, override_id)
    if not item:
        raise HTTPException(404, "Override not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.get("/runs", dependencies=[Depends(require_session)])
def runs(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
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


@router.get("/settings/mode", dependencies=[Depends(require_session)])
def get_mode(db: Session = Depends(get_db)):
    item = db.get(Setting, "mode")
    return item.value if item else {"mode": "shadow", "activation_date": None}


@router.put("/settings/mode", dependencies=[Depends(require_csrf)])
def set_mode(payload: ModeUpdate, db: Session = Depends(get_db)):
    value = {"mode": payload.mode, "activation_date": payload.activation_date.isoformat() if payload.activation_date else None}
    item = db.get(Setting, "mode")
    if item:
        item.value = value
    else:
        db.add(Setting(key="mode", value=value))
    db.commit()
    return value
