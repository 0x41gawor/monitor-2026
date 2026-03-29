# app/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    fitbit_user_id: str
    fitbit_client_id: str
    fitbit_client_secret: str
    fitbit_tokens_file: str

    google_credentials_file: str
    google_spreadsheet_key: str
    google_worksheet: str

    dietonez_base_url: str

    target_sleep_start: str
    target_sleep_end: str
    target_in_bed_time: str
    target_asleep_time: str

    schedule_hour: int
    schedule_minute: int
    timezone: str

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_config() -> AppConfig:
    return AppConfig(
        fitbit_user_id=_require("FITBIT_USER_ID"),
        fitbit_client_id=_require("FITBIT_CLIENT_ID"),
        fitbit_client_secret=_require("FITBIT_CLIENT_SECRET"),
        fitbit_tokens_file=os.getenv("FITBIT_TOKENS_FILE", ".fitbit_tokens.json"),

        google_credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
        google_spreadsheet_key=_require("GOOGLE_CLOUD_KEY"),
        google_worksheet=os.getenv("GOOGLE_WORKSHEET", "Monitor-2026"),

        dietonez_base_url=_require("DIETONEZ_BASE_URL"),

        target_sleep_start=_require("TARGET_SLEEP_START"),
        target_sleep_end=_require("TARGET_SLEEP_END"),
        target_in_bed_time=_require("TARGET_IN_BED_TIME"),
        target_asleep_time=_require("TARGET_ASLEEP_TIME"),

        schedule_hour=int(os.getenv("SCHEDULE_HOUR", "11")),
        schedule_minute=int(os.getenv("SCHEDULE_MINUTE", "5")),
        timezone=os.getenv("TIMEZONE", "Europe/Warsaw"),
    )