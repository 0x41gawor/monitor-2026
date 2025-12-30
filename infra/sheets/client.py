from dataclasses import fields
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from monitor.snapshot import DaySnapshot


# ============================================================
# Colors
# ============================================================

LIGHT_BLUE_3 = {
    "red": 0.8235,
    "green": 0.8902,
    "blue": 0.9882,
}


# ============================================================
# Client
# ============================================================

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

    # ============================================================
    # Helpers
    # ============================================================

    def _find_date_row(self, date_str: str) -> int:
        col = self.col_idx["date [date]"]
        for i, v in enumerate(self.sheet.col_values(col)[4:], start=5):
            if v.strip() == date_str:
                return i
        raise RuntimeError(f"Date {date_str} not found")

    def _colnum_to_letter(self, n: int) -> str:
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

    def _color_row(self, row: int, start_col: int, end_col: int, color: dict):
        start_letter = self._colnum_to_letter(start_col)
        end_letter = self._colnum_to_letter(end_col)

        self.sheet.format(
            f"{start_letter}{row}:{end_letter}{row}",
            {"backgroundColor": color},
        )

    def is_sunday(self, date_str: str) -> bool:
        return datetime.fromisoformat(date_str).weekday() == 6

    # ============================================================
    # Public API
    # ============================================================

    def insert_cell(self, date_str: str, header: str, value):
        row = self._find_date_row(date_str)
        col = self.col_idx[header]
        self.sheet.update_cell(row, col, value)


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
        """
        If last date in sheet is Sunday, append next week
        and color the last inserted row.
        """
        date_col = self.col_idx["date [date]"]
        values = self.sheet.col_values(date_col)
        last_row = len(values)
        last_date = values[-1]

        if not self.is_sunday(last_date):
            return

        start_date = datetime.fromisoformat(last_date).date()

        rows = [
            [""] * (date_col - 1) + [(start_date + timedelta(days=i)).isoformat()]
            for i in range(1, 8)
        ]

        self.sheet.insert_rows(
            rows,
            row=last_row + 1,
            value_input_option="USER_ENTERED",
        )

        last_new_row = last_row + 7

        # kolorujemy ostatni nowo dodany wiersz
        self._color_row(
            row=last_new_row,
            start_col=12,  # L
            end_col=20,    # T
            color=LIGHT_BLUE_3,
        )