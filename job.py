from datetime import date
from monitor.monitor import Monitor
from infra.fitbit.client import FitbitClient
from infra.sheets.client import SheetsClient
import os

from dotenv import load_dotenv
load_dotenv()

# today = date.today().isoformat()
today = "2025-10-05"

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
)

monitor.insert_week_if_needed(today)
monitor.insert_day(today)