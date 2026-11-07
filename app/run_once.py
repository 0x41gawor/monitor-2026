# app/run_once.py
from __future__ import annotations

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.bootstrap import build_monitor
from app.config import load_config
from app.run_log import RunLog


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )


def resolve_run_date(explicit_date: str | None, timezone_name: str) -> str:
    if explicit_date:
        try:
            datetime.fromisoformat(explicit_date)
        except ValueError as exc:
            raise SystemExit("Invalid --date format. Expected YYYY-MM-DD") from exc
        return explicit_date

    return datetime.now(ZoneInfo(timezone_name)).date().isoformat()


def run_once(run_date: str | None = None, trigger: str = "scheduler") -> None:
    config = load_config()
    setup_logging()

    resolved_date = resolve_run_date(run_date, config.timezone)
    logger.info("Starting monitor run for date=%s", resolved_date)

    run_log = RunLog(config.run_log_db)
    run_id = run_log.start(resolved_date, trigger)
    started = time.monotonic()

    try:
        monitor = build_monitor(config)
        monitor.insert_week_if_needed(resolved_date)
        monitor.insert_day(resolved_date)
    except Exception as exc:
        run_log.finish(run_id, "fail", started, error=f"{type(exc).__name__}: {exc}")
        raise

    run_log.finish(run_id, "ok", started)
    logger.info("Monitor run completed for date=%s", resolved_date)