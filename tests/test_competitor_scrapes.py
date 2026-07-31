from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.competitor_scrapes import (
    ensure_no_overlapping_run,
    pending_dates,
    validate_scrape_range,
)
from app.config import get_settings
from app.database import Base, get_database_session
from app.main import app
from app.models import (
    CompetitorListing,
    CompetitorDateError,
    CompetitorObservation,
    CompetitorStayQuote,
    PricingGroup,
    Run,
    RunKind,
    RunStatus,
)


def database():
    """Create one shared in-memory database for an API test."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


def competitor(session):
    """Create one normalized competitor fixture."""

    group = PricingGroup(
        name="Canggu villas", pricing_settings={}, competitor_urls=[]
    )
    session.add(group)
    session.flush()
    listing = CompetitorListing(
        pricing_group_id=group.id,
        canonical_url="https://www.airbnb.com/rooms/123",
        external_listing_id="123",
    )
    session.add(listing)
    session.commit()
    return listing


def test_pending_dates_skip_fresh_observations_unless_forced():
    Session = database()
    with Session() as session:
        listing = competitor(session)
        today = date.today()
        session.add(
            CompetitorObservation(
                competitor_listing_id=listing.id,
                stay_date=today,
                price=Decimal("1000000"),
                available=True,
                available_for_checkin=True,
                minimum_stay=2,
                currency="IDR",
                scraped_at=datetime.now(timezone.utc),
                parser_version="test",
                price_method="test",
            )
        )
        session.commit()
        pending, skipped = pending_dates(
            session, listing.id, today, today + timedelta(days=1), False
        )
        assert pending == [today + timedelta(days=1)]
        assert skipped == [today]
        forced, skipped = pending_dates(
            session, listing.id, today, today + timedelta(days=1), True
        )
        assert forced == [today, today + timedelta(days=1)]
        assert skipped == []


def test_scrape_range_limit_is_configurable():
    assert validate_scrape_range(
        date(2026, 8, 1), date(2026, 8, 30), 30
    ) == 30
    try:
        validate_scrape_range(date(2026, 8, 1), date(2026, 8, 31), 30)
    except ValueError as exc:
        assert "30 days" in str(exc)
    else:
        raise AssertionError("oversized range was accepted")


def test_overlapping_active_run_is_rejected():
    Session = database()
    with Session() as session:
        listing = competitor(session)
        session.add(
            Run(
                kind=RunKind.scrape,
                status=RunStatus.running,
                summary={
                    "competitor_listing_id": listing.id,
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-07",
                },
            )
        )
        session.commit()
        try:
            ensure_no_overlapping_run(
                session, listing.id, date(2026, 8, 7), date(2026, 8, 10)
            )
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 409
        else:
            raise AssertionError("overlapping run was accepted")


def test_callback_is_authenticated_atomic_and_idempotent():
    Session = database()
    with Session() as session:
        listing = competitor(session)
        run = Run(
            kind=RunKind.scrape,
            status=RunStatus.running,
            summary={
                "phase": "collecting",
                "competitor_listing_id": listing.id,
                "external_listing_id": listing.external_listing_id,
                "start_date": "2026-08-01",
                "end_date": "2026-08-01",
                "requested_dates": ["2026-08-01"],
            },
        )
        session.add(run)
        session.commit()
        run_id = run.id

    def override_session():
        with Session() as session:
            yield session

    app.dependency_overrides[get_database_session] = override_session
    settings = get_settings()
    old_token = settings.competitor_callback_token
    settings.competitor_callback_token = "callback-secret"
    client = TestClient(app)
    payload = {
        "run_id": run_id,
        "external_listing_id": "123",
        "start_date": "2026-08-01",
        "end_date": "2026-08-01",
        "status": "succeeded",
        "observations": [{
            "stay_date": "2026-08-01",
            "currency": "IDR",
            "available": True,
            "available_for_checkin": True,
            "min_nights": 3,
            "stay_quotes": [{
                "check_out_date": "2026-08-04",
                "stay_nights": 3,
                "total_price": "3600000",
                "cleaning_fee": "300000",
                "taxes": "0",
                "other_excluded_fees": "0",
            }],
            "scraped_at": "2026-07-30T12:00:00Z",
            "parser_version": "fixture-v1",
        }],
    }
    try:
        assert client.post(
            "/api/internal/competitor-observations", json=payload
        ).status_code == 401
        invalid = {
            **payload,
            "observations": [{
                **payload["observations"][0],
                "stay_quotes": [],
            }],
        }
        assert client.post(
            "/api/internal/competitor-observations",
            json=invalid,
            headers={"Authorization": "Bearer callback-secret"},
        ).status_code == 422
        with Session() as session:
            assert session.query(CompetitorObservation).count() == 0
        first = client.post(
            "/api/internal/competitor-observations",
            json=payload,
            headers={"Authorization": "Bearer callback-secret"},
        )
        assert first.status_code == 200
        second = client.post(
            "/api/internal/competitor-observations",
            json=payload,
            headers={"Authorization": "Bearer callback-secret"},
        )
        assert second.json()["idempotent"] is True
        with Session() as session:
            assert session.query(CompetitorObservation).count() == 1
            observation = session.query(CompetitorObservation).one()
            assert observation.price == Decimal("1100000")
            assert observation.price_method == "minimum_stay_average"
            assert session.query(CompetitorStayQuote).count() == 1
            stored_listing = session.get(CompetitorListing, listing.id)
            assert stored_listing.current_minimum_stay == 3
            assert session.get(Run, run_id).status == RunStatus.succeeded
    finally:
        settings.competitor_callback_token = old_token
        app.dependency_overrides.clear()


def test_partial_callback_keeps_success_and_retries_failed_date():
    Session = database()
    with Session() as session:
        listing = competitor(session)
        run = Run(
            kind=RunKind.scrape,
            status=RunStatus.running,
            summary={
                "phase": "collecting",
                "competitor_listing_id": listing.id,
                "external_listing_id": "123",
                "start_date": "2026-08-01",
                "end_date": "2026-08-02",
                "requested_dates": ["2026-08-01", "2026-08-02"],
            },
        )
        session.add(run)
        session.commit()
        run_id, listing_id = run.id, listing.id

    def override_session():
        with Session() as session:
            yield session

    app.dependency_overrides[get_database_session] = override_session
    settings = get_settings()
    old_token = settings.competitor_callback_token
    settings.competitor_callback_token = "callback-secret"
    payload = {
        "run_id": run_id,
        "external_listing_id": "123",
        "start_date": "2026-08-01",
        "end_date": "2026-08-02",
        "status": "partially_succeeded",
        "observations": [{
            "stay_date": "2026-08-01",
            "currency": "IDR",
            "available": True,
            "available_for_checkin": True,
            "min_nights": 2,
            "stay_quotes": [{
                "check_out_date": "2026-08-03",
                "stay_nights": 2,
                "total_price": "2000000",
            }],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "parser_version": "fixture-v1",
        }],
        "date_errors": [{
            "stay_date": "2026-08-02",
            "code": "quote_unavailable",
            "message": "No quote returned",
        }],
    }
    try:
        response = TestClient(app).post(
            "/api/internal/competitor-observations",
            json=payload,
            headers={"Authorization": "Bearer callback-secret"},
        )
        assert response.status_code == 200
        with Session() as session:
            assert session.get(Run, run_id).status == RunStatus.partially_succeeded
            assert session.query(CompetitorObservation).count() == 1
            assert session.query(CompetitorDateError).count() == 1
            pending, skipped = pending_dates(
                session,
                listing_id,
                date(2026, 8, 1),
                date(2026, 8, 2),
                False,
            )
            assert pending == [date(2026, 8, 2)]
            assert skipped == [date(2026, 8, 1)]
    finally:
        settings.competitor_callback_token = old_token
        app.dependency_overrides.clear()
