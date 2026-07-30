import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from datetime import date, datetime, timezone
from decimal import Decimal

from app.jobs import generate_price_recommendations, serialized_run
from app.models import CompetitorObservation, HostexCalendarDay, HostexListing, Property, Recommendation, Run, RunKind, RunStatus, Setting
from app.worker import create_scheduler


def test_daily_jobs_are_serialized_in_expected_order():
    scheduler = create_scheduler()
    import_job = scheduler.get_job("daily-hostex-import")
    pricing_job = scheduler.get_job("daily-pricing")
    assert import_job is not None
    assert pricing_job is not None
    assert str(import_job.trigger).startswith("cron[hour='4', minute='0'")
    assert str(pricing_job.trigger).startswith("cron[hour='5', minute='0'")
    assert import_job.max_instances == 1
    assert pricing_job.max_instances == 1


def test_failed_serialized_job_rolls_back_partial_data_and_records_failure():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(engine, expire_on_commit=False)() as db:
        with pytest.raises(RuntimeError, match="import failed"):
            with serialized_run(db, RunKind.import_):
                db.add(Setting(key="partial-import", value={"unsafe": True}))
                raise RuntimeError("import failed")
        assert db.get(Setting, "partial-import") is None
        run = db.scalar(select(Run))
        assert run.status == RunStatus.failed
        assert run.error == "import failed"


def test_shadow_optimizer_uses_exact_date_portfolio_and_competitor_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(engine, expire_on_commit=False)() as db:
        prop = Property(
            name="Test Villa", hostex_property_id=1, hostex_listing_id="direct-1",
            booking_site_listing_id="direct-1", active=True,
            min_price=Decimal("500000"), max_price=Decimal("2000000"), rounding_increment=50000,
            competitor_urls=["https://www.airbnb.com/rooms/1", "https://www.airbnb.com/rooms/2"],
        )
        db.add(prop); db.flush()
        db.add(HostexListing(property_id=prop.id, hostex_property_id=1, listing_id="direct-1", channel_type="booking_site", raw={}))
        start = date(2026, 7, 22)
        for offset, inventory in enumerate([0, 1, 1, 0]):
            db.add(HostexCalendarDay(property_id=prop.id, listing_id="direct-1", channel_type="booking_site", stay_date=start.replace(day=start.day + offset), price=Decimal("1000000"), inventory=inventory, minimum_stay=3, raw={}, imported_at=datetime.now(timezone.utc)))
        for offset in range(4):
            stay_date = start.replace(day=start.day + offset)
            db.add(CompetitorObservation(property_id=prop.id, url=prop.competitor_urls[0], stay_date=stay_date, price=Decimal("1200000"), available=True, currency="IDR", scraped_at=datetime.now(timezone.utc), parser_version="test"))
            db.add(CompetitorObservation(property_id=prop.id, url=prop.competitor_urls[1], stay_date=stay_date, price=None, available=False, currency="IDR", scraped_at=datetime.now(timezone.utc), parser_version="test"))
        db.commit()
        assert generate_price_recommendations(db, horizon_days=4, today=start) == 2
        gap_day = db.scalar(select(Recommendation).where(Recommendation.property_id == prop.id, Recommendation.stay_date == date(2026, 7, 23)))
        assert gap_day.actual_price == Decimal("1000000")
        assert gap_day.explanation["market_price"] == 1200000
        assert gap_day.explanation["competitor_unavailability"] == 0.5
        assert gap_day.explanation["portfolio_occupancy"] == 0
        assert gap_day.explanation["engine_version"] == "v2"
