
import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("HFDL_API_KEY")

# Project paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "hf_data_library" / "raw"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API configuration
TICKER = "AAPL"

API_URL = (
    f"https://api.hfdatalibrary.com/v1/download-token/{TICKER}"
)

PARAMS = {
    "timeframe": "daily",
    "format": "csv",
    "version": "clean"
}

HEADERS = {
    "X-API-Key": API_KEY
}


def fetch_stock_data():

    if not API_KEY:
        raise ValueError("HFDL_API_KEY not found in .env")

    print(f"Requesting {TICKER} historical data...")

    # Step 1: Request temporary download URL
    response = requests.get(
        API_URL,
        headers=HEADERS,
        params=PARAMS,
        timeout=30
    )

    response.raise_for_status()

    download_info = response.json()
    download_url = download_info["url"]

    print("Download URL received successfully.")

    # Step 2: Download CSV data
    data_response = requests.get(
        download_url,
        timeout=60
    )

    data_response.raise_for_status()

    # Save CSV
    output_file = OUTPUT_DIR / "aapl_iex_prices.csv"

    with open(output_file, "wb") as file:
        file.write(data_response.content)

    # Inspect downloaded data
    df = pd.read_csv(output_file)

    if df.empty:
        raise ValueError("Downloaded dataset is empty.")

    print("\n--- DATA RETRIEVAL SUMMARY ---")
    print(f"Ticker: {TICKER}")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    print("\n--- FIRST 5 ROWS ---")
    print(df.head())

    print(f"\nDataset saved to: {output_file}")


if __name__ == "__main__":
    fetch_stock_data()
