
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load event-study summary
input_path = Path("data/processed/aapl_event_study_summary.csv")

df = pd.read_csv(input_path)

# Create output directory
output_path = Path("reports/figures/aapl_event_study.png")
output_path.parent.mkdir(parents=True, exist_ok=True)

# Create figure
fig, ax = plt.subplots(figsize=(11, 6))

# Plot average normalized price
ax.plot(
    df["event_time"],
    df["mean_normalized_price"],
    marker="o",
    linewidth=2,
    markersize=7,
    label="Average normalized price"
)

# Reference lines
ax.axhline(
    y=100,
    linestyle=":",
    linewidth=1,
    label="Baseline (100)"
)

ax.axvline(
    x=0,
    linestyle="--",
    linewidth=1,
    label="Earnings announcement"
)

# Titles and labels
ax.set_title(
    "AAPL Stock Price Performance Around Earnings",
    fontsize=14,
    fontweight="bold"
)

ax.set_xlabel("Trading Sessions Relative to Earnings")
ax.set_ylabel("Normalized Stock Price (Baseline = 100)")

ax.set_xticks(range(-5, 6))
ax.grid(axis="y", alpha=0.3)

ax.legend()
fig.tight_layout()

# Save figure
fig.savefig(output_path, dpi=300, bbox_inches="tight")

plt.show()

print(f"Chart saved to: {output_path}")
