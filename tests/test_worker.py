import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.jobs import serialized_run
from app.models import Run, RunKind, RunStatus, Setting
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
