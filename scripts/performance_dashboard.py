import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


REPORT_FILE = "reports/logs/performance_report.csv"
OUTPUT_FILE = "reports/dashboard/performance_dashboard.png"


def build_dashboard():

    csv_file = Path(REPORT_FILE)

    if not csv_file.exists():
        print("No performance report found.")
        return

    df = pd.read_csv(csv_file)

    if len(df) == 0:
        print("No data available.")
        return

    plt.figure(figsize=(12, 6))

    plt.plot(
        df.index,
        df["avg_ms"],
        marker="o",
        label="Average Latency"
    )

    plt.title("Performance Trend Dashboard")

    plt.xlabel("Test Run")

    plt.ylabel("Latency (ms)")

    plt.grid(True)

    plt.legend()

    plt.tight_layout()

    plt.savefig(OUTPUT_FILE)

    print(f"Dashboard created: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_dashboard()