Mam takie pliki mojego projektu Monitor-2026.


### day_snapshot.py (model danych)
```py
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DaySnapshot:
    sleep_start: Optional[str] = field(
        default=None,
        metadata={"sheet": "start [ts]"},
    )
    sleep_end: Optional[str] = field(
        default=None,
        metadata={"sheet": "end [ts]"},
    )
    sleep_asleep: Optional[str] = field(
        default=None,
        metadata={"sheet": "asleep [h]"},
    )
    sleep_in_bed: Optional[str] = field(
        default=None,
        metadata={"sheet": "in_bed [h]"},
    )
    sleep_efficiency: Optional[float] = field(
        default=None,
        metadata={"sheet": "effic. [%]"},
    )

    sleep_deep: Optional[str] = field(
        default=None,
        metadata={"sheet": "deep [h]"},
    )

    sleep_light: Optional[str] = field(
        default=None,
        metadata={"sheet": "light [h]"},
    )

    sleep_rem: Optional[str] = field(
        default=None,
        metadata={"sheet": "rem [h]"},
    )

    sleep_wake: Optional[str] = field(
        default=None,
        metadata={"sheet": "wake [h]"},
    )   


    hrv: Optional[int] = field(
        default=None,
        metadata={"sheet": "hrv [ms]"},
    )
    rhr: Optional[int] = field(
        default=None,
        metadata={"sheet": "rhr [bpm]"},
    )

    steps: Optional[int] = field(
        default=None,
        metadata={"sheet": "steps [1]"},
    )

    kcal: Optional[int] = field(
        default=None,
        metadata={"sheet": "cal. [kcal]"},
    )
    protein: Optional[int] = field(
        default=None,
        metadata={"sheet": "prot. [g]"},
    )
    fats: Optional[int] = field(
        default=None,
        metadata={"sheet": "fats [g]"},
    )
    carbs: Optional[int] = field(
        default=None,
        metadata={"sheet": "carb. [g]"},
    )
```

### dietonez.py (moduł dietonez)

```py
# dietonez.py
import requests
from typing import Dict, Any


class DietonezClient:
    BASE_URL = "http://192.46.236.119:8080"


    def get(self, path: str, params: Dict[str, str] | None = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


def get_menu_summary(
    client: DietonezClient,
    date: str,
) -> Dict[str, Any]:
    """
    Infra-level call.
    Returns raw API response from dietonez backend.
    """
    return client.get(
        "/api/v1/menu/summary",
        params={"date": date},
    )
```

### fitbit.py (moduł fitbit)


```py
import requests
from typing import Dict, Any


# =========================
# Infrastructure layer
# =========================

class FitbitClient:
    BASE_URL = "https://api.fitbit.com"

    def __init__(self, token: str, user_id: str = "-"):
        self.token = token
        self.user_id = user_id

    def get(self, path: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

import requests
import base64
from typing import Dict, Any


def refresh_fitbit_tokens(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> Dict[str, Any]:
    """
    Refresh Fitbit OAuth2 tokens.

    Returns raw JSON response:
    {
        access_token,
        refresh_token,
        expires_in,
        token_type,
        scope
    }
    """
    auth = base64.b64encode(
        f"{client_id}:{client_secret}".encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }

    response = requests.post(
        "https://api.fitbit.com/oauth2/token",
        headers=headers,
        data=data,
    )

    response.raise_for_status()
    return response.json()


# =========================
# Use cases
# =========================

def get_profile(client: FitbitClient) -> Dict[str, Any]:
    return client.get(
        f"/1/user/{client.user_id}/profile.json"
    )


def get_sleep_by_date(
    client: FitbitClient,
    date: str,
) -> Dict[str, Any]:
    return client.get(
        f"/1.2/user/{client.user_id}/sleep/date/{date}.json"
    )


def get_hrv_by_date(
    client: FitbitClient,
    date: str,
) -> Dict[str, Any]:
    return client.get(
        f"/1/user/{client.user_id}/hrv/date/{date}.json"
    )


def get_activities_by_date(
    client: FitbitClient,
    date: str,
) -> Dict[str, Any]:
    return client.get(
        f"/1/user/{client.user_id}/activities/date/{date}.json"
    )


def get_breathing_rate_by_date(
    client: FitbitClient,
    date: str,
) -> Dict[str, Any]:
    return client.get(
        f"/1/user/{client.user_id}/br/date/{date}.json"
    )


def get_heart_rate_intraday(
    client: FitbitClient,
    date: str,
    detail_level: str = "1min",
) -> Dict[str, Any]:
    return client.get(
        f"/1/user/{client.user_id}/activities/heart/date/{date}/{date}/{detail_level}.json"
    )
```

### sheets (moduł sheets)
```py
LIGHT_BLUE_3 = {
    "red": 0.8235,
    "green": 0.8902,
    "blue": 0.9882,
}

LIGHT_GREY = {
    "red": 0.95,
    "green": 0.95,
    "blue": 0.95,
}

from datetime import datetime

def find_date_row(sheet, date_col: int, date_str: str) -> int:
    """
    Returns row_index for the given date_str.
    """
    col_values = sheet.col_values(date_col)

    # col_values[0:4] = nagłówki
    for i in range(4, len(col_values)):
        if col_values[i].strip() == date_str:
            return i + 1  # index -> row number

    raise RuntimeError(f"Date {date_str} not found in sheet")


def is_sunday(date_str: str) -> bool:
    d = datetime.fromisoformat(date_str)
    return d.weekday() == 6   # Monday=0 … Sunday=6

from datetime import timedelta

def color_row(
    sheet,
    row: int,
    start_col: int,
    end_col: int,
    color: dict,
):
    start_letter = colnum_to_letter(start_col)
    end_letter = colnum_to_letter(end_col)

    sheet.format(
        f"{start_letter}{row}:{end_letter}{row}",
        {"backgroundColor": color},
    )


def colnum_to_letter(n: int) -> str:
    """
    1 -> A
    26 -> Z
    27 -> AA
    """
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def append_week_after(sheet, start_row: int, start_date_str: str, date_col: int):
    start_date = datetime.fromisoformat(start_date_str).date()

    rows = []
    for i in range(1, 8):
        next_date = start_date + timedelta(days=i)
        row = [""] * (date_col - 1) + [next_date.isoformat()]
        rows.append(row)

    sheet.insert_rows(
        rows,
        row=start_row + 1,
        value_input_option="USER_ENTERED",
    )

    last_new_row = start_row + 7

    # kolorujemy ostani nowododany wiersz
    color_row(
        sheet,
        row=last_new_row,
        start_col=12,   # L
        end_col=20,     # T
        color=LIGHT_BLUE_3,
    )

def find_last_date_row(sheet, date_col: int) -> tuple[int, str]: 
    """ 
    Returns (row_index, date_string) 
    """ 
    col_values = sheet.col_values(date_col) 
    # col_values[0:4] = nagłówki 

    for i in range(len(col_values) - 1, 3, -1): 
        if col_values[i].strip(): 
            return i + 1, col_values[i] # +1 bo index → row 
        
    raise RuntimeError("No date found in sheet")

def insert_week_template(col_idx: dict, sheet):
    DATE_COL = col_idx['date [date]']

    last_row, last_date_str = find_last_date_row(sheet, DATE_COL)

    if not is_sunday(last_date_str):
        print("Last date is not Sunday – nothing to do")
        return

    append_week_after(sheet, last_row, last_date_str, DATE_COL)
    print("Week template appended")


from dataclasses import fields
from day_snapshot import DaySnapshot

from dataclasses import fields


def insert_day_values(sheet, date_str: str, snapshot: DaySnapshot, col_idx: dict):
    DATE_COL = col_idx["date [date]"]

    row_idx = find_date_row(sheet, DATE_COL, date_str)

    for f in fields(snapshot):
        value = getattr(snapshot, f.name)
        if value is None:
            continue

        header = f.metadata.get("sheet")
        if not header:
            continue

        col = col_idx[header]
        sheet.update_cell(row_idx, col, value)


```

### util.py (util dla monitor)

```py
def minutes_to_hhmm(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def iso_to_hhmm(iso_ts: str) -> str:
    return iso_ts[11:16]
```

### Monitor (moduł głowny)

```py
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


date = "2025-10-02"

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


GOOGLE_CLOUD_KEY = os.getenv("GOOGLE_CLOUD_KEY")
if not FITBIT_USER_ID:
    raise RuntimeError("Missing GOOGLE_CLOUD_KEY")

spreadsheet = gc.open_by_key(GOOGLE_CLOUD_KEY)
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
```


Struktura plików:
```
.
├── credentials.json
├── day_snapshot.py
├── dietonez.py
├── elo.md
├── elo.txt
├── fitbit.py
├── journal.md
├── labs
│   ├── example-activities-heart.json
│   ├── example-activities.json
│   ├── example-hrv.json
│   ├── example-profile.json
│   └── example-sleep.json
├── monitor.py
├── __pycache__
│   ├── day_snapshot.cpython-310.pyc
│   ├── dietonez.cpython-310.pyc
│   ├── fitbit.cpython-310.pyc
│   ├── sheets.cpython-310.pyc
│   └── util.cpython-310.pyc
├── readme.md
├── sheets.py
└── util.py

2 directories, 21 files
```

Poproszę Ciebie o refaktor taki aby:

- dietonez, fitbit oraz sheets stały się dedykowanymi modułami infrastrukturalnymi opartymi o paradygmat obiektowy (jeden ich client jeden obiekt, bez przekazywania np. sheets do metod Monitora, tylko sheets.insert_day_values(...))
- Monitor to był moduł agregator (on czyta z env i z fitbit_tokens) i to on daje obiekt do...
- skryptu głównego o nazwie job.py, który ma kilka linijek (czyta dzisiejszą datę, jeśli niedziela to wywołuje monitor.insert_week_template, potem wywołuje insert_day_values)
- kod był łatwo rozszerzalny, gdyby kiedyś w monitor i do daysnapshot chciał dodać kolejne źródło, to pisze po prostu kolejny moduł klienta

Łapiesz moją idęę. Zaproponujesz mi dir structure oraz kod takiego projektu?
