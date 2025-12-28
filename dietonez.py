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
