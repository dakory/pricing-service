from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.jobs import daily_hostex_import, daily_pricing_run


def create_scheduler() -> BlockingScheduler:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.business_timezone)
    scheduler.add_job(
        daily_hostex_import,
        CronTrigger(hour=4, minute=0, timezone=settings.business_timezone),
        id="daily-hostex-import",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        daily_pricing_run,
        CronTrigger(hour=5, minute=0, timezone=settings.business_timezone),
        id="daily-pricing",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler


def main():
    scheduler = create_scheduler()
    scheduler.start()


if __name__ == "__main__":
    main()
