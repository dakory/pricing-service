from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import api
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
    CompetitorObservation,
    CompetitorPriceTarget,
    CompetitorScrapeBatch,
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


def test_pending_dates_use_mode_specific_freshness():
    Session = database()
    with Session() as session:
        listing = competitor(session)
        today = date(2026, 8, 1)
        now = datetime(2026, 8, 1, tzinfo=timezone.utc)
        session.add_all(
            [
                CompetitorObservation(
                    competitor_listing_id=listing.id,
                    stay_date=today,
                    price=Decimal("1000000"),
                    bookable=True,
                    minimum_stay=2,
                    currency="IDR",
                    scraped_at=now - timedelta(hours=23),
                    parser_version="test",
                    price_method="minimum_stay_average",
                    collection_mode="precise",
                ),
                CompetitorObservation(
                    competitor_listing_id=listing.id,
                    stay_date=today + timedelta(days=100),
                    price=Decimal("1200000"),
                    bookable=True,
                    minimum_stay=2,
                    currency="IDR",
                    scraped_at=now - timedelta(days=20),
                    parser_version="test",
                    price_method="minimum_stay_average",
                    collection_mode="rough",
                ),
            ]
        )
        session.commit()
        assert pending_dates(
            session, listing.id, today, today, False, "precise", now
        ) == ([], [today])
        far = today + timedelta(days=100)
        assert pending_dates(
            session, listing.id, far, far, False, "rough", now
        ) == ([], [far])
        assert pending_dates(
            session, listing.id, today, today, True, "precise", now
        ) == ([today], [])


def test_scrape_range_limit_is_configurable():
    assert validate_scrape_range(
        date(2026, 8, 1), date(2026, 8, 30), 30
    ) == 30


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


def test_two_stage_callbacks_persist_calendar_quotes_and_price(monkeypatch):
    Session = database()
    with Session() as session:
        listing = competitor(session)
        run = Run(
            kind=RunKind.scrape,
            status=RunStatus.running,
            summary={
                "phase": "calendar",
                "competitor_listing_id": listing.id,
                "external_listing_id": "123",
                "start_date": "2026-08-03",
                "end_date": "2026-08-03",
                "requested_dates": ["2026-08-03"],
                "skipped_dates": [],
                "collection_mode": "precise",
            },
        )
        session.add(run)
        session.flush()
        session.add(
            CompetitorScrapeBatch(
                scrape_run_id=run.id,
                competitor_listing_id=listing.id,
                operation="calendar",
                status="running",
                expected_quote_ids=[],
            )
        )
        session.commit()
        run_id = run.id

    def override_session():
        with Session() as session:
            yield session

    app.dependency_overrides[get_database_session] = override_session
    settings = get_settings()
    old_token = settings.competitor_callback_token
    settings.competitor_callback_token = "callback-secret"
    monkeypatch.setattr(api, "invoke_quote_batches", lambda *args: None)
    client = TestClient(app)
    headers = {"Authorization": "Bearer callback-secret"}
    days = [
        {
            "stay_date": f"2026-08-0{day}",
            "bookable": True,
            "min_nights": 2,
        }
        for day in range(1, 6)
    ]
    calendar_payload = {
        "operation": "calendar",
        "run_id": run_id,
        "external_listing_id": "123",
        "status": "succeeded",
        "calendar_days": days,
        "scraped_at": "2026-08-01T00:00:00Z",
        "parser_version": "calendar-v1",
        "error": None,
    }
    try:
        assert client.post(
            "/api/internal/competitor-observations", json=calendar_payload
        ).status_code == 401
        response = client.post(
            "/api/internal/competitor-observations",
            json=calendar_payload,
            headers=headers,
        )
        assert response.status_code == 200, response.text
        with Session() as session:
            target = session.query(CompetitorPriceTarget).one()
            batch = session.query(CompetitorScrapeBatch).filter_by(
                operation="quotes"
            ).one()
            assert target.price_method == "quote_difference_left"
            assert len(target.quote_ids) == 2
            assert batch.status == "running"
            expected = list(batch.expected_quote_ids)
            quote_dates = {}
            for quote_id in expected:
                if quote_id == target.quote_ids[0]:
                    quote_dates[quote_id] = ("2026-08-01", "2026-08-04", "3000000")
                else:
                    quote_dates[quote_id] = ("2026-08-01", "2026-08-03", "2000000")
            batch_id = batch.id
        quote_payload = {
            "operation": "quotes",
            "run_id": run_id,
            "batch_id": batch_id,
            "external_listing_id": "123",
            "status": "succeeded",
            "quotes": [
                {
                    "quote_id": quote_id,
                    "check_in_date": values[0],
                    "check_out_date": values[1],
                    "adults": 4,
                    "total_price": values[2],
                    "currency": "IDR",
                    "scraped_at": "2026-08-01T00:01:00Z",
                    "parser_version": "checkout-v1",
                }
                for quote_id, values in quote_dates.items()
            ],
            "quote_errors": [],
            "error": None,
        }
        first = client.post(
            "/api/internal/competitor-observations",
            json=quote_payload,
            headers=headers,
        )
        assert first.status_code == 200, first.text
        second = client.post(
            "/api/internal/competitor-observations",
            json=quote_payload,
            headers=headers,
        )
        assert second.json()["idempotent"] is True
        with Session() as session:
            observation = session.scalar(
                session.query(CompetitorObservation).filter_by(
                    scrape_run_id=run_id, stay_date=date(2026, 8, 3)
                ).statement
            )
            assert observation.price == Decimal("1000000")
            assert observation.price_method == "quote_difference_left"
            assert session.query(CompetitorStayQuote).count() == 2
            assert session.get(Run, run_id).status == RunStatus.succeeded
    finally:
        settings.competitor_callback_token = old_token
        app.dependency_overrides.clear()


def test_calendar_callback_rejects_gaps_without_partial_writes():
    Session = database()
    with Session() as session:
        listing = competitor(session)
        run = Run(
            kind=RunKind.scrape,
            status=RunStatus.running,
            summary={
                "competitor_listing_id": listing.id,
                "start_date": "2026-08-01",
                "end_date": "2026-08-03",
                "requested_dates": ["2026-08-01", "2026-08-03"],
            },
        )
        session.add(run)
        session.flush()
        session.add(
            CompetitorScrapeBatch(
                scrape_run_id=run.id,
                competitor_listing_id=listing.id,
                operation="calendar",
                status="running",
                expected_quote_ids=[],
            )
        )
        session.commit()
        run_id = run.id

    def override_session():
        with Session() as session:
            yield session

    app.dependency_overrides[get_database_session] = override_session
    settings = get_settings()
    old_token = settings.competitor_callback_token
    settings.competitor_callback_token = "callback-secret"
    try:
        response = TestClient(app).post(
            "/api/internal/competitor-calendar",
            headers={"Authorization": "Bearer callback-secret"},
            json={
                "operation": "calendar",
                "run_id": run_id,
                "external_listing_id": "123",
                "status": "succeeded",
                "calendar_days": [
                    {"stay_date": "2026-08-01", "bookable": False},
                    {"stay_date": "2026-08-03", "bookable": False},
                ],
                "scraped_at": "2026-08-01T00:00:00Z",
                "parser_version": "calendar-v1",
            },
        )
        assert response.status_code == 422
        with Session() as session:
            assert session.query(CompetitorObservation).count() == 0
    finally:
        settings.competitor_callback_token = old_token
        app.dependency_overrides.clear()
