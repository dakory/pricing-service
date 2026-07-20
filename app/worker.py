from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.jobs import daily_pricing_run


def main():
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.business_timezone)
    scheduler.add_job(
        daily_pricing_run,
        CronTrigger(hour=5, minute=0, timezone=settings.business_timezone),
        id="daily-pricing",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.start()


if __name__ == "__main__":
    main()

