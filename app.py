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
SPREADSHEET_ID = "1bzVb7hkWRpWHLoktVNEytjA7vYJEBLOy3vQLhHLVWfc"
PLAYER_RANGE = "players!A:Z"
INFO_RANGE = "Info!A6:B"          # news ticker
SUGGESTIONS_RANGE = "Info!C6:D"   # game suggestionss

def fetch_sheet_data(range_name):
    """Helper function to fetch Google Sheets data as list of rows."""
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    return result.get("values", [])

@app.route("/")
def index():
    # Fetch ticker messages
    ticker_values = fetch_sheet_data(INFO_RANGE)
    ticker_items = [f"{row[0]} - {row[1]}" for row in ticker_values if len(row) >= 2]

    # Fetch suggestions
    suggestion_values = fetch_sheet_data(SUGGESTIONS_RANGE)
    suggestion_items = [f"{row[0]} - {row[1]}" for row in suggestion_values if len(row) >= 2]

    return render_template(
        "index.html",
        ticker_items=ticker_items,
        suggestion_items=suggestion_items
    )

@app.route("/player/<code>")
def get_player(code):
    values = fetch_sheet_data(PLAYER_RANGE)
    if not values:
        return jsonify({"error": "No data found"})

    headers = values[0]
    rows = values[1:]

    for row in rows:
        if row[0] == code:  # PlayerCode in col A
            player = dict(zip(headers, row))

            structured = {
                "PlayerCode": player.get("PlayerCode"),
                "NationName": player.get(headers[1]),  # col B
                "QuickStats": {h: player.get(h) for h in headers[2:6]},
                "Revenues": {h: player.get(h) for h in headers[6:11]},
                "Expenditures": {h: player.get(h) for h in headers[11:16]},
                "Other": {h: player.get(h) for h in headers[16:]}
            }
            return jsonify(structured)

    return jsonify({"error": f"Player {code} not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
