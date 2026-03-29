# app/server.py
from __future__ import annotations

import logging
import signal
import sys

from app.config import load_config
from app.http import create_http_app
from app.run_once import setup_logging
from app.scheduler import build_scheduler


logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    config = load_config()

    scheduler = build_scheduler(config)
    scheduler.start()

    logger.info("Scheduler started")

    app = create_http_app(scheduler)

    def _shutdown(signum, _frame):
        logger.info("Received shutdown signal=%s", signum)
        try:
            if scheduler.running:
                scheduler.shutdown(wait=False)
        finally:
            sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info(
        "HTTP server starting on 0.0.0.0:%s",
        5000,
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()