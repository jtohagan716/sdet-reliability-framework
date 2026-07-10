import json
import math
import shutil
import subprocess
import time
from pathlib import Path
from statistics import mean, median

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://localhost:8000"
SAMPLE_SIZE = 20
WARMUP_REQUESTS = 3

REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"

SEED_PREFIX = "dq-api-perf-baseline-review-"


def run_command(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


def docker_is_available() -> bool:
    return shutil.which("docker") is not None


def postgres_service_is_available() -> bool:
    result = run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "pg_isready",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ]
    )

    return result.returncode == 0


def run_sql(sql: str) -> None:
    result = run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ],
        input_text=sql,
    )

    if result.returncode != 0:
        raise RuntimeError(f"SQL failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def apply_schema() -> None:
    if not REVIEW_QUEUE_SCHEMA.exists():
        raise FileNotFoundError(f"Schema not found: {REVIEW_QUEUE_SCHEMA}")

    run_sql(REVIEW_QUEUE_SCHEMA.read_text(encoding="utf-8"))


def cleanup_seed_data() -> None:
    cleanup_sql = f"""
DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key LIKE '{SEED_PREFIX}%'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key LIKE '{SEED_PREFIX}%';
"""
    run_sql(cleanup_sql)


def seed_review_items() -> None:
    seed_sql = f"""
INSERT INTO patient_data_quality_review_items (
    review_item_key,
    review_source,
    patient_reference,
    encounter_reference,
    related_event_id,
    review_reason,
    risk_summary,
    review_priority,
    review_status,
    assigned_role,
    assigned_to,
    details,
    created_at
)
SELECT
    '{SEED_PREFIX}' || LPAD(series_id::text, 3, '0') AS review_item_key,
    'api_performance_baseline',
    'Patient/api-performance-baseline-patient-' || LPAD(series_id::text, 3, '0') AS patient_reference,
    'Encounter/api-performance-baseline-encounter-' || LPAD(series_id::text, 3, '0') AS encounter_reference,
    'api-performance-baseline-event-' || LPAD(series_id::text, 3, '0') AS related_event_id,
    'API endpoint performance baseline review item',
    'Synthetic review item used to measure API endpoint response behavior',
    CASE
        WHEN series_id <= 25 THEN 'high'
        WHEN series_id <= 75 THEN 'medium'
        ELSE 'low'
    END AS review_priority,
    CASE
        WHEN series_id <= 80 THEN 'pending_review'
        ELSE 'closed'
    END AS review_status,
    'Data Quality Expert',
    'synthetic_api_performance_reviewer',
    jsonb_build_object(
        'api_performance_baseline', true,
        'series_id', series_id,
        'synthetic_validation', true
    ),
    NOW() - ((100 - series_id) * INTERVAL '1 second') AS created_at
FROM generate_series(1, 100) AS series_id;
"""
    run_sql(seed_sql)


def ensure_api_is_available() -> None:
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.RequestException as exc:
        raise RuntimeError(f"API is not reachable at {BASE_URL}: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"API health check failed with status {response.status_code}: {response.text}")


def timed_get(path: str) -> dict:
    start_time = time.perf_counter()
    response = requests.get(f"{BASE_URL}{path}", timeout=10)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "path": path,
        "status_code": response.status_code,
        "elapsed_ms": elapsed_ms,
        "payload_bytes": len(response.content),
        "text": response.text,
    }


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("Cannot calculate percentile for empty value list.")

    sorted_values = sorted(values)
    index = math.ceil((percentile_value / 100) * len(sorted_values)) - 1
    index = max(0, min(index, len(sorted_values) - 1))
    return sorted_values[index]


def summarize(endpoint_name: str, measurements: list[dict]) -> dict:
    elapsed_values = [measurement["elapsed_ms"] for measurement in measurements]
    payload_sizes = [measurement["payload_bytes"] for measurement in measurements]
    status_codes = sorted({measurement["status_code"] for measurement in measurements})

    return {
        "endpoint": endpoint_name,
        "request_count": len(measurements),
        "status_codes": status_codes,
        "min_ms": min(elapsed_values),
        "max_ms": max(elapsed_values),
        "mean_ms": mean(elapsed_values),
        "median_ms": median(elapsed_values),
        "p95_ms": percentile(elapsed_values, 95),
        "payload_bytes_min": min(payload_sizes),
        "payload_bytes_max": max(payload_sizes),
    }


def print_summary(summary: dict) -> None:
    endpoint = summary["endpoint"]

    print(f"{endpoint}_request_count | {summary['request_count']}")
    print(f"{endpoint}_status_codes | {summary['status_codes']}")
    print(f"{endpoint}_latency_ms_min | {summary['min_ms']:.3f}")
    print(f"{endpoint}_latency_ms_mean | {summary['mean_ms']:.3f}")
    print(f"{endpoint}_latency_ms_median | {summary['median_ms']:.3f}")
    print(f"{endpoint}_latency_ms_p95 | {summary['p95_ms']:.3f}")
    print(f"{endpoint}_latency_ms_max | {summary['max_ms']:.3f}")
    print(f"{endpoint}_payload_bytes_min | {summary['payload_bytes_min']}")
    print(f"{endpoint}_payload_bytes_max | {summary['payload_bytes_max']}")


def main() -> int:
    print("API_ENDPOINT_PERFORMANCE_BASELINE_START")

    if not docker_is_available():
        raise RuntimeError("Docker is not available.")

    if not postgres_service_is_available():
        raise RuntimeError("PostgreSQL Docker service is not available.")

    apply_schema()

    try:
        cleanup_seed_data()
        seed_review_items()
        ensure_api_is_available()

        print("Seeded synthetic API performance baseline review items.")
        print("Warm-up requests starting...")

        for _ in range(WARMUP_REQUESTS):
            timed_get("/health")
            timed_get("/qa/data-quality-review-items")

        print("Warm-up requests complete.")
        print("Collecting API endpoint performance samples...")

        health_measurements = [timed_get("/health") for _ in range(SAMPLE_SIZE)]
        review_list_measurements = [
            timed_get("/qa/data-quality-review-items") for _ in range(SAMPLE_SIZE)
        ]

        health_summary = summarize("health_endpoint", health_measurements)
        review_summary = summarize("review_list_endpoint", review_list_measurements)

        print("API endpoint performance summary:")
        print_summary(health_summary)
        print_summary(review_summary)

        review_response_text = review_list_measurements[-1]["text"]

        health_status_assertion = (
            "passed"
            if all(item["status_code"] == 200 for item in health_measurements)
            else "failed"
        )

        review_list_status_assertion = (
            "passed"
            if all(item["status_code"] == 200 for item in review_list_measurements)
            else "failed"
        )

        review_payload_assertion = (
            "passed"
            if SEED_PREFIX in review_response_text
            else "failed"
        )

        metrics_captured_assertion = (
            "passed"
            if health_summary["request_count"] == SAMPLE_SIZE
            and review_summary["request_count"] == SAMPLE_SIZE
            and health_summary["p95_ms"] >= 0
            and review_summary["p95_ms"] >= 0
            else "failed"
        )

        print(f"health_status_code_assertion | {health_status_assertion}")
        print(f"review_list_status_code_assertion | {review_list_status_assertion}")
        print(f"review_list_payload_assertion | {review_payload_assertion}")
        print(f"performance_metrics_captured_assertion | {metrics_captured_assertion}")

        print(
            "performance_threshold_note | "
            "No hard latency threshold is enforced in this baseline. "
            "This script captures repeatable local API timing evidence for future comparison."
        )

        if "failed" in {
            health_status_assertion,
            review_list_status_assertion,
            review_payload_assertion,
            metrics_captured_assertion,
        }:
            return 1

        return 0

    finally:
        cleanup_seed_data()
        print("Cleaned up synthetic API performance baseline review items.")
        print("API_ENDPOINT_PERFORMANCE_BASELINE_COMPLETE")


if __name__ == "__main__":
    raise SystemExit(main())