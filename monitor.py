from dotenv import load_dotenv
import os

import json
from pathlib import Path

from day_snapshot import DaySnapshot

FITBIT_TOKENS_FILE = Path(".fitbit_tokens.json")

if not FITBIT_TOKENS_FILE.exists():
    raise RuntimeError("Missing .fitbit_tokens.json")

with FITBIT_TOKENS_FILE.open("r", encoding="utf-8") as f:
    tokens = json.load(f)

FITBIT_ACCESS_TOKEN = tokens.get("access_token")
FITBIT_REFRESH_TOKEN = tokens.get("refresh_token")
FITBIT_EXPIRES_AT = tokens.get("expires_at")  # optional

if not FITBIT_ACCESS_TOKEN or not FITBIT_REFRESH_TOKEN:
    raise RuntimeError("Invalid .fitbit_tokens.json (missing tokens)")

load_dotenv()

FITBIT_USER_ID = os.getenv("FITBIT_USER_ID")
if not FITBIT_USER_ID:
    raise RuntimeError("Missing FITBIT_USER_ID")

FITBIT_CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
FITBIT_CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")

if not FITBIT_CLIENT_ID or not FITBIT_CLIENT_SECRET:
    raise RuntimeError("Missing FITBIT_CLIENT_ID / FITBIT_CLIENT_SECRET")


from datetime import date
import fitbit as fitbit
import util as util
import json

from datetime import datetime, timedelta


def save_fitbit_tokens(
    access_token: str,
    refresh_token: str,
    expires_in: int,
):
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (
            datetime.utcnow() + timedelta(seconds=expires_in)
        ).isoformat(),
    }

    with FITBIT_TOKENS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

import fitbit
from requests import HTTPError


def ensure_fitbit_client():
    global FITBIT_ACCESS_TOKEN, FITBIT_REFRESH_TOKEN

    client = fitbit.FitbitClient(
        token=FITBIT_ACCESS_TOKEN,
        user_id=FITBIT_USER_ID,
    )

    try:
        # lekki ping – najtańszy endpoint
        fitbit.get_profile(client)
        return client

    except HTTPError as e:
        if e.response.status_code != 401:
            raise

        print("Access token expired – refreshing...")

        refreshed = fitbit.refresh_fitbit_tokens(
            client_id=FITBIT_CLIENT_ID,
            client_secret=FITBIT_CLIENT_SECRET,
            refresh_token=FITBIT_REFRESH_TOKEN,
        )

        FITBIT_ACCESS_TOKEN = refreshed["access_token"]
        FITBIT_REFRESH_TOKEN = refreshed["refresh_token"]

        save_fitbit_tokens(
            access_token=FITBIT_ACCESS_TOKEN,
            refresh_token=FITBIT_REFRESH_TOKEN,
            expires_in=refreshed["expires_in"],
        )

        return fitbit.FitbitClient(
            token=FITBIT_ACCESS_TOKEN,
            user_id=FITBIT_USER_ID,
        )


client = ensure_fitbit_client()


def get_steps(date: str) -> int:
    activities = fitbit.get_activities_by_date(client, date)
    return activities["summary"]["steps"]

def get_hrv(date: str) -> int:
    hrv_data = fitbit.get_hrv_by_date(client, date)
    return round(hrv_data["hrv"][0]["value"]["dailyRmssd"])

def get_sleep(date: str):
    sleep_data = fitbit.get_sleep_by_date(client, date)

    main_sleep = next(
        (s for s in sleep_data["sleep"] if s.get("isMainSleep")),
        None
    )

    if not main_sleep:
        return None

    return {
        "startTime": util.iso_to_hhmm(main_sleep["startTime"]),
        "endTime": util.iso_to_hhmm(main_sleep["endTime"]),
        "timeAsleep": util.minutes_to_hhmm(sleep_data["summary"]["totalMinutesAsleep"]),
        "timeInBed": util.minutes_to_hhmm(sleep_data["summary"]["totalTimeInBed"]),
        "efficiency": main_sleep["efficiency"],
        "deep": util.minutes_to_hhmm(sleep_data["summary"]["stages"]["deep"]),
        "light": util.minutes_to_hhmm(sleep_data["summary"]["stages"]["light"]),
        "rem": util.minutes_to_hhmm(sleep_data["summary"]["stages"]["rem"]),
        "wake": util.minutes_to_hhmm(sleep_data["summary"]["stages"]["wake"]),
    }

def get_heart_rate(date: str):
    hr_data = fitbit.get_heart_rate_intraday(client, date)
    return hr_data["activities-heart"][0]["value"]["restingHeartRate"]

import dietonez

diet_client = dietonez.DietonezClient()

def get_diet(date: str) -> dict:
    summary = dietonez.get_menu_summary(diet_client, date)

    return {
        "kcal": round(summary["kcal"]),
        "prot": round(summary["proteins"]),
        "fats": round(summary["fats"]),
        "carb": round(summary["carbs"]),
    }


date = "2025-10-01"

sleep = get_sleep(date)
hrv = get_hrv(date)
rhr = get_heart_rate(date)
steps = get_steps(date)
print("Sleep: ", sleep)
print("HRV: ", hrv)
print("Resting Heart Rate: ", rhr) 
print("Steps: ", steps)
# print("Diet: ", get_diet(date))

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES,
)

gc = gspread.authorize(creds)

sheet = gc.open_by_key("13mpOKAxKXc9H5TgOQ8yIvGWOEQ12g6XGuX-HJeDuCNE").sheet1

spreadsheet = gc.open_by_key("13mpOKAxKXc9H5TgOQ8yIvGWOEQ12g6XGuX-HJeDuCNE")

sheet = spreadsheet.worksheet("Monitor-2026")

headers = sheet.row_values(4)
col_idx = {h: i+1 for i, h in enumerate(headers)}

import sheets as sheets

# sheets.insert_week_template(col_idx, sheet)

snapshot = DaySnapshot(
    sleep_start=sleep["startTime"],
    sleep_end=sleep["endTime"],
    sleep_asleep=sleep["timeAsleep"],
    sleep_in_bed=sleep["timeInBed"],
    sleep_efficiency=sleep["efficiency"],
    sleep_deep=sleep["deep"],
    sleep_light=sleep["light"],
    sleep_rem=sleep["rem"],
    sleep_wake=sleep["wake"],
    hrv=hrv,
    rhr=rhr,
    steps=steps,
)

sheets.insert_day_values(sheet, date, snapshot, col_idx)