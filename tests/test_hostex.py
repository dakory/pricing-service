from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.api import hostex_status
from app.config import get_settings
from app.hostex import HostexClient, HostexError
from app.hostex_import import import_hostex
from app.models import (
    HostexCalendarDay,
    HostexListing,
    Property,
    Reservation,
    Run,
    RunKind,
    RunStatus,
)

FIXTURES = Path(__file__).parent / "fixtures" / "hostex"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_read_only_import_persists_mappings_reservations_and_calendar():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Hostex-Access-Token"] == "secret-token"
        assert request.headers["User-Agent"].startswith("NicerHomesPricing/")
        responses = {
            "/v3/properties": fixture("properties.json"),
            "/v3/listings": fixture("listings.json"),
            "/v3/reservations": fixture("reservations.json"),
            "/v3/listings/calendar": fixture("calendar.json"),
        }
        return httpx.Response(200, json=responses[request.url.path])

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.hostex.test")
        client = HostexClient("secret-token", client=http)
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with sessionmaker(engine, expire_on_commit=False)() as db:
            summary = await import_hostex(db, client, today=date(2026, 7, 20))
            prop = db.scalar(select(Property).where(Property.hostex_property_id == 101))
            assert prop.name == "Bingin Garden Villa"
            assert prop.active is False
            assert prop.booking_site_listing_id == "booking-site-101"
            assert db.scalar(select(func.count()).select_from(HostexListing)) == 2
            assert db.scalar(select(func.count()).select_from(HostexListing).where(HostexListing.property_id == prop.id)) == 2
            assert db.scalar(select(func.count()).select_from(Reservation)) == 1
            assert db.scalar(select(func.count()).select_from(HostexCalendarDay)) == 2
            assert summary["calendar"]["created"] == 2
            second = await import_hostex(db, client, today=date(2026, 7, 20))
            assert second["properties"]["created"] == 0
            assert second["listings"]["created"] == 0
            assert second["reservations"]["created"] == 0
            assert second["calendar"]["created"] == 0
            assert db.scalar(select(func.count()).select_from(HostexCalendarDay)) == 2
        await http.aclose()

    asyncio.run(run())


def test_pagination_stops_on_short_page():
    offsets = []

    def handler(request: httpx.Request) -> httpx.Response:
        offsets.append(int(request.url.params["offset"]))
        count = 100 if offsets[-1] == 0 else 1
        return httpx.Response(200, json={"properties": [{"id": i} for i in range(count)]})

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.hostex.test")
        client = HostexClient("token", client=http)
        assert len(await client.properties()) == 101
        await http.aclose()

    asyncio.run(run())
    assert offsets == [0, 100]


def test_reservations_are_split_into_hostex_180_day_windows():
    ranges = []

    def handler(request: httpx.Request) -> httpx.Response:
        start = date.fromisoformat(request.url.params["start_check_in_date"])
        end = date.fromisoformat(request.url.params["end_check_in_date"])
        assert (end - start).days <= 179
        ranges.append((start, end))
        return httpx.Response(200, json={"reservations": []})

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.hostex.test")
        client = HostexClient("token", client=http)
        await client.reservations(date(2025, 1, 1), date(2026, 1, 1))
        await http.aclose()

    asyncio.run(run())
    assert len(ranges) == 3
    assert ranges[1][0] == ranges[0][1] + timedelta(days=1)


def test_http_200_body_error_is_not_treated_as_success():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error_code": 420, "error_msg": "Subscription expired"})

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.hostex.test")
        client = HostexClient("token", client=http)
        with pytest.raises(HostexError, match="420"):
            await client.properties()
        await http.aclose()

    asyncio.run(run())


def test_body_rate_limit_retries_then_succeeds(monkeypatch):
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                200, headers={"Retry-After": "1"}, json={"error_code": 429, "error_msg": "Too Many Attempts"}
            )
        return httpx.Response(200, json={"properties": []})

    async def no_sleep(_: float):
        return None

    monkeypatch.setattr("app.hostex.asyncio.sleep", no_sleep)

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.hostex.test")
        client = HostexClient("token", client=http)
        assert await client.properties() == []
        await http.aclose()

    asyncio.run(run())
    assert attempts == 2


def test_pricing_ratios_support_live_data_channels_envelope():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "error_code": 0,
                "data": {
                    "link_type": "property",
                    "link_id": 101,
                    "channels": [
                        {"channel_type": "booking_site", "listing_id": "direct-101", "ratio": 100}
                    ],
                },
            },
        )

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.hostex.test")
        client = HostexClient("token", client=http)
        ratios = await client.pricing_ratios(101)
        assert ratios[0]["channel_type"] == "booking_site"
        assert ratios[0]["ratio"] == 100
        await http.aclose()

    asyncio.run(run())


def test_publish_prices_sends_booking_site_channel_and_date_ranges():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v3/listings/prices"
        assert json.loads(request.content) == {
            "listing_id": "direct-101",
            "channel_type": "booking_site",
            "prices": [
                {
                    "start_date": "2026-08-15",
                    "end_date": "2026-08-15",
                    "price": 1558625,
                }
            ],
        }
        return httpx.Response(200, json={"error_code": 200})

    async def run():
        http = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.hostex.test",
        )
        client = HostexClient("token", client=http)
        result = await client.publish_prices(
            "direct-101",
            [
                {
                    "start_date": "2026-08-15",
                    "end_date": "2026-08-15",
                    "price": 1558625,
                }
            ],
        )
        assert result.accepted == 1
        await http.aclose()

    asyncio.run(run())


def test_hostex_status_reports_last_success_and_schedule():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with sessionmaker(engine, expire_on_commit=False)() as db:
        successful = Run(
            kind=RunKind.import_,
            status=RunStatus.succeeded,
            started_at=now - timedelta(hours=3),
            finished_at=now - timedelta(hours=2),
            summary={"calendar": {"received": 100}},
        )
        failed = Run(
            kind=RunKind.import_,
            status=RunStatus.failed,
            started_at=now - timedelta(hours=1),
            finished_at=now - timedelta(minutes=50),
            error="upstream failed",
        )
        db.add_all([successful, failed])
        db.commit()

        result = hostex_status(db)

        assert result["last_successful_import_at"] == successful.finished_at.replace(
            tzinfo=timezone.utc
        )
        assert result["last_import"]["id"] == failed.id
        assert result["schedule"]["enabled"] is True
        assert result["schedule"]["description"] == "Daily at 04:00 WITA"
        assert result["schedule"]["next_import_at"] > datetime.now(
            get_settings().timezone
        )
