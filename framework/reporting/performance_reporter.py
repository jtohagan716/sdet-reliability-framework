import csv
import json
import os
from datetime import datetime


REPORT_DIR = "reports/logs"
CSV_REPORT_FILE = os.path.join(REPORT_DIR, "performance_report.csv")


REPORT_FIELDS = [
    "url",
    "iterations",

    "min_ms",
    "max_ms",
    "avg_ms",
    "stdev_ms",

    "p50_ms",
    "p95_ms",
    "p99_ms",

    "regression",
    "baseline",
    "allowed_max",

    "p95_regression",
    "trend",

    "reliability_score",
    "verdict",
    "score_breakdown",

    "risk_level",
    "risk_points",

    "status",

    "release_decision",
    "release_reason",
]


def _ensure_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)


def _normalize_value(value):
    """
    Converts complex values into CSV-safe strings.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value)

    return value


def _build_csv_row(result: dict) -> dict:
    """
    Builds a stable CSV row based on the reporting contract.

    Missing fields are written as blank.
    Extra fields are ignored.
    """
    row = {}

    for field in REPORT_FIELDS:
        row[field] = _normalize_value(result.get(field, ""))

    return row


def write_csv_report(result: dict):
    _ensure_dir()

    file_exists = os.path.isfile(CSV_REPORT_FILE)

    with open(CSV_REPORT_FILE, mode="a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=REPORT_FIELDS,
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(_build_csv_row(result))


def write_json_report(result: dict):
    _ensure_dir()

    file_path = os.path.join(
        REPORT_DIR,
        f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )

    with open(file_path, "w") as f:
        json.dump(result, f, indent=2)