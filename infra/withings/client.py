import hmac
import hashlib
import json
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


class WithingsClient:
    BASE_URL = "https://wbsapi.withings.net"
    MEASURE_PATH = "/measure"

    # meastype ids
    WEIGHT = 1
    FAT_MASS = 8
    MUSCLE_MASS = 76

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tokens_file: str,
        timezone: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens_file = tokens_file
        self.tz = ZoneInfo(timezone)

        self._load_tokens()

    # ============================================================
    # Low-level HTTP
    # ============================================================

    def _post(self, path: str, data: dict, headers: dict | None = None) -> dict:
        """
        Withings answers 200 with {"status": int, "body": {...}}.
        status 0 == ok, 401 == invalid/expired access token.
        """
        response = requests.post(f"{self.BASE_URL}{path}", data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def _measure(self, params: dict) -> dict:
        for attempt in (1, 2):
            payload = self._post(
                self.MEASURE_PATH,
                {"action": "getmeas", **params},
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if payload["status"] == 401 and attempt == 1:
                self._refresh_tokens()
                continue

            if payload["status"] != 0:
                raise RuntimeError(
                    f"Withings getmeas failed: status={payload['status']} "
                    f"error={payload.get('error')}"
                )
            return payload["body"]

    # ============================================================
    # Signing / token handling
    # ============================================================

    def _sign(self, *parts) -> str:
        message = ",".join(str(p) for p in parts)
        return hmac.new(
            self.client_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _get_nonce(self) -> str:
        timestamp = int(time.time())
        payload = self._post(
            "/v2/signature",
            {
                "action": "getnonce",
                "client_id": self.client_id,
                "timestamp": timestamp,
                "signature": self._sign("getnonce", self.client_id, timestamp),
            },
        )
        if payload["status"] != 0:
            raise RuntimeError(f"Withings getnonce failed: {payload}")
        return payload["body"]["nonce"]

    def _load_tokens(self):
        with open(self.tokens_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")

        if not self.access_token or not self.refresh_token:
            raise RuntimeError("Invalid Withings token file")

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
        nonce = self._get_nonce()

        payload = self._post(
            "/v2/oauth2",
            {
                "action": "requesttoken",
                "client_id": self.client_id,
                "nonce": nonce,
                "signature": self._sign("requesttoken", self.client_id, nonce),
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
        )
        if payload["status"] != 0:
            raise RuntimeError(f"Withings token refresh failed: {payload}")

        body = payload["body"]

        # The refresh token rotates on every refresh: always store the new one
        self.access_token = body["access_token"]
        self.refresh_token = body["refresh_token"]

        self._save_tokens()

    # ============================================================
    # Public API
    # ============================================================

    def body_composition(self, date: str) -> dict:
        """
        First weigh-in of the given day (local time) as
        {"weight": kg, "fat": kg, "muscle": kg}; missing values are None.
        """
        day_start = datetime.fromisoformat(date).replace(tzinfo=self.tz)
        day_end = day_start + timedelta(days=1)

        body = self._measure(
            {
                "meastypes": f"{self.WEIGHT},{self.FAT_MASS},{self.MUSCLE_MASS}",
                "category": 1,
                "startdate": int(day_start.timestamp()),
                "enddate": int(day_end.timestamp()) - 1,
            }
        )

        groups = sorted(body.get("measuregrps") or [], key=lambda g: g["date"])
        if not groups:
            print(f"No body composition data for {date}")
            return {"weight": None, "fat": None, "muscle": None}

        values = {
            m["type"]: round(m["value"] * 10 ** m["unit"], 1)
            for m in groups[0]["measures"]
        }
        return {
            "weight": values.get(self.WEIGHT),
            "fat": values.get(self.FAT_MASS),
            "muscle": values.get(self.MUSCLE_MASS),
        }
