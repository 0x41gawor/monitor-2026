# app/scheduler.py
from __future__ import annotations

import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import load_config
from app.run_once import run_once, setup_logging


logger = logging.getLogger(__name__)


def main() -> None:
    config = load_config()
    setup_logging()

    scheduler = BlockingScheduler(timezone=config.tzinfo)

    scheduler.add_job(
        func=run_once,
        trigger=CronTrigger(
            hour=config.schedule_hour,
            minute=config.schedule_minute,
            timezone=config.tzinfo,
        ),
        id="daily-monitor-job",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60 * 60 * 6,
        replace_existing=True,
    )

    logger.info(
        "Scheduler configured",
        extra={
            "timezone": config.timezone,
            "hour": config.schedule_hour,
            "minute": config.schedule_minute,
        },
    )

    def _shutdown(signum, _frame):
        logger.info("Received shutdown signal", extra={"signal": signum})
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Scheduler started")
    scheduler.start()


if __name__ == "__main__":
    main()