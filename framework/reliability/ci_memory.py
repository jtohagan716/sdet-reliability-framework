import json
import os
from datetime import datetime

MEMORY_FILE = "reports/ci_memory.json"


def load_history():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_run(record: dict):
    history = load_history()

    record["timestamp"] = datetime.utcnow().isoformat()

    history.append(record)

    # keep last 50 runs only (avoid noise + file bloat)
    history = history[-50:]

    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_recent_baseline(window: int = 5):
    history = load_history()

    if len(history) < window:
        return None

    recent = history[-window:]

    scores = [r.get("reliability_score", 0) for r in recent]

    return sum(scores) / len(scores)


def detect_ci_trend(current_score: float, window: int = 5):
    baseline = get_recent_baseline(window)

    if baseline is None:
        return {
            "trend": "INSUFFICIENT_DATA",
            "baseline": None
        }

    if current_score < baseline - 5:
        return {
            "trend": "DEGRADING",
            "baseline": baseline
        }

    if current_score > baseline + 5:
        return {
            "trend": "IMPROVING",
            "baseline": baseline
        }

    return {
        "trend": "STABLE",
        "baseline": baseline
    }