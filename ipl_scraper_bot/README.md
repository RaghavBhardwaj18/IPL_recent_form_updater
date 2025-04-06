# IPL Scraper Bot 🏏

A Python automation script that scrapes IPL 2025 player stats from HowStat, computes recent form, and uploads results to Google Sheets using Google Sheets API.

## Features
- Selenium-based web scraper (headless)
- Google Sheets integration with `gspread`
- Computes recent form & fantasy scores
- Automatically maintains match history in CSV

## Run Locally
```bash
pip install -r requirements.txt
python main.py
