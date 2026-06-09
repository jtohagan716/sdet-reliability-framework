import csv
import json
import os
from datetime import datetime


REPORT_DIR = "reports/logs"


def _ensure_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)


def write_csv_report(result: dict):
    _ensure_dir()

    file_path = os.path.join(REPORT_DIR, "performance_report.csv")

    file_exists = os.path.isfile(file_path)

    with open(file_path, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=result.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)


def write_json_report(result: dict):
    _ensure_dir()

    file_path = os.path.join(
        REPORT_DIR,
        f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(file_path, "w") as f:
        json.dump(result, f, indent=2)