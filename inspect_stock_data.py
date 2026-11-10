
import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# Load API credentials
load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

if not API_KEY:
    print("API key not found.")
    sys.exit(1)

# API endpoint
url = "https://financialmodelingprep.com/stable/historical-price-eod/full"

params = {
    "symbol": "AAPL",
    "from": "2026-01-22",
    "to": "2026-11-09",
    "apikey": API_KEY
}

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or not data:
        print("Unexpected or empty API response:", data)
        sys.exit(1)

    # Convert API response into a DataFrame
    df = pd.DataFrame(data)

    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Sort records by date
    df = df.sort_values("date").reset_index(drop=True)

    # Save raw stock data
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "aapl_stock_prices.csv"

    df.to_csv(output_file, index=False)

    print(f"\nData successfully saved to: {output_file}")

    # Inspect the dataset
    print("\n--- First 5 Rows ---")
    print(df.head())

    print("\n--- Dataset Shape ---")
    print(df.shape)

    print("\n--- Column Names ---")
    print(df.columns.tolist())

    print("\n--- Data Types ---")
    print(df.dtypes)

    print("\n--- Missing Values ---")
    print(df.isnull().sum())

    print("\n--- Duplicate Dates ---")
    print(df["date"].duplicated().sum())

    print("\n--- Date Range ---")
    print(df["date"].min(), "to", df["date"].max())

except requests.exceptions.RequestException as error:
    print("API request failed:", error)
    sys.exit(1)
