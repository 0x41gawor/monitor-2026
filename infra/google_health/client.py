import json
import time
from datetime import datetime, timedelta, timezone

import requests
from requests import HTTPError


class GoogleHealthClient:
    BASE_URL = "https://health.googleapis.com/v4/users/me"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SOURCE_FAMILY = "users/me/dataSourceFamilies/google-wearables"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tokens_file: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens_file = tokens_file

        self._load_tokens()

    # ============================================================
    # Low-level HTTP
    # ============================================================

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """
        Calls the API; on 401 refreshes the access token once and retries.
        """
        url = f"{self.BASE_URL}{path}"

        for attempt in (1, 2):
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            }
            response = requests.request(method, url, headers=headers, **kwargs)

            if response.status_code == 401 and attempt == 1:
                self._refresh_tokens()
                continue

            if response.status_code == 429:
                raise RuntimeError("Google Health rate limit hit – slow down")

            response.raise_for_status()
            return response.json()

    def _get(self, path: str, params: dict | None = None) -> dict:
        return self._request("GET", path, params=params)

    def _post(self, path: str, body: dict) -> dict:
        return self._request("POST", path, json=body)

    # ============================================================
    # Token handling
    # ============================================================

    def _load_tokens(self):
        with open(self.tokens_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")

        if not self.access_token or not self.refresh_token:
            raise RuntimeError("Invalid Google Health token file")

    def _save_tokens(self):
        with open(self.tokens_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                },
                f,
                indent=2,
            )

    def _refresh_tokens(self):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()

        refreshed = response.json()

        self.access_token = refreshed["access_token"]
        # Google usually does not return a new refresh token on refresh
        self.refresh_token = refreshed.get("refresh_token", self.refresh_token)

        self._save_tokens()

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _next_day(date: str) -> str:
        return (datetime.fromisoformat(date) + timedelta(days=1)).date().isoformat()

    @staticmethod
    def _to_local_iso(utc_ts: str, utc_offset: str) -> str:
        """
        '2026-11-06T00:21:00Z' + '3600s' -> '2026-11-06T01:21:00'
        """
        utc = datetime.fromisoformat(utc_ts.replace("Z", "+00:00"))
        local = utc.astimezone(timezone(timedelta(seconds=int(utc_offset.rstrip("s")))))
        return local.replace(tzinfo=None).isoformat()

    def _daily(self, data_type: str, date: str) -> dict | None:
        """
        Returns the single data point of a Daily data type for the given date.
        """
        field = data_type.replace("-", "_")
        data = self._get(
            f"/dataTypes/{data_type}/dataPoints",
            params={
                "filter": (
                    f'{field}.date >= "{date}" AND '
                    f'{field}.date < "{self._next_day(date)}"'
                )
            },
        )
        points = data.get("dataPoints") or []
        return points[0] if points else None

    # ============================================================
    # Public API
    # ============================================================

    def sleep(self, date: str) -> dict:
        """
        Sleep that ended on the given date, in the shape of the legacy
        Fitbit response: {"sleep": [...], "summary": {...}}.
        """
        data = self._get(
            "/dataTypes/sleep/dataPoints:reconcile",
            params={
                "dataSourceFamily": self.SOURCE_FAMILY,
                "filter": (
                    f'sleep.interval.civil_end_time >= "{date}" AND '
                    f'sleep.interval.civil_end_time < "{self._next_day(date)}"'
                ),
            },
        )
        points = data.get("dataPoints") or []
        if not points:
            return {"sleep": [], "summary": {}}

        main = next(
            (p for p in points if p["sleep"].get("metadata", {}).get("mainSleep")),
            None,
        )
        if main is None:
            main = max(
                points,
                key=lambda p: int(p["sleep"].get("summary", {}).get("minutesInSleepPeriod", 0)),
            )

        sleep = main["sleep"]
        interval = sleep["interval"]
        summary = sleep.get("summary", {})

        minutes_asleep = int(summary.get("minutesAsleep", 0))
        minutes_in_bed = int(summary.get("minutesInSleepPeriod", 0))
        stages = {
            s["type"]: int(s["minutes"]) for s in summary.get("stagesSummary", [])
        }

        # The API has no efficiency field; documented formula
        efficiency = round(minutes_asleep / minutes_in_bed * 100) if minutes_in_bed else None

        return {
            "sleep": [
                {
                    "isMainSleep": True,
                    "startTime": self._to_local_iso(interval["startTime"], interval["startUtcOffset"]),
                    "endTime": self._to_local_iso(interval["endTime"], interval["endUtcOffset"]),
                    "efficiency": efficiency,
                }
            ],
            "summary": {
                "totalMinutesAsleep": minutes_asleep,
                "totalTimeInBed": minutes_in_bed,
                "stages": {
                    "deep": stages.get("DEEP"),
                    "light": stages.get("LIGHT"),
                    "rem": stages.get("REM"),
                    "wake": stages.get("AWAKE"),
                },
            },
        }

    def hrv(self, date: str) -> int:
        point = self._daily("daily-heart-rate-variability", date)
        if not point:
            print(f"No HRV data for {date}")
            return None
        return round(point["dailyHeartRateVariability"]["averageHeartRateVariabilityMilliseconds"])

    def steps(self, date: str) -> int:
        day, next_day = (
            datetime.fromisoformat(date),
            datetime.fromisoformat(self._next_day(date)),
        )
        data = self._post(
            "/dataTypes/steps/dataPoints:dailyRollUp",
            {
                "range": {
                    "start": {"date": {"year": day.year, "month": day.month, "day": day.day}, "time": {}},
                    "end": {"date": {"year": next_day.year, "month": next_day.month, "day": next_day.day}, "time": {}},
                },
                "windowSizeDays": 1,
            },
        )
        points = data.get("rollupDataPoints") or []
        steps = int(points[0]["steps"]["countSum"]) if points else 0
        if steps == 0:
            print(f"No steps data for {date}")
            return None
        return steps

    def rhr(self, date: str) -> int:
        point = self._daily("daily-resting-heart-rate", date)
        if not point:
            print(f"No RHR data for {date}")
            return None
        return int(point["dailyRestingHeartRate"]["beatsPerMinute"])
