import csv
import os
import statistics

REPORT_FILE = "reports/logs/performance_report.csv"


# -----------------------------
# GENERIC CSV LOADER
# -----------------------------
def _load_column(column: str):
    if not os.path.exists(REPORT_FILE):
        return []

    values = []

    with open(REPORT_FILE, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                values.append(float(row[column]))
            except (KeyError, ValueError):
                continue

    return values


# -----------------------------
# HISTORY (AVG)
# -----------------------------
def get_average_history():
    return _load_column("avg_ms")


# -----------------------------
# HISTORY (P95)
# -----------------------------
def get_p95_history():
    return _load_column("p95_ms")


# -----------------------------
# BASELINE (median of averages)
# -----------------------------
def get_baseline():
    history = get_average_history()

    if len(history) < 3:
        return None

    return statistics.median(history)


# -----------------------------
# TREND ANALYSIS
# -----------------------------
def get_trend():
    history = get_average_history()

    if len(history) < 2:
        return "INSUFFICIENT_DATA"

    if history[-1] > history[-2]:
        return "DEGRADING"

    if history[-1] < history[-2]:
        return "IMPROVING"

    return "UNCHANGED"


# -----------------------------
# AVG REGRESSION DETECTION
# -----------------------------
def detect_regression(current_value: float, threshold: float = 0.15):
    history = get_average_history()

    if len(history) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "baseline": None,
            "allowed_max": None,
        }

    baseline = statistics.median(history)
    allowed_max = baseline * (1 + threshold)

    if current_value > allowed_max:
        return {
            "status": "REGRESSION",
            "baseline": baseline,
            "allowed_max": allowed_max,
        }

    return {
        "status": "OK",
        "baseline": baseline,
        "allowed_max": allowed_max,
    }


# -----------------------------
# P95 REGRESSION DETECTION
# -----------------------------
def detect_p95_regression(current_p95: float, threshold: float = 0.15):
    history = get_p95_history()

    if len(history) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "baseline": None,
            "allowed_max": None,
        }

    baseline = statistics.median(history)
    allowed_max = baseline * (1 + threshold)

    if current_p95 > allowed_max:
        return {
            "status": "REGRESSION",
            "baseline": baseline,
            "allowed_max": allowed_max,
        }

    return {
        "status": "OK",
        "baseline": baseline,
        "allowed_max": allowed_max,
    }