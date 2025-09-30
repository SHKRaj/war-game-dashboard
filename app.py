from flask import Flask, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Load service account credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'service_account.json'   # My JSON key file

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Google Sheet info
SPREADSHEET_ID = '1bzVb7hkWRpWHLoktVNEytjA7vYJEBLOy3vQLhHLVWfc'   # Google Sheets ID
RANGE_NAME = 'Players!A1:Z'              # Testing w/ All


@app.route("/player/<code>")
def get_player(code):
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()

    values = result.get('values', [])

    if not values:
        return jsonify({"error": "No data found"})

    headers = values[0]  # first row = column names
    rows = values[1:]    # rest = data

    for row in rows:
        player = dict(zip(headers, row))
        if player.get("PlayerCode") == code:
            return jsonify(player)

    return jsonify({"error": "Player not found"})

from flask import render_template

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
