import base64
import json
import requests
from requests import HTTPError


class FitbitClient:
    BASE_URL = "https://api.fitbit.com"

    def __init__(
        self,
        user_id: str,
        client_id: str,
        client_secret: str,
        tokens_file: str,
    ):
        self.user_id = user_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens_file = tokens_file

        self._load_tokens()

    # ============================================================
    # Low-level HTTP
    # ============================================================

    def _get(self, path: str) -> dict:
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Token handling
    # ============================================================

    def _load_tokens(self):
        with open(self.tokens_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")

        if not self.access_token or not self.refresh_token:
            raise RuntimeError("Invalid Fitbit token file")

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
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        response = requests.post(
            "https://api.fitbit.com/oauth2/token",
            headers=headers,
            data=data,
        )
        response.raise_for_status()

        refreshed = response.json()

        self.access_token = refreshed["access_token"]
        self.refresh_token = refreshed["refresh_token"]

        self._save_tokens()

    # ============================================================
    # Ensure-valid-token (PING-BASED)
    # ============================================================

    def _ensure(self):
        """
        Ensure access token is valid.
        Strategy:
        - make a cheap ping call
        - if 401 → refresh token → retry
        """
        try:
            self._get(f"/1/user/{self.user_id}/profile.json")
        except HTTPError as e:
            if e.response.status_code != 401:
                raise

            # token expired
            self._refresh_tokens()

    # ============================================================
    # Public API
    # ============================================================

    def sleep(self, date: str) -> dict:
        self._ensure()
        return self._get(
            f"/1.2/user/{self.user_id}/sleep/date/{date}.json"
        )

    def hrv(self, date: str) -> int:
        self._ensure()
        data = self._get(
            f"/1/user/{self.user_id}/hrv/date/{date}.json"
        )
        return round(data["hrv"][0]["value"]["dailyRmssd"])

    def steps(self, date: str) -> int:
        self._ensure()
        data = self._get(
            f"/1/user/{self.user_id}/activities/date/{date}.json"
        )
        return data["summary"]["steps"]

    def rhr(self, date: str) -> int:
        self._ensure()
        data = self._get(
            f"/1/user/{self.user_id}/activities/heart/date/{date}/{date}/1min.json"
        )
        return data["activities-heart"][0]["value"]["restingHeartRate"]
