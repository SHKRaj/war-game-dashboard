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
INFO_RANGE = "Info!A6:B"   # ticker messages

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
    # Fetch players data
    values = fetch_sheet_data(PLAYER_RANGE)
    if not values:
        return "No data found in Google Sheet"

    # Clean into DataFrame
    data = [[cell.replace("\n", "").strip() for cell in row] for row in values]
    df = pd.DataFrame(data)

    if df.iloc[:, 0].isna().all() or df.iloc[:, 0].eq("").all():
        df = df.iloc[:, 1:]

    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    df.columns.name = None

    # Fetch ticker messages from Info!A6:B
    ticker_values = fetch_sheet_data(INFO_RANGE)
    ticker_items = [
        f"{row[0]} - {row[1]}" for row in ticker_values if len(row) >= 2
    ]

    print("\n==== FINAL DATAFRAME BEFORE HTML RENDER ====")
    print(df.to_string(index=False))
    print("Ticker items:", ticker_items)

    return render_template(
        "index.html",
        tables=[df.to_html(classes="data", index=False)],
        titles=df.columns.values,
        ticker_items=ticker_items
    )

@app.route("/player/<code>")
def get_player(code):
    values = fetch_sheet_data(PLAYER_RANGE)
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
