import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from datetime import date, datetime, timezone
from decimal import Decimal

from app.jobs import generate_price_recommendations, pricing_configuration, serialized_run
from app.models import CompetitorListing, CompetitorObservation, HostexCalendarDay, HostexListing, PricingGroup, Property, Recommendation, Run, RunKind, RunStatus, Setting
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


def test_shadow_optimizer_uses_exact_date_group_and_competitor_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(engine, expire_on_commit=False)() as db:
        group = PricingGroup(
            name="Test market",
            competitor_urls=[
                "https://www.airbnb.com/rooms/1",
                "https://www.airbnb.com/rooms/2",
            ],
            pricing_settings={},
        )
        db.add(group)
        db.flush()
        prop = Property(
            name="Test Villa", pricing_group_id=group.id, hostex_property_id=1, hostex_listing_id="direct-1",
            booking_site_listing_id="direct-1", active=True,
            min_price=Decimal("500000"), max_price=Decimal("2000000"), rounding_increment=50000,
            pricing_settings={},
        )
        db.add(prop); db.flush()
        competitor_one = CompetitorListing(
            pricing_group_id=group.id,
            canonical_url=group.competitor_urls[0],
            external_listing_id="1",
        )
        competitor_two = CompetitorListing(
            pricing_group_id=group.id,
            canonical_url=group.competitor_urls[1],
            external_listing_id="2",
        )
        db.add_all([competitor_one, competitor_two]); db.flush()
        db.add(HostexListing(property_id=prop.id, hostex_property_id=1, listing_id="direct-1", channel_type="booking_site", raw={}))
        start = date(2026, 7, 22)
        for offset, inventory in enumerate([0, 1, 1, 0]):
            db.add(HostexCalendarDay(property_id=prop.id, listing_id="direct-1", channel_type="booking_site", stay_date=start.replace(day=start.day + offset), price=Decimal("1000000"), inventory=inventory, minimum_stay=3, raw={}, imported_at=datetime.now(timezone.utc)))
        for offset in range(4):
            stay_date = start.replace(day=start.day + offset)
            db.add(CompetitorObservation(competitor_listing_id=competitor_one.id, stay_date=stay_date, price=Decimal("1200000"), available=True, available_for_checkin=True, minimum_stay=2, currency="IDR", scraped_at=datetime.now(timezone.utc), parser_version="test", price_method="test"))
            db.add(CompetitorObservation(competitor_listing_id=competitor_two.id, stay_date=stay_date, price=None, available=False, available_for_checkin=False, minimum_stay=None, currency="IDR", scraped_at=datetime.now(timezone.utc), parser_version="test", price_method="test"))
        db.commit()
        assert generate_price_recommendations(db, horizon_days=4, today=start) == 2
        gap_day = db.scalar(select(Recommendation).where(Recommendation.property_id == prop.id, Recommendation.stay_date == date(2026, 7, 23)))
        assert gap_day.actual_price == Decimal("1000000")
        assert gap_day.explanation["market_price"] == 1200000
        assert gap_day.explanation["competitor_unavailability"] == 0.5
        assert gap_day.explanation["pricing_group_occupancy"] == 0
        assert gap_day.explanation["engine_version"] == "v2"


def test_property_pricing_settings_override_only_selected_global_values():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(engine, expire_on_commit=False)() as db:
        group = PricingGroup(
            name="Inherited market",
            competitor_urls=[],
            pricing_settings={},
        )
        db.add(group)
        db.flush()
        prop = Property(
            name="Inherited Villa",
            pricing_group_id=group.id,
            hostex_listing_id="direct-2",
            active=True,
            min_price=Decimal("500000"),
            max_price=Decimal("2000000"),
            rounding_increment=50000,
            pricing_settings={
                "base_price_mode": "manual",
                "manual_base_price": 1_250_000,
                "urgency_adjustment_enabled": False,
                "urgency_adjustments": [
                    {"maximum_days": 7, "adjustment": -0.12}
                ],
            },
        )
        db.add(prop)
        db.add(
            Setting(
                key="pricing_engine_v2",
                value={
                    "competitor_weight": 0.6,
                    "pricing_group_weight": 0.4,
                    "market_price_adjustment": -0.1,
                },
            )
        )
        db.commit()

        effective = pricing_configuration(db, prop)
        assert effective["base_price_mode"] == "manual"
        assert effective["manual_base_price"] == 1_250_000
        assert effective["urgency_adjustment_enabled"] is False
        assert effective["competitor_weight"] == 0.6
        assert effective["market_price_adjustment"] == -0.1
        assert effective["demand_adjustment_enabled"] is True
        assert effective["urgency_adjustments"] == [
            {"maximum_days": 3, "adjustment": -0.15},
            {"maximum_days": 7, "adjustment": -0.12},
            {"maximum_days": 14, "adjustment": -0.05},
            {"maximum_days": 30, "adjustment": -0.02},
        ]
