import requests
from typing import Any, Dict


class DietonezClient:
    def __init__(self, base_url: str):
        """
        base_url example: http://100.20.400.30:8000
        """
        self.base_url = base_url.rstrip("/")

    # ============================================================
    # Low-level HTTP
    # ============================================================

    def _get(self, path: str, params: Dict[str, str] | None = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Public API
    # ============================================================

    def menu_summary(self, date: str) -> Dict[str, Any]:
        """
        Returns raw menu summary for given date.

        Expected keys (example):
        {
            "kcal": float,
            "proteins": float,
            "fats": float,
            "carbs": float
        }
        """
        return self._get(
            "/api/v1/menu/summary",
            params={"date": date},
        )
