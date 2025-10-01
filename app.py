from flask import Flask, render_template
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import os, json

app = Flask(__name__, static_folder='static')

# Google Sheets API Authentication
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Load creds from environment variable (Render-safe)
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)

# Spreadsheet details
SPREADSHEET_ID = "1bzVb7hkWRpWHLoktVNEytjA7vYJEBLOy3vQLhHLVWfc"       # Sheet ID
RANGE_NAME = "players!A:Z"                  # <-- Sheet Tab Name and Column Range

@app.route('/')
def index():
    # Fetch data from Google Sheets
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    if not values:
        return "No data found in Google Sheet"

    # Clean into DataFrame
    data = [[cell.replace("\n", "").strip() for cell in row] for row in values]
    df = pd.DataFrame(data)

    # Remove empty first column if present
    if df.iloc[:, 0].isna().all() or df.iloc[:, 0].eq("").all():
        df = df.iloc[:, 1:]

    df.columns = df.iloc[0]          # First row = headers
    df = df[1:].reset_index(drop=True)
    df.columns.name = None

    # Debug print in Render logs
    print("\n==== FINAL DATAFRAME BEFORE HTML RENDER ====")
    print(df.to_string(index=False))

    return render_template("index.html",
                           tables=[df.to_html(classes="data", index=False)],
                           titles=df.columns.values)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
