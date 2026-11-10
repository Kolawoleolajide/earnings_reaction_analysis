
from pathlib import Path
import sys
import pandas as pd

# Define input files
calendar_file = Path("data/reference/aapl_earnings_calendar.csv")

aapl_event_file = Path(
    "data/processed/aapl_earnings_event_windows.csv"
)

benchmark_file = Path(
    "data/processed/aapl_spy_event_windows.csv"
)

spy_file = Path("data/raw/spy_stock_prices.csv")

# Load datasets
calendar = pd.read_csv(calendar_file)
aapl_events = pd.read_csv(aapl_event_file)
benchmark = pd.read_csv(benchmark_file)
spy = pd.read_csv(spy_file)

# Convert date columns
calendar["announcement_date"] = pd.to_datetime(
    calendar["announcement_date"]
)
calendar["reaction_date"] = pd.to_datetime(
    calendar["reaction_date"]
)

for df in [aapl_events, benchmark, spy]:
    df["date"] = pd.to_datetime(df["date"])

# Create event ID
calendar["event_id"] = (
    calendar["fiscal_quarter"]
    .str.replace(" ", "_", regex=False)
)

# Build the event dimension
dim_events = calendar[
    [
        "event_id",
        "fiscal_quarter",
        "announcement_date",
        "reaction_date",
        "conference_call_time_pt",
        "source_url"
    ]
].copy()

# Prepare Apple's daily information
aapl_detail = aapl_events[
    [
        "fiscal_quarter",
        "date",
        "daily_return_pct",
        "volume"
    ]
].rename(
    columns={
        "daily_return_pct": "aapl_daily_return_pct",
        "volume": "aapl_volume"
    }
)

# Prepare SPY daily information
spy = spy.sort_values("date").copy()

spy["spy_daily_return_pct"] = (
    spy["close"].pct_change() * 100
)

spy_detail = spy[
    ["date", "volume", "spy_daily_return_pct"]
].rename(
    columns={"volume": "spy_volume"}
)

# Prepare benchmark event data
fact_events = benchmark.merge(
    aapl_detail,
    on=["fiscal_quarter", "date"],
    how="left",
    validate="one_to_one"
)

fact_events = fact_events.merge(
    spy_detail,
    on="date",
    how="left",
    validate="many_to_one"
)

# Rename price and return columns
fact_events = fact_events.rename(
    columns={
        "close": "aapl_close",
        "cumulative_return_pct": "aapl_cumulative_return_pct"
    }
)

# Generate event ID
fact_events["event_id"] = (
    fact_events["fiscal_quarter"]
    .str.replace(" ", "_", regex=False)
)

# Classify trading sessions
def classify_session(offset):
    if offset < 0:
        return "Pre-announcement"
    elif offset == 0:
        return "Announcement day"
    else:
        return "Post-announcement"


fact_events["session_period"] = (
    fact_events["trading_day_offset"]
    .apply(classify_session)
)

# Select final fact table columns
fact_events = fact_events[
    [
        "event_id",
        "trading_day_offset",
        "session_period",
        "date",
        "aapl_close",
        "spy_close",
        "aapl_daily_return_pct",
        "spy_daily_return_pct",
        "aapl_cumulative_return_pct",
        "spy_cumulative_return_pct",
        "benchmark_relative_return_pp",
        "aapl_volume",
        "spy_volume"
    ]
]

# Sort fact table
fact_events = fact_events.sort_values(
    ["event_id", "trading_day_offset"]
).reset_index(drop=True)

# Validate output
if len(dim_events) != 4:
    raise ValueError("Expected four earnings events.")

if len(fact_events) != 28:
    raise ValueError("Expected 28 event-window records.")

if dim_events["event_id"].duplicated().any():
    raise ValueError("Duplicate event IDs detected.")

if fact_events.isnull().any().any():
    raise ValueError(
        "Missing values detected in Power BI fact table."
    )

if set(fact_events["event_id"]) != set(dim_events["event_id"]):
    raise ValueError("Event IDs do not match.")

# Create Power BI output folder
output_dir = Path("data/processed/powerbi")
output_dir.mkdir(parents=True, exist_ok=True)

# Export tables
dim_events.to_csv(
    output_dir / "DimEarningsEvents.csv",
    index=False
)

fact_events.to_csv(
    output_dir / "FactEventWindows.csv",
    index=False
)

# Display results
print("\n--- POWER BI DATA PREPARATION ---")

print("\nDimension table:")
print("Rows:", len(dim_events))
print("Columns:", len(dim_events.columns))

print("\nFact table:")
print("Rows:", len(fact_events))
print("Columns:", len(fact_events.columns))

print("\nEvent IDs:")
print(dim_events["event_id"].tolist())

print("\nFact table missing values:")
print(fact_events.isnull().sum())

print("\nData preparation completed successfully!")

print(f"\nFiles saved in: {output_dir}")
