from flask import Flask, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

app = Flask(__name__, static_folder='static')

# Google Sheets API Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the project directory
json_key_path = os.path.join(BASE_DIR, "wargame-key.json")

creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)
client = gspread.authorize(creds)

# Open the Google Sheet
spreadsheet = client.open("Backend - Millenium of War")  # Match the exact sheet name
sheet = spreadsheet.worksheet("compare")  # Ensure this matches the correct sheet tab

data = sheet.get_all_values()
print("Raw data from Google Sheets:", data)  # Debugging step


@app.route('/')
def index():
    data = [[cell.replace("\n", "").strip() for cell in row] for row in sheet.get_all_values()]
    df = pd.DataFrame(data)



    # 🚀 Remove empty first column if it exists
    if df.iloc[:, 0].isna().all() or df.iloc[:, 0].eq("").all():
        df = df.iloc[:, 1:]  # Drop the first column
    
    df.columns = df.iloc[0]  # Set first row as column headers
    df = df[1:].reset_index(drop=True)  # Remove first row from data
    df.columns.name = None  # Remove extra column header formatting


    # 🛑 Debug print to check what’s actually in the DataFrame
    print("\n==== FINAL DATAFRAME BEFORE HTML RENDER ====")
    print(df.to_string(index=False))

    return render_template("index.html", tables=[df.to_html(classes='data', index=False)], titles=df.columns.values)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

