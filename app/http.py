# app/http.py
from __future__ import annotations

import hmac
import logging
from datetime import datetime
from functools import wraps
from threading import Lock

from flask import Flask, jsonify, request

from app.config import load_config
from app.run_log import RunLog
from app.run_once import run_once


logger = logging.getLogger(__name__)


def create_http_app(scheduler) -> Flask:
    app = Flask(__name__)
    run_lock = Lock()
    config = load_config()

    def require_api_key(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            provided = request.headers.get("X-API-Key", "")
            if not hmac.compare_digest(provided.encode("utf-8"), config.api_key.encode("utf-8")):
                return jsonify({"status": "fail", "error": "Unauthorized."}), 401
            return view(*args, **kwargs)

        return wrapper

    @app.get("/api/v1/health/live")
    def health_live():
        return jsonify(
            {
                "status": "ok",
                "service": "monitor-2026",
                "check": "live",
            }
        ), 200

    @app.get("/api/v1/health/ready")
    def health_ready():
        try:
            config = load_config()
        except Exception as exc:
            return jsonify(
                {
                    "status": "fail",
                    "service": "monitor-2026",
                    "check": "ready",
                    "reason": f"config error: {exc}",
                }
            ), 503

        scheduler_running = getattr(scheduler, "running", False)

        if not scheduler_running:
            return jsonify(
                {
                    "status": "fail",
                    "service": "monitor-2026",
                    "check": "ready",
                    "reason": "scheduler not running",
                    "timezone": config.timezone,
                }
            ), 503

        return jsonify(
            {
                "status": "ok",
                "service": "monitor-2026",
                "check": "ready",
                "scheduler_running": True,
                "timezone": config.timezone,
                "schedule_hour": config.schedule_hour,
                "schedule_minute": config.schedule_minute,
            }
        ), 200

    @app.get("/api/v1/runs")
    @require_api_key
    def api_runs():
        try:
            limit = min(max(int(request.args.get("limit", 20)), 1), 200)
        except ValueError:
            return jsonify({"status": "fail", "error": "Invalid limit."}), 400

        return jsonify({"runs": RunLog(config.run_log_db).recent(limit)}), 200

    @app.post("/api/v1/run")
    @app.get("/api/v1/run")
    @require_api_key
    def api_run():
        requested_date = request.args.get("date")

        if requested_date is not None:
            try:
                datetime.fromisoformat(requested_date)
            except ValueError:
                return jsonify(
                    {
                        "status": "fail",
                        "error": "Invalid date format. Expected YYYY-MM-DD.",
                    }
                ), 400

        acquired = run_lock.acquire(blocking=False)
        if not acquired:
            return jsonify(
                {
                    "status": "fail",
                    "error": "Run already in progress.",
                }
            ), 409

        try:
            run_once(requested_date, trigger="manual")
        except Exception as exc:
            logger.exception("Manual run failed")
            return jsonify(
                {
                    "status": "fail",
                    "error": str(exc),
                    "date": requested_date,
                }
            ), 500
        finally:
            run_lock.release()

        return jsonify(
            {
                "status": "ok",
                "message": "Run completed.",
                "date": requested_date,
            }
        ), 200

    return app