import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os


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

    os.makedirs("reports/dashboard", exist_ok=True)

    # Convert risk levels to numeric values
    risk_mapping = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3
    }

    if "risk_level" in df.columns:
        df["risk_numeric"] = df["risk_level"].map(risk_mapping)

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    # -------------------------------------------------
    # Average Latency
    # -------------------------------------------------

    axs[0, 0].plot(
        df.index,
        df["avg_ms"],
        marker="o"
    )

    axs[0, 0].set_title("Average Latency")
    axs[0, 0].set_ylabel("Milliseconds")
    axs[0, 0].grid(True)

    # -------------------------------------------------
    # P95 Latency
    # -------------------------------------------------

    if "p95_ms" in df.columns:

        axs[0, 1].plot(
            df.index,
            df["p95_ms"],
            marker="o"
        )

        axs[0, 1].set_title("P95 Latency")
        axs[0, 1].set_ylabel("Milliseconds")
        axs[0, 1].grid(True)

    # -------------------------------------------------
    # Reliability Score
    # -------------------------------------------------

    if "reliability_score" in df.columns:

        axs[1, 0].plot(
            df.index,
            df["reliability_score"],
            marker="o"
        )

        axs[1, 0].set_title("Reliability Score")
        axs[1, 0].set_ylabel("Score")
        axs[1, 0].grid(True)

    # -------------------------------------------------
    # Risk Trend
    # -------------------------------------------------

    if "risk_numeric" in df.columns:

        axs[1, 1].plot(
            df.index,
            df["risk_numeric"],
            marker="o"
        )

        axs[1, 1].set_title("Release Risk Trend")
        axs[1, 1].set_ylabel("Risk")

        axs[1, 1].set_yticks([1, 2, 3])
        axs[1, 1].set_yticklabels(
            ["LOW", "MEDIUM", "HIGH"]
        )

        axs[1, 1].grid(True)

    plt.tight_layout()

    plt.savefig(OUTPUT_FILE)

    print(f"Dashboard created: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_dashboard()