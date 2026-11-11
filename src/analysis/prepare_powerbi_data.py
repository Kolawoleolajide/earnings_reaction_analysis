
import pandas as pd
from pathlib import Path


# 1. Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "data" / "processed"

REACTIONS_PATH = DATA_PATH / "aapl_earnings_reactions.csv"
WINDOWS_PATH = DATA_PATH / "aapl_earnings_5day_windows.csv"
EVENT_STUDY_PATH = DATA_PATH / "aapl_event_study_summary.csv"

OUTPUT_DIR = DATA_PATH / "powerbi"

DASHBOARD_OUTPUT = OUTPUT_DIR / "aapl_earnings_dashboard.csv"
EVENT_STUDY_OUTPUT = OUTPUT_DIR / "aapl_event_study_summary.csv"


# 2. Helper function for reaction classification
def classify_direction(value):
    if pd.isna(value):
        return "Missing"
    elif value > 0:
        return "Positive"
    elif value < 0:
        return "Negative"
    else:
        return "Flat"


# 3. Load analytical datasets
reactions = pd.read_csv(
    REACTIONS_PATH,
    parse_dates=["announcement_date"]
)

windows = pd.read_csv(
    WINDOWS_PATH,
    parse_dates=["announcement_date"]
)

event_study = pd.read_csv(EVENT_STUDY_PATH)


# 4. Normalize announcement dates
for df in [reactions, windows]:
    df["announcement_date"] = (
        pd.to_datetime(df["announcement_date"]).dt.normalize()
    )


# 5. Define matching keys
keys = ["ticker", "fiscal_quarter", "announcement_date"]

if reactions.duplicated(keys).any():
    raise ValueError("Duplicate earnings events found in reaction data.")

if windows.duplicated(keys).any():
    raise ValueError("Duplicate earnings events found in window data.")


# 6. Select relevant five-session columns
window_columns = keys + [
    "pre_window_start_date",
    "post_window_end_date",
    "pre_5_session_return_pct",
    "post_5_session_return_pct"
]

windows = windows[window_columns]


# 7. Combine the analytical datasets
dashboard = reactions.merge(
    windows,
    on=keys,
    how="left",
    validate="one_to_one"
)

if len(dashboard) != len(reactions):
    raise ValueError("Unexpected change in the number of earnings events.")

if dashboard[
    ["pre_5_session_return_pct", "post_5_session_return_pct"]
].isna().any().any():
    raise ValueError("Some earnings events have missing five-session returns.")


# 8. Add analytical classification fields
dashboard["next_day_reaction"] = (
    dashboard["next_day_close_return_pct"].apply(classify_direction)
)

dashboard["overnight_gap_direction"] = (
    dashboard["overnight_gap_pct"].apply(classify_direction)
)

dashboard["intraday_direction"] = (
    dashboard["intraday_return_pct"].apply(classify_direction)
)

dashboard["pre_earnings_direction"] = (
    dashboard["pre_5_session_return_pct"].apply(classify_direction)
)

dashboard["post_earnings_direction"] = (
    dashboard["post_5_session_return_pct"].apply(classify_direction)
)


# 9. Classify five-day follow-through
def classify_follow_through(row):

    initial = row["next_day_close_return_pct"]
    later = row["post_5_session_return_pct"]

    if initial == 0 or later == 0:
        return "Flat / Mixed"

    if (initial > 0) == (later > 0):
        return "Continued"

    return "Reversed"


dashboard["five_day_follow_through"] = dashboard.apply(
    classify_follow_through,
    axis=1
)

# Identify the data source
dashboard["data_source"] = "IEX"


# 10. Sort the final dashboard table
dashboard = dashboard.sort_values(
    "announcement_date"
).reset_index(drop=True)


# 11. Prepare output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 12. Save Power BI datasets
dashboard.to_csv(DASHBOARD_OUTPUT, index=False)

event_study.to_csv(EVENT_STUDY_OUTPUT, index=False)


# 13. Validate and display results
print("=" * 50)
print("POWER BI DATA PREPARATION COMPLETED")
print("=" * 50)

print("\nEarnings Dashboard Dataset")
print("Total events:", len(dashboard))
print("Total columns:", len(dashboard.columns))
print("Missing values:", dashboard.isna().sum().sum())

print("\nReaction classification:")
print(dashboard["next_day_reaction"].value_counts().to_string())

print("\nFollow-through classification:")
print(
    dashboard["five_day_follow_through"]
    .value_counts()
    .to_string()
)

print("\nEvent Study Dataset")
print("Event-time observations:", len(event_study))

print("\nSaved files:")
print(DASHBOARD_OUTPUT)
print(EVENT_STUDY_OUTPUT)

print("\nPower BI datasets are ready.")
