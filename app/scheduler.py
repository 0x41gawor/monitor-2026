# app/scheduler.py
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import AppConfig
from app.run_once import run_once


logger = logging.getLogger(__name__)


def build_scheduler(config: AppConfig) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=config.tzinfo)

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
        "Scheduler configured: timezone=%s hour=%s minute=%s",
        config.timezone,
        config.schedule_hour,
        config.schedule_minute,
    )

    return scheduler