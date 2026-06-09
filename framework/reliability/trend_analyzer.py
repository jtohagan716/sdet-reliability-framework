import csv
import os
import statistics

REPORT_FILE = "reports/logs/performance_report.csv"
WINDOW_SIZE = 5  # rolling baseline window


def get_average_history():
    if not os.path.exists(REPORT_FILE):
        return []

    history = []

    with open(REPORT_FILE, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                history.append(float(row["avg_ms"]))
            except (KeyError, ValueError):
                continue

    return history


def get_rolling_window():
    history = get_average_history()
    return history[-WINDOW_SIZE:]


def get_baseline():
    window = get_rolling_window()

    if len(window) < 3:
        return None

    return statistics.mean(window)


def get_volatility():
    window = get_rolling_window()

    if len(window) < 2:
        return 0.0

    mean = statistics.mean(window)
    stdev = statistics.stdev(window)

    if mean == 0:
        return 0.0

    return stdev / mean  # coefficient of variation


def detect_regression(current_value: float):
    baseline = get_baseline()
    volatility = get_volatility()

    if baseline is None:
        return {
            "status": "INSUFFICIENT_DATA",
            "baseline": None,
            "volatility": volatility
        }

    # adaptive threshold (this is key upgrade)
    threshold = 0.2 + volatility

    allowed_max = baseline * (1 + threshold)

    if current_value > allowed_max:
        if current_value > baseline * 1.5:
            status = "SEVERE_REGRESSION"
        else:
            status = "REGRESSION"
    else:
        status = "OK"

    return {
        "status": status,
        "baseline": round(baseline, 2),
        "current": current_value,
        "allowed_max": round(allowed_max, 2),
        "volatility": round(volatility, 3)
    }


def get_summary():
    history = get_rolling_window()

    if len(history) < 2:
        return {"trend": "INSUFFICIENT_DATA"}

    latest = history[-1]
    previous = history[-2]

    trend = "IMPROVING" if latest < previous else "DEGRADING" if latest > previous else "STABLE"

    return {
        "trend": trend,
        "latest_ms": latest,
        "previous_ms": previous,
        "volatility": get_volatility()
    }