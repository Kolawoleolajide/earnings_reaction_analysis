
from pathlib import Path
import sys
import pandas as pd

# Define file paths
event_file = Path(
    "data/processed/aapl_earnings_event_windows.csv"
)

spy_file = Path(
    "data/raw/spy_stock_prices.csv"
)

# Load datasets
events = pd.read_csv(event_file)
spy = pd.read_csv(spy_file)

# Convert date columns
for column in ["date", "announcement_date", "reaction_date"]:
    events[column] = pd.to_datetime(events[column])

spy["date"] = pd.to_datetime(spy["date"])

# Convert prices to numeric
events["close"] = pd.to_numeric(
    events["close"], errors="coerce"
)

spy["close"] = pd.to_numeric(
    spy["close"], errors="coerce"
)

# Check data quality
if events["date"].duplicated().any():
    raise ValueError("Duplicate dates in event dataset.")

if spy["date"].duplicated().any():
    raise ValueError("Duplicate dates in SPY dataset.")

if events["close"].isna().any() or spy["close"].isna().any():
    raise ValueError("Missing or invalid closing prices detected.")

# Verify each event has seven correctly aligned sessions
for quarter, group in events.groupby("fiscal_quarter"):

    offsets = sorted(group["trading_day_offset"].tolist())

    if offsets != list(range(-3, 4)):
        raise ValueError(
            f"Incorrect trading-day offsets for {quarter}"
        )

    event_date = group.loc[
        group["trading_day_offset"] == 0, "date"
    ].iloc[0]

    announcement_date = group[
        "announcement_date"
    ].iloc[0]

    if event_date != announcement_date:
        raise ValueError(
            f"Announcement date mismatch for {quarter}"
        )

# Select SPY prices
spy_prices = spy[
    ["date", "close"]
].rename(
    columns={"close": "spy_close"}
)

# Calculate SPY daily returns
spy_prices = spy_prices.sort_values("date").copy()

spy_prices["spy_daily_return_pct"] = (
    spy_prices["spy_close"].pct_change() * 100
)

# Merge Apple event windows with SPY
combined = events.merge(
    spy_prices,
    on="date",
    how="left",
    validate="one_to_one",
    indicator=True
)

# Check whether every event date matched
unmatched = combined[
    combined["_merge"] != "both"
]

if not unmatched.empty:
    print("Dates missing from SPY dataset:")
    print(unmatched[["fiscal_quarter", "date"]])
    sys.exit(1)

combined = combined.drop(columns="_merge")

# Find SPY announcement-day closing price for each quarter
spy_baselines = combined.loc[
    combined["trading_day_offset"] == 0,
    ["fiscal_quarter", "spy_close"]
].rename(
    columns={"spy_close": "spy_announcement_close"}
)

combined = combined.merge(
    spy_baselines,
    on="fiscal_quarter",
    how="left",
    validate="many_to_one"
)

# Calculate SPY cumulative return
combined["spy_cumulative_return_pct"] = (
    (
        combined["spy_close"] /
        combined["spy_announcement_close"]
    ) - 1
) * 100

# Calculate Apple performance relative to SPY
combined["benchmark_relative_return_pp"] = (
    combined["cumulative_return_pct"] -
    combined["spy_cumulative_return_pct"]
)

# Select analytical columns
combined = combined[
    [
        "fiscal_quarter",
        "announcement_date",
        "trading_day_offset",
        "date",
        "close",
        "spy_close",
        "cumulative_return_pct",
        "spy_cumulative_return_pct",
        "benchmark_relative_return_pp"
    ]
]

# Save comparison dataset
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = (
    output_dir / "aapl_spy_event_windows.csv"
)

combined.to_csv(output_file, index=False)

# Display results
print("\n--- Benchmark Matching Results ---")
print("Apple event records:", len(events))
print("Matched SPY records:", len(combined))

print("\n--- Benchmark Comparison by Quarter ---")

print(
    combined.groupby("fiscal_quarter")[
        [
            "cumulative_return_pct",
            "spy_cumulative_return_pct",
            "benchmark_relative_return_pp"
        ]
    ].agg(["min", "max"]).round(2)
)

print("\n--- First 10 Records ---")
print(combined.head(10).to_string(index=False))

print(f"\nComparison saved to: {output_file}")
