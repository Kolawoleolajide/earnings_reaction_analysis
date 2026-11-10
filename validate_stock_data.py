
from pathlib import Path
import pandas as pd

# Locate our raw data
file_path = Path("data/raw/aapl_stock_prices.csv")

# Load the CSV
df = pd.read_csv(file_path)

# Required columns
required_columns = [
    "symbol", "date", "open", "high", "low",
    "close", "volume", "change", "changePercent", "vwap"
]

# Check for missing columns
missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Convert date to datetime
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Check numeric columns
numeric_columns = [
    "open", "high", "low", "close",
    "volume", "change", "changePercent", "vwap"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Check missing values
print("\n--- Missing Values ---")
print(df.isnull().sum())

# Check duplicate stock records
print("\n--- Duplicate Records ---")
print(df.duplicated(subset=["symbol", "date"]).sum())

# Check invalid price relationships
invalid_prices = (
    (df["low"] > df["high"]) |
    (df["open"] < df["low"]) |
    (df["open"] > df["high"]) |
    (df["close"] < df["low"]) |
    (df["close"] > df["high"])
)

print("\n--- Invalid OHLC Records ---")
print(invalid_prices.sum())

# Check negative trading volume
print("\n--- Negative Trading Volume ---")
print((df["volume"] < 0).sum())

# Check non-positive prices
price_columns = ["open", "high", "low", "close", "vwap"]

invalid_price_values = (df[price_columns] <= 0).sum()

print("\n--- Non-positive Price Values ---")
print(invalid_price_values)

# Dataset summary
print("\n--- Dataset Summary ---")
print("Total records:", len(df))
print("Stock symbols:", df["symbol"].unique())
print("Date range:", df["date"].min(), "to", df["date"].max())
