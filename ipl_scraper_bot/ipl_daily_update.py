# ipl_daily_update.py

import os
import time
import pandas as pd
import gspread
from google.auth import default
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from sklearn.preprocessing import StandardScaler, LabelEncoder
from google.colab import auth  # Remove this line if not running on Google Colab

# Step 1: Setup Selenium
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

# Step 2: Scrape IPL data
def scrape_ipl_2025_stats():
    driver = setup_driver()
    driver.get("https://www.howstat.com/Cricket/statistics/IPL/PlayerList.asp")
    time.sleep(3)
    Select(driver.find_element(By.NAME, "cboSeason")).select_by_value("2025")
    time.sleep(2)
    table = driver.find_element(By.XPATH, '//table[@class="TableLined"]')
    rows = table.find_elements(By.TAG_NAME, "tr")
    headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th")]
    data = [[col.text.strip() for col in row.find_elements(By.TAG_NAME, "td")] for row in rows[1:]]
    driver.quit()
    if headers and data:
        df = pd.DataFrame(data, columns=headers)
        df["Match_Date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
        return df
    return None

# Step 3: Maintain historical data
HISTORY_FILE = "ipl_2025_matchwise_stats.csv"

def save_and_update_history(new_data):
    if new_data is not None:
        existing = pd.read_csv(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame()
        combined = pd.concat([existing, new_data], ignore_index=True)
        combined.to_csv(HISTORY_FILE, index=False)

# Step 4: Recent form stats
def get_recent_form():
    if not os.path.exists(HISTORY_FILE):
        return None
    df = pd.read_csv(HISTORY_FILE)
    df["Match_Date"] = pd.to_datetime(df["Match_Date"])
    for col in ["Runs", "Bat Avg", "Wickets", "Bowl Avg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    recent = df.sort_values("Match_Date", ascending=False).groupby("Name").head(5)
    return recent.groupby("Name").agg({
        "Runs": "mean", "Bat Avg": "mean", "Wickets": "mean", "Bowl Avg": "mean"
    }).reset_index().rename(columns={
        "Runs": "Avg Runs (Last 5 Matches)",
        "Bat Avg": "Avg Batting Avg",
        "Wickets": "Avg Wickets",
        "Bowl Avg": "Avg Bowling Avg"
    })

# Step 5: Recent form score
def compute_recent_form_score(df):
    if df is None or df.empty:
        return None
    for col in ["Avg Runs (Last 5 Matches)", "Avg Batting Avg", "Avg Wickets", "Avg Bowling Avg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.fillna(0)
    df["Recent_Form_Score"] = (
        df["Avg Runs (Last 5 Matches)"] * 0.5 +
        df["Avg Batting Avg"] * 0.3 +
        df["Avg Wickets"] * 0.1 +
        df["Avg Bowling Avg"] * 0.1
    )
    return df

# Step 6: Preprocess data
def preprocess_data(df, categorical_cols=None, scale_cols=None):
    df.fillna(df.median(numeric_only=True), inplace=True)
    df.fillna(df.mode().iloc[0], inplace=True)
    df.drop_duplicates(inplace=True)
    if categorical_cols:
        for col in categorical_cols:
            if df[col].dtype == 'object':
                df[col] = LabelEncoder().fit_transform(df[col])
    if scale_cols:
        df[scale_cols] = StandardScaler().fit_transform(df[scale_cols])
    return df

# Step 7: Upload to Google Sheets
def upload_to_google_sheets(data):
    if data is None or data.empty:
        return
    creds, _ = default()
    gc = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/1YtbjJ9UyKu7jo-fHKYzhAZS0iilJaOjL0jQQx1Aprac/edit?usp=sharing"
    sheet = gc.open_by_url(sheet_url).sheet1
    sheet.clear()
    sheet.update([data.columns.tolist()] + data.values.tolist())
    print("✅ Data updated to Google Sheets!")

# Step 8: Run full flow
def main():
    new_data = scrape_ipl_2025_stats()
    save_and_update_history(new_data)
    recent_form = get_recent_form()
    form_with_score = compute_recent_form_score(recent_form)
    if form_with_score is not None:
        cat_cols = [col for col in form_with_score.select_dtypes(include='object') if col.lower() != 'name']
        num_cols = form_with_score.select_dtypes(include='number').columns.tolist()
        preprocessed = preprocess_data(form_with_score, cat_cols, num_cols)
        upload_to_google_sheets(preprocessed)

if __name__ == "__main__":
    main()
