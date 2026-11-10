
from pathlib import Path
import pandas as pd

# Load benchmark comparison dataset
file_path = Path(
    "data/processed/aapl_spy_event_windows.csv"
)

df = pd.read_csv(file_path)

# Prepare summary results
results = []

# Analyze each earnings quarter
for quarter, group in df.groupby("fiscal_quarter"):

    group = group.sort_values("trading_day_offset")

    # Retrieve first reaction session
    day_1 = group[
        group["trading_day_offset"] == 1
    ]

    # Retrieve third reaction session
    day_3 = group[
        group["trading_day_offset"] == 3
    ]

    # Validate required observations
    if len(day_1) != 1 or len(day_3) != 1:
        raise ValueError(
            f"Missing T+1 or T+3 record for {quarter}"
        )

    day_1 = day_1.iloc[0]
    day_3 = day_3.iloc[0]

    results.append({

        "fiscal_quarter": quarter,

        "announcement_date":
            group["announcement_date"].iloc[0],

        # First reaction session
        "aapl_t1_return_pct":
            day_1["cumulative_return_pct"],

        "spy_t1_return_pct":
            day_1["spy_cumulative_return_pct"],

        "relative_t1_pp":
            day_1["benchmark_relative_return_pp"],

        # Third reaction session
        "aapl_t3_return_pct":
            day_3["cumulative_return_pct"],

        "spy_t3_return_pct":
            day_3["spy_cumulative_return_pct"],

        "relative_t3_pp":
            day_3["benchmark_relative_return_pp"]
    })


# Create summary DataFrame
summary = pd.DataFrame(results)

# Round numerical values
numeric_columns = summary.select_dtypes(
    include="number"
).columns

summary[numeric_columns] = (
    summary[numeric_columns].round(2)
)

# Classify relative performance
summary["market_comparison"] = summary[
    "relative_t3_pp"
].apply(
    lambda value: (
        "Outperformed SPY"
        if value > 0
        else "Underperformed SPY"
        if value < 0
        else "Matched SPY"
    )
)

# Save output
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = (
    output_dir / "aapl_spy_reaction_summary.csv"
)

summary.to_csv(output_file, index=False)

# Display results
print("\n--- Apple vs SPY Earnings Comparison ---")

print(summary.to_string(index=False))

print("\n--- Average Performance Across Four Quarters ---")

print(
    summary[
        [
            "aapl_t1_return_pct",
            "spy_t1_return_pct",
            "relative_t1_pp",
            "aapl_t3_return_pct",
            "spy_t3_return_pct",
            "relative_t3_pp"
        ]
    ].mean().round(2)
)

print(f"\nSummary saved to: {output_file}")
