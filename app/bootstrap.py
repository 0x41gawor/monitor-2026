# app/bootstrap.py
from __future__ import annotations

import os

from app.config import AppConfig
from infra.dietonez.client import DietonezClient
from infra.fitbit.client import FitbitClient
from infra.sheets.client import SheetsClient
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
    fitbit = FitbitClient(
        user_id=config.fitbit_user_id,
        client_id=config.fitbit_client_id,
        client_secret=config.fitbit_client_secret,
        tokens_file=config.fitbit_tokens_file,
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
        fitbit=fitbit,
        sheets=sheets,
        dietonez=dietonez,
        colorer=colorer,
    )