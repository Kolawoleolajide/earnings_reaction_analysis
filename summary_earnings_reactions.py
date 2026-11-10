
from pathlib import Path
import pandas as pd

# Load our earnings event dataset
file_path = Path(
    "data/processed/aapl_earnings_event_windows.csv"
)

df = pd.read_csv(file_path)

# Store summary results
summary_results = []

# Analyze each earnings quarter
for quarter, group in df.groupby("fiscal_quarter"):

    group = group.sort_values("trading_day_offset")

    # Retrieve important trading sessions
    announcement_day = group[
        group["trading_day_offset"] == 0
    ].iloc[0]

    first_reaction = group[
        group["trading_day_offset"] == 1
    ].iloc[0]

    day_plus_2 = group[
        group["trading_day_offset"] == 2
    ].iloc[0]

    day_plus_3 = group[
        group["trading_day_offset"] == 3
    ].iloc[0]

    day_minus_3 = group[
        group["trading_day_offset"] == -3
    ].iloc[0]

    # Isolate post-announcement sessions
    post_event = group[
        group["trading_day_offset"].between(1, 3)
    ]

    pre_event = group[
        group["trading_day_offset"].between(-3, -1)
    ]

    # Calculate average trading volume
    avg_pre_volume = pre_event["volume"].mean()
    avg_post_volume = post_event["volume"].mean()

    volume_change_pct = (
        (avg_post_volume / avg_pre_volume) - 1
    ) * 100

    # Calculate pre-announcement price movement
    pre_announcement_return = (
        (announcement_day["close"] /
         day_minus_3["close"]) - 1
    ) * 100

    # Store quarterly metrics
    summary_results.append({

        "fiscal_quarter": quarter,

        "announcement_date":
            announcement_day["date"],

        "announcement_close":
            announcement_day["close"],

        "first_reaction_return_pct":
            first_reaction["cumulative_return_pct"],

        "day_plus_2_return_pct":
            day_plus_2["cumulative_return_pct"],

        "day_plus_3_return_pct":
            day_plus_3["cumulative_return_pct"],

        "highest_post_event_return_pct":
            post_event["cumulative_return_pct"].max(),

        "lowest_post_event_return_pct":
            post_event["cumulative_return_pct"].min(),

        "pre_announcement_return_pct":
            pre_announcement_return,

        "avg_pre_event_volume":
            avg_pre_volume,

        "avg_post_event_volume":
            avg_post_volume,

        "volume_change_pct":
            volume_change_pct
    })


# Create comparison DataFrame
summary_df = pd.DataFrame(summary_results)

# Round numerical results
numeric_columns = summary_df.select_dtypes(
    include="number"
).columns

summary_df[numeric_columns] = (
    summary_df[numeric_columns].round(2)
)

# Save summary
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = (
    output_dir / "aapl_earnings_reaction_summary.csv"
)

summary_df.to_csv(output_file, index=False)

# Display results
print("\n--- Earnings Reaction Comparison ---")

print(summary_df.to_string(index=False))

print("\n--- Summary Statistics ---")

print(
    summary_df[
        [
            "first_reaction_return_pct",
            "day_plus_3_return_pct",
            "volume_change_pct"
        ]
    ].describe().round(2)
)

print(f"\nSummary saved to: {output_file}")
