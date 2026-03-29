import os

from infra.sheets.client import SheetsClient
from monitor.colorer import Colorer, ColorPalette

from dotenv import load_dotenv
load_dotenv()


# ============================================================
# Config
# ============================================================

ROWS_START = 53
ROWS_END = 107

HEADERS = [
    "start [ts]",
    "end [ts]",
    "asleep [h]",
    "in_bed [h]",
]


# ============================================================
# Bootstrap
# ============================================================

def build_colorer() -> Colorer:
    return Colorer(
        strong_palette=ColorPalette(
                ok="#57BB8A",
                warn="#FFD666",
                bad="#E67C73",
            ),
            soft_palette=ColorPalette(
                ok="#99DABA",
                warn="#FCE7AD",
                bad="#EEA49E",
            ),
    )


def build_sheets() -> SheetsClient:
    return SheetsClient(
            credentials_file="credentials.json",
            spreadsheet_key=os.environ["GOOGLE_CLOUD_KEY"],
            worksheet="Monitor-2026",
    )


# ============================================================
# Main logic
# ============================================================

def colorize_range():
    sheets = build_sheets()
    colorer = build_colorer()

    headers = [
        "start [ts]",
        "end [ts]",
        "asleep [h]",
        "in_bed [h]",
    ]

    rows = sheets.read_range(
        start_row=ROWS_START,
        end_row=ROWS_END,
        headers=headers,
    )

    requests = []

    for i, row in enumerate(rows):
        sheet_row = ROWS_START + i

        for header in headers:
            value = row.get(header)
            if not value:
                continue

            hex_color = colorer.get_color(header, value)
            if not hex_color:
                continue

            requests.append(
                sheets.build_color_request(
                    row=sheet_row,
                    header=header,
                    hex_color=hex_color,
                )
            )

    sheets.batch_color_cells(requests)



if __name__ == "__main__":
    colorize_range()