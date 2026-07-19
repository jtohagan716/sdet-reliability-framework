from __future__ import annotations

import csv
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPORTS_DIRECTORY = Path("reports")
LATEST_RUN_PATH = REPORTS_DIRECTORY / "latest_correlated_run_id.txt"

LOG_TIMESTAMP_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} "
    r"\d{2}:\d{2}:\d{2},\d{3})"
)

REQUEST_ID_PATTERN = re.compile(
    r"request_id=(?P<request_id>[^\s]+)"
)

DURATION_PATTERN = re.compile(
    r"duration_ms=(?P<duration_ms>[0-9.]+)"
)


def parse_client_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def parse_server_timestamp(line: str) -> datetime | None:
    match = LOG_TIMESTAMP_PATTERN.search(line)

    if not match:
        return None

    parsed = datetime.strptime(
        match.group("timestamp"),
        "%Y-%m-%d %H:%M:%S,%f",
    )

    return parsed.replace(tzinfo=UTC)


def milliseconds_between(
    later: datetime | None,
    earlier: datetime | None,
) -> float | None:
    if later is None or earlier is None:
        return None

    return round((later - earlier).total_seconds() * 1000, 3)


def percentile(
    values: list[float],
    percent: int,
) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    rank = math.ceil((percent / 100) * len(ordered))
    index = max(0, min(len(ordered) - 1, rank - 1))

    return round(ordered[index], 3)


def metric_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "minimum_ms": None,
            "mean_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "maximum_ms": None,
        }

    return {
        "count": len(values),
        "minimum_ms": round(min(values), 3),
        "mean_ms": round(sum(values) / len(values), 3),
        "p50_ms": percentile(values, 50),
        "p95_ms": percentile(values, 95),
        "p99_ms": percentile(values, 99),
        "maximum_ms": round(max(values), 3),
    }


run_id = LATEST_RUN_PATH.read_text(encoding="utf-8").strip()

client_csv_path = REPORTS_DIRECTORY / f"{run_id}-client.csv"
api_log_path = REPORTS_DIRECTORY / f"{run_id}-api.log"

output_csv_path = REPORTS_DIRECTORY / f"{run_id}-correlated.csv"
output_summary_path = REPORTS_DIRECTORY / f"{run_id}-correlation-summary.json"

server_events: dict[str, dict[str, Any]] = {}

for line in api_log_path.read_text(
    encoding="utf-8",
    errors="replace",
).splitlines():
    request_id_match = REQUEST_ID_PATTERN.search(line)

    if not request_id_match:
        continue

    request_id = request_id_match.group("request_id")

    if not request_id.startswith(run_id):
        continue

    timestamp = parse_server_timestamp(line)

    if timestamp is None:
        continue

    event = server_events.setdefault(request_id, {})

    if "message=request_start" in line:
        event["server_started_at"] = timestamp

    elif "message=request_complete" in line:
        event["server_completed_at"] = timestamp

        duration_match = DURATION_PATTERN.search(line)

        if duration_match:
            event["server_duration_ms"] = float(
                duration_match.group("duration_ms")
            )


correlated_rows: list[dict[str, Any]] = []

with client_csv_path.open(
    "r",
    newline="",
    encoding="utf-8",
) as client_file:
    reader = csv.DictReader(client_file)

    for client_row in reader:
        request_id = client_row["request_id"]
        server_event = server_events.get(request_id, {})

        client_started_at = parse_client_timestamp(
            client_row["client_started_at_utc"]
        )

        client_finished_at = parse_client_timestamp(
            client_row["client_finished_at_utc"]
        )

        server_started_at = server_event.get("server_started_at")
        server_completed_at = server_event.get("server_completed_at")

        pre_server_ms = milliseconds_between(
            server_started_at,
            client_started_at,
        )

        server_timestamp_duration_ms = milliseconds_between(
            server_completed_at,
            server_started_at,
        )

        response_delivery_ms = milliseconds_between(
            client_finished_at,
            server_completed_at,
        )

        server_start_after_client_finish_ms = milliseconds_between(
            server_started_at,
            client_finished_at,
        )

        server_complete_after_client_finish_ms = milliseconds_between(
            server_completed_at,
            client_finished_at,
        )

        correlated_rows.append(
            {
                **client_row,
                "server_started_at_utc": (
                    server_started_at.isoformat()
                    if server_started_at
                    else ""
                ),
                "server_completed_at_utc": (
                    server_completed_at.isoformat()
                    if server_completed_at
                    else ""
                ),
                "pre_server_ms": (
                    pre_server_ms
                    if pre_server_ms is not None
                    else ""
                ),
                "server_logged_duration_ms": server_event.get(
                    "server_duration_ms",
                    "",
                ),
                "server_timestamp_duration_ms": (
                    server_timestamp_duration_ms
                    if server_timestamp_duration_ms is not None
                    else ""
                ),
                "response_delivery_ms": (
                    response_delivery_ms
                    if response_delivery_ms is not None
                    else ""
                ),
                "server_start_after_client_finish_ms": (
                    server_start_after_client_finish_ms
                    if (
                        server_start_after_client_finish_ms is not None
                        and server_start_after_client_finish_ms > 0
                    )
                    else ""
                ),
                "server_complete_after_client_finish_ms": (
                    server_complete_after_client_finish_ms
                    if (
                        server_complete_after_client_finish_ms is not None
                        and server_complete_after_client_finish_ms > 0
                    )
                    else ""
                ),
            }
        )


fieldnames = list(correlated_rows[0].keys())

with output_csv_path.open(
    "w",
    newline="",
    encoding="utf-8",
) as output_file:
    writer = csv.DictWriter(
        output_file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(correlated_rows)


matched_rows = [
    row
    for row in correlated_rows
    if row["server_started_at_utc"]
    and row["server_completed_at_utc"]
]

successful_rows = [
    row
    for row in matched_rows
    if row["outcome"] == "success"
]

timeout_rows = [
    row
    for row in matched_rows
    if row["outcome"] == "read_timeout"
]

pre_server_values = [
    float(row["pre_server_ms"])
    for row in matched_rows
    if row["pre_server_ms"] != ""
]

server_duration_values = [
    float(row["server_logged_duration_ms"])
    for row in matched_rows
    if row["server_logged_duration_ms"] != ""
]

successful_response_delivery_values = [
    float(row["response_delivery_ms"])
    for row in successful_rows
    if row["response_delivery_ms"] != ""
]

server_started_after_timeout = [
    row
    for row in timeout_rows
    if row["server_start_after_client_finish_ms"] != ""
]

server_completed_after_timeout = [
    row
    for row in timeout_rows
    if row["server_complete_after_client_finish_ms"] != ""
]


summary = {
    "run_id": run_id,
    "client_request_count": len(correlated_rows),
    "matched_client_server_count": len(matched_rows),
    "successful_request_count": len(successful_rows),
    "read_timeout_count": len(timeout_rows),
    "server_started_after_client_timeout_count": len(
        server_started_after_timeout
    ),
    "server_completed_after_client_timeout_count": len(
        server_completed_after_timeout
    ),
    "client_start_to_server_start": metric_summary(
        pre_server_values
    ),
    "server_request_duration": metric_summary(
        server_duration_values
    ),
    "server_complete_to_successful_client_finish": metric_summary(
        successful_response_delivery_values
    ),
}

output_summary_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8",
)

print()
print("CLIENT/SERVER CORRELATION SUMMARY")
print("---------------------------------")
print(json.dumps(summary, indent=2))

print()
print("TIMED-OUT REQUESTS")
print("------------------")

for row in timeout_rows:
    print(
        row["request_number"],
        row["request_id"],
        "pre_server_ms=",
        row["pre_server_ms"],
        "server_duration_ms=",
        row["server_logged_duration_ms"],
        "server_start_after_client_finish_ms=",
        row["server_start_after_client_finish_ms"],
        "server_complete_after_client_finish_ms=",
        row["server_complete_after_client_finish_ms"],
    )

print()
print("SLOWEST SUCCESSFUL CLIENT REQUESTS")
print("----------------------------------")

for row in sorted(
    successful_rows,
    key=lambda item: float(item["client_elapsed_ms"]),
    reverse=True,
)[:20]:
    print(
        row["request_number"],
        "client_elapsed_ms=",
        row["client_elapsed_ms"],
        "pre_server_ms=",
        row["pre_server_ms"],
        "server_duration_ms=",
        row["server_logged_duration_ms"],
        "response_delivery_ms=",
        row["response_delivery_ms"],
    )

print()
print("Correlated CSV:", output_csv_path)
print("Summary JSON:", output_summary_path)
