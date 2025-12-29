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
