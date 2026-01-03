import argparse
import os
from datetime import date, datetime

from dotenv import load_dotenv
load_dotenv()

from monitor.monitor import Monitor
from monitor.colorer import Colorer, ColorPalette
from infra.fitbit.client import FitbitClient
from infra.sheets.client import SheetsClient
from infra.dietonez.client import DietonezClient


# ============================================================
# Argument parsing
# ============================================================

def parse_args() -> str:
    parser = argparse.ArgumentParser(
        description="Daily Monitor job (Fitbit → Google Sheets)",
    )

    parser.add_argument(
        "--date",
        type=str,
        help="Date in ISO format (YYYY-MM-DD). Defaults to today.",
    )

    args = parser.parse_args()

    if args.date:
        try:
            datetime.fromisoformat(args.date)
            return args.date
        except ValueError:
            raise SystemExit("Invalid --date format. Expected YYYY-MM-DD")

    return date.today().isoformat()


# ============================================================
# Main
# ============================================================

def main():
    run_date = parse_args()

    monitor = Monitor(
        fitbit=FitbitClient(
            user_id=os.environ["FITBIT_USER_ID"],
            client_id=os.environ["FITBIT_CLIENT_ID"],
            client_secret=os.environ["FITBIT_CLIENT_SECRET"],
            tokens_file=".fitbit_tokens.json",
        ),
        sheets=SheetsClient(
            credentials_file="credentials.json",
            spreadsheet_key=os.environ["GOOGLE_CLOUD_KEY"],
            worksheet="Monitor-2026",
        ),
        dietonez=DietonezClient(
            base_url=os.environ["DIETONEZ_BASE_URL"],
        ),
        colorer=Colorer(
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
        ),
    )

    monitor.insert_week_if_needed(run_date)
    monitor.insert_day(run_date)


if __name__ == "__main__":
    main()