from dotenv import load_dotenv
import os

load_dotenv()

FITBIT_TOKEN = os.getenv("FITBIT_TOKEN")
FITBIT_USER_ID = os.getenv("FITBIT_USER_ID")

if not FITBIT_TOKEN:
    raise RuntimeError("Missing FITBIT_TOKEN")

from datetime import date
import fitbit as fitbit
import util as util
import json

client = fitbit.FitbitClient(token=FITBIT_TOKEN, user_id=FITBIT_USER_ID)

sleep = fitbit.get_sleep_by_date(client, "2025-12-26")
hrv = fitbit.get_hrv_by_date(client, "2025-12-28")
heart = fitbit.get_heart_rate_intraday(client, "2025-12-28")


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


date = "2025-09-22"

print("Sleep: ", get_sleep(date))
print("HRV: ", get_hrv(date))
print("Resting Heart Rate: ", get_heart_rate(date))
print("Steps: ", get_steps(date))
# print("Diet: ", get_diet(date))