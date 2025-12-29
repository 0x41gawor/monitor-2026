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


