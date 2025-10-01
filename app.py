from flask import Flask, render_template, jsonify
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
SPREADSHEET_ID = "1bzVb7hkWRpWHLoktVNEytjA7vYJEBLOy3vQLhHLVWfc"   # <-- your Sheet ID
RANGE_NAME = "players!A:Z"                                      # <-- tab name & range

def fetch_sheet_data():
    """Helper function to fetch Google Sheets data as list of rows."""
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()
    return result.get("values", [])

@app.route("/")
def index():
    values = fetch_sheet_data()
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

    return render_template(
        "index.html",
        tables=[df.to_html(classes="data", index=False)],
        titles=df.columns.values
    )

@app.route("/player/<code>")
def get_player(code):
    values = fetch_sheet_data()
    if not values:
        return jsonify({"error": "No data found"})

    headers = values[0]
    rows = values[1:]

    for row in rows:
        player = dict(zip(headers, row))
        if player.get("PlayerCode") == code:
            return jsonify(player)

    return jsonify({"error": f"Player {code} not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
