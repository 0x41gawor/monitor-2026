from dataclasses import fields
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from monitor.snapshot import DaySnapshot


class SheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_key: str, worksheet: str):
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        self.sheet = (
            gspread.authorize(creds)
            .open_by_key(spreadsheet_key)
            .worksheet(worksheet)
        )

        headers = self.sheet.row_values(4)
        self.col_idx = {h: i + 1 for i, h in enumerate(headers)}

    # ---------- helpers ----------
    def _find_date_row(self, date_str: str) -> int:
        col = self.col_idx["date [date]"]
        for i, v in enumerate(self.sheet.col_values(col)[4:], start=5):
            if v.strip() == date_str:
                return i
        raise RuntimeError(f"Date {date_str} not found")

    def is_sunday(self, date_str: str) -> bool:
        return datetime.fromisoformat(date_str).weekday() == 6

    # ---------- public ----------
    def insert_day(self, date_str: str, snapshot: DaySnapshot):
        row = self._find_date_row(date_str)

        for f in fields(snapshot):
            value = getattr(snapshot, f.name)
            if value is None:
                continue
            col = self.col_idx.get(f.metadata.get("sheet"))
            if col:
                self.sheet.update_cell(row, col, value)

    def insert_week_template(self):
        date_col = self.col_idx["date [date]"]
        values = self.sheet.col_values(date_col)
        last_date = values[-1]
        if not self.is_sunday(last_date):
            return

        start = datetime.fromisoformat(last_date).date()
        rows = [
            [""] * (date_col - 1) + [(start + timedelta(days=i)).isoformat()]
            for i in range(1, 8)
        ]

        self.sheet.insert_rows(rows, row=len(values) + 1)