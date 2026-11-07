# app/bootstrap.py
from __future__ import annotations

import os

from app.config import AppConfig
from infra.dietonez.client import DietonezClient
from infra.google_health.client import GoogleHealthClient
from infra.sheets.client import SheetsClient
from infra.withings.client import WithingsClient
from monitor.colorer import ColorPalette, Colorer
from monitor.monitor import Monitor


def build_colorer(config: AppConfig) -> Colorer:
    # Colorer obecnie czyta targety z os.environ,
    # więc pilnujemy zgodności z istniejącym kodem.
    os.environ["TARGET_SLEEP_START"] = config.target_sleep_start
    os.environ["TARGET_SLEEP_END"] = config.target_sleep_end
    os.environ["TARGET_IN_BED_TIME"] = config.target_in_bed_time
    os.environ["TARGET_ASLEEP_TIME"] = config.target_asleep_time

    return Colorer(
        strong_palette=ColorPalette(
            ok="#57BB8A",
            warn="#FFD666",
            bad="#E67C73",
        ),
        soft_palette=ColorPalette(
            ok="#99DABA",
            warn="#FCE7AD",
            bad="#EEA49E",
        ),
    )


def build_monitor(config: AppConfig) -> Monitor:
    google_health = GoogleHealthClient(
        client_id=config.google_health_client_id,
        client_secret=config.google_health_client_secret,
        tokens_file=config.google_health_tokens_file,
    )

    withings = WithingsClient(
        client_id=config.withings_client_id,
        client_secret=config.withings_client_secret,
        tokens_file=config.withings_tokens_file,
        timezone=config.timezone,
    )

    sheets = SheetsClient(
        credentials_file=config.google_credentials_file,
        spreadsheet_key=config.google_spreadsheet_key,
        worksheet=config.google_worksheet,
    )

    dietonez = DietonezClient(
        base_url=config.dietonez_base_url,
    )

    colorer = build_colorer(config)

    return Monitor(
        google_health=google_health,
        withings=withings,
        sheets=sheets,
        dietonez=dietonez,
        colorer=colorer,
    )