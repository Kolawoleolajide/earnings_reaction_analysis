
import os
import sys
from pathlib import Path

import requests
import pandas as pd
from dotenv import load_dotenv

# Load API credentials
load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

if not API_KEY:
    print("API key not found. Check your .env file.")
    sys.exit(1)

# API configuration
url = "https://financialmodelingprep.com/stable/historical-price-eod/full"

params = {
    "symbol": "SPY",
    "from": "2026-01-22",
    "to": "2026-11-09",
    "apikey": API_KEY
}

try:
    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

except requests.exceptions.RequestException:
    print("API request failed. Check your connection and API access.")
    sys.exit(1)

# Check API response
if not isinstance(data, list) or not data:
    print("Unexpected or empty API response:", data)
    sys.exit(1)

# Convert response into DataFrame
df = pd.DataFrame(data)

# Check required columns
required_columns = ["symbol", "date", "close"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    print("Missing columns:", missing_columns)
    sys.exit(1)

# Prepare dates
df["date"] = pd.to_datetime(df["date"])

# Sort chronologically
df = df.sort_values("date").reset_index(drop=True)

# Check duplicate dates
if df["date"].duplicated().any():
    print("Duplicate dates detected in SPY data.")
    sys.exit(1)

# Save raw benchmark data
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "spy_stock_prices.csv"

df.to_csv(output_file, index=False)

# Display results
print("\n--- SPY Data Retrieval ---")
print("Records retrieved:", len(df))
print("Dataset shape:", df.shape)

print(
    "Date range:",
    df["date"].min(),
    "to",
    df["date"].max()
)

print("\n--- First 5 Records ---")
print(df.head().to_string(index=False))

print(f"\nData saved to: {output_file}")
