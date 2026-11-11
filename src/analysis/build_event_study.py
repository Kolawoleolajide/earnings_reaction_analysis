
import pandas as pd
from pathlib import Path

# 1. Define file paths
PRICE_PATH = Path("data/hf_data_library/raw/aapl_iex_prices.parquet")
EVENT_PATH = Path("data/hf_data_library/reference/aapl_earnings_events.csv")

OUTPUT_PATH = Path("data/processed/aapl_event_study_window.csv")
SUMMARY_PATH = Path("data/processed/aapl_event_study_summary.csv")

# 2. Load datasets
prices = pd.read_parquet(PRICE_PATH)
events = pd.read_csv(EVENT_PATH, parse_dates=["announcement_date"])

# 3. Prepare dates
prices["datetime"] = pd.to_datetime(prices["datetime"]).dt.normalize()
events["announcement_date"] = (
    pd.to_datetime(events["announcement_date"]).dt.normalize()
)

prices = prices.sort_values("datetime").reset_index(drop=True)

# 4. Create a trading-date lookup
date_lookup = {
    date: index
    for index, date in enumerate(prices["datetime"])
}

event_rows = []

# 5. Build the event windows
for event in events.itertuples(index=False):

    event_date = event.announcement_date

    if event_date not in date_lookup:
        raise ValueError(f"Missing price data for {event_date}")

    event_index = date_lookup[event_date]

    if event_index < 5 or event_index + 5 >= len(prices):
        raise ValueError(f"Insufficient trading history for {event_date}")

    # Event-day closing price is the baseline.
    # Announcements occurred after market close.
    base_close = prices.loc[event_index, "Close"]

    for offset in range(-5, 6):

        price_row = prices.iloc[event_index + offset]
        close = price_row["Close"]

        normalized_price = (close / base_close) * 100

        event_rows.append({
            "ticker": event.ticker,
            "fiscal_quarter": event.fiscal_quarter,
            "announcement_date": event_date,
            "event_time": offset,
            "trading_date": price_row["datetime"],
            "close": close,
            "normalized_price": normalized_price
        })

# 6. Create the event-window dataset
window = pd.DataFrame(event_rows)

# 7. Aggregate performance across all events
summary = (
    window.groupby("event_time")
    .agg(
        mean_normalized_price=("normalized_price", "mean"),
        median_normalized_price=("normalized_price", "median"),
        event_count=("ticker", "count")
    )
    .reset_index()
)

# 8. Save results
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

window.to_csv(OUTPUT_PATH, index=False)
summary.to_csv(SUMMARY_PATH, index=False)

# 9. Display results
print("EVENT STUDY COMPLETED")
print("Total earnings events:", events.shape[0])
print("Total event-window observations:", window.shape[0])

print("\nAVERAGE NORMALIZED PRICE")
print(summary.round(3).to_string(index=False))

print("\nSaved files:")
print(OUTPUT_PATH)
print(SUMMARY_PATH)
