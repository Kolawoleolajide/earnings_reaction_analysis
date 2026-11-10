
from pathlib import Path
import pandas as pd

# Define file locations
stock_file = Path("data/raw/aapl_stock_prices.csv")
calendar_file = Path("data/reference/aapl_earnings_calendar.csv")

# Load datasets
stock = pd.read_csv(stock_file)
events = pd.read_csv(calendar_file)

# Convert date columns
stock["date"] = pd.to_datetime(stock["date"])
events["announcement_date"] = pd.to_datetime(
    events["announcement_date"]
)
events["reaction_date"] = pd.to_datetime(
    events["reaction_date"]
)

# Sort stock data chronologically
stock = stock.sort_values("date").reset_index(drop=True)

# Check for duplicate dates
if stock["date"].duplicated().any():
    raise ValueError("Duplicate stock dates detected.")

# Create a date-to-position lookup
date_positions = {
    date: position
    for position, date in enumerate(stock["date"])
}

# Calculate daily returns across the full dataset
stock["daily_return_pct"] = (
    stock["close"].pct_change() * 100
)

event_windows = []

# Process each earnings announcement
for _, event in events.iterrows():

    announcement_date = event["announcement_date"]
    reaction_date = event["reaction_date"]

    # Confirm both dates exist in stock data
    if announcement_date not in date_positions:
        raise ValueError(
            f"Announcement date not found: {announcement_date}"
        )

    if reaction_date not in date_positions:
        raise ValueError(
            f"Reaction date not found: {reaction_date}"
        )

    announcement_position = date_positions[announcement_date]
    reaction_position = date_positions[reaction_date]

    # Confirm reaction date is the next trading session
    if reaction_position != announcement_position + 1:
        raise ValueError(
            f"Reaction date is not the next trading session: "
            f"{reaction_date}"
        )

    # Define seven-session window
    start_position = reaction_position - 3
    end_position = reaction_position + 3

    if start_position < 0 or end_position >= len(stock):
        raise ValueError(
            f"Insufficient stock data for {event['fiscal_quarter']}"
        )

    # Extract event window
    window = stock.iloc[
        start_position:end_position + 1
    ].copy()

    # Get announcement-day closing price
    baseline_close = stock.loc[
        announcement_position, "close"
    ]

    # Assign trading-day offsets
    window["trading_day_offset"] = range(-3, 4)

    # Calculate cumulative returns against announcement-day close
    window["cumulative_return_pct"] = (
        (window["close"] / baseline_close - 1) * 100
    )

    # Attach earnings information
    window["fiscal_quarter"] = event["fiscal_quarter"]
    window["announcement_date"] = announcement_date
    window["reaction_date"] = reaction_date

    event_windows.append(window)

# Combine all event windows
analysis_df = pd.concat(
    event_windows,
    ignore_index=True
)

# Select relevant analytical columns
analysis_df = analysis_df[
    [
        "fiscal_quarter",
        "announcement_date",
        "reaction_date",
        "trading_day_offset",
        "date",
        "close",
        "daily_return_pct",
        "cumulative_return_pct",
        "volume"
    ]
]

# Save processed dataset
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "aapl_earnings_event_windows.csv"

analysis_df.to_csv(output_file, index=False)

# Display results
print("\n--- Event Window Summary ---")
print(
    analysis_df.groupby("fiscal_quarter")
    .agg(
        trading_sessions=("date", "count"),
        first_date=("date", "min"),
        last_date=("date", "max")
    )
)

print("\n--- Analysis Dataset Shape ---")
print(analysis_df.shape)

print("\n--- First 10 Records ---")
print(analysis_df.head(10).to_string(index=False))

print(f"\nDataset saved to: {output_file}")
