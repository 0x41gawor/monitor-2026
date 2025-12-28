import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES,
)

gc = gspread.authorize(creds)

sheet = gc.open_by_key("13mpOKAxKXc9H5TgOQ8yIvGWOEQ12g6XGuX-HJeDuCNE").sheet1

spreadsheet = gc.open_by_key("13mpOKAxKXc9H5TgOQ8yIvGWOEQ12g6XGuX-HJeDuCNE")

sheet = spreadsheet.worksheet("Monitor-2026")


print(sheet.get("A1:T4"))