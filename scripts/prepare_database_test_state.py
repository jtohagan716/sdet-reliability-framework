from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
import requests


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIRECTORY = REPOSITORY_ROOT / "reports" / "test-runs"

DEFAULT_DATABASE_URL = (
    "postgresql://sdet_user:sdet_password@"
    "localhost:5432/sdet_reliability"
)

DEFAULT_API_BASE_URL = "http://localhost:8000"


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_timestamp() -> str:
    return utc_now().isoformat()


def run_command(
    command: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def wait_for_postgres(timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""

    while time.monotonic() < deadline:
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
            ],
            check=False,
        )

        if result.returncode == 0:
            return

        last_error = result.stderr.strip() or result.stdout.strip()
        time.sleep(1)

    raise RuntimeError(
        "PostgreSQL did not become ready within "
        f"{timeout_seconds} seconds. Last response: {last_error}"
    )


def wait_for_api(
    api_base_url: str,
    timeout_seconds: int,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""

    while time.monotonic() < deadline:
        try:
            response = requests.get(
                f"{api_base_url}/health",
                timeout=(2, 5),
            )

            if response.status_code == 200:
                return

            last_error = (
                f"HTTP {response.status_code}: {response.text}"
            )

        except requests.RequestException as exc:
            last_error = str(exc)

        time.sleep(1)

    raise RuntimeError(
        "API did not become ready within "
        f"{timeout_seconds} seconds. Last response: {last_error}"
    )


def restart_for_cold_run(
    api_base_url: str,
    readiness_timeout_seconds: int,
) -> None:
    print("Restarting PostgreSQL...")
    run_command(["docker", "compose", "restart", "postgres"])
    wait_for_postgres(readiness_timeout_seconds)

    print("Restarting API...")
    run_command(["docker", "compose", "restart", "api"])
    wait_for_api(api_base_url, readiness_timeout_seconds)


def get_git_state() -> dict[str, Any]:
    branch = run_command(
        ["git", "branch", "--show-current"]
    ).stdout.strip()

    commit = run_command(
        ["git", "rev-parse", "HEAD"]
    ).stdout.strip()

    short_commit = run_command(
        ["git", "rev-parse", "--short", "HEAD"]
    ).stdout.strip()

    status_lines = [
        line
        for line in run_command(
            ["git", "status", "--porcelain"]
        ).stdout.splitlines()
        if line.strip()
    ]

    return {
        "branch": branch,
        "commit": commit,
        "short_commit": short_commit,
        "working_tree_clean": not status_lines,
        "working_tree_changes": status_lines,
    }


def verify_database_state(
    database_url: str,
) -> dict[str, Any]:
    with psycopg.connect(
        database_url,
        application_name="database-study-preflight",
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM patients
                WHERE patient_id = 1001
                """
            )
            patient_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT
                    state,
                    COUNT(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid <> pg_backend_pid()
                  AND application_name
                      <> 'database-study-preflight'
                GROUP BY state
                ORDER BY state
                """
            )
            state_counts = {
                str(state): int(count)
                for state, count in cursor.fetchall()
            }

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid <> pg_backend_pid()
                  AND state LIKE 'idle in transaction%'
                """
            )
            idle_in_transaction_count = cursor.fetchone()[0]

    if patient_count != 1:
        raise RuntimeError(
            "Expected exactly one patient record with "
            f"patient_id=1001, found {patient_count}"
        )

    if idle_in_transaction_count != 0:
        raise RuntimeError(
            "Starting state is invalid: "
            f"{idle_in_transaction_count} PostgreSQL session(s) "
            "are idle in transaction"
        )

    return {
        "patient_1001_count": int(patient_count),
        "session_state_counts": state_counts,
        "idle_in_transaction_count": int(
            idle_in_transaction_count
        ),
    }


def identify_connection_strategy(
    api_base_url: str,
) -> dict[str, Any]:
    response = requests.get(
        (
            f"{api_base_url}/qa/database-connection-timing"
            "?patient_id=1001"
        ),
        timeout=(3, 10),
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Could not identify the database connection strategy. "
            f"Diagnostic endpoint returned HTTP "
            f"{response.status_code}: {response.text}"
        )

    payload = response.json()

    return {
        "connection_strategy": payload.get(
            "connection_strategy",
            "unknown",
        ),
        "sample_database_phases": payload.get(
            "database_phases",
            {},
        ),
    }


def run_warmup(
    api_base_url: str,
    warmup_count: int,
) -> dict[str, Any]:
    if warmup_count == 0:
        return {
            "request_count": 0,
            "success_count": 0,
            "minimum_ms": None,
            "mean_ms": None,
            "maximum_ms": None,
        }

    latencies_ms: list[float] = []

    with requests.Session() as session:
        for request_number in range(1, warmup_count + 1):
            started = time.perf_counter()

            response = session.get(
                f"{api_base_url}/patients/1001",
                headers={
                    "X-Request-ID": (
                        "database-study-warmup-"
                        f"{request_number:04d}"
                    )
                },
                timeout=(3, 10),
            )

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            if response.status_code != 200:
                raise RuntimeError(
                    "Warm-up request failed: "
                    f"HTTP {response.status_code}: {response.text}"
                )

            latencies_ms.append(elapsed_ms)

    return {
        "request_count": warmup_count,
        "success_count": len(latencies_ms),
        "minimum_ms": round(min(latencies_ms), 3),
        "mean_ms": round(
            sum(latencies_ms) / len(latencies_ms),
            3,
        ),
        "maximum_ms": round(max(latencies_ms), 3),
    }


def capture_runtime_state() -> dict[str, Any]:
    compose_state = run_command(
        ["docker", "compose", "ps"],
        check=False,
    )

    docker_stats = run_command(
        [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            (
                "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|"
                "{{.NetIO}}|{{.BlockIO}}|{{.PIDs}}"
            ),
        ],
        check=False,
    )

    return {
        "docker_compose_ps": compose_state.stdout.splitlines(),
        "docker_stats": docker_stats.stdout.splitlines(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and record a deterministic starting state "
            "for a database connection study run."
        )
    )

    parser.add_argument(
        "--mode",
        choices=["warm", "cold"],
        required=True,
    )

    parser.add_argument(
        "--warmup-count",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--stabilization-seconds",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--readiness-timeout-seconds",
        type=int,
        default=60,
    )

    parser.add_argument(
        "--require-clean-git",
        action="store_true",
    )

    arguments = parser.parse_args()

    if arguments.warmup_count < 0:
        raise ValueError("--warmup-count cannot be negative")

    if arguments.mode == "cold" and arguments.warmup_count != 0:
        raise ValueError(
            "Cold mode must use --warmup-count 0 so database "
            "first-use behavior remains un-warmed"
        )

    api_base_url = os.getenv(
        "SDET_API_BASE_URL",
        DEFAULT_API_BASE_URL,
    )

    database_url = os.getenv(
        "DATABASE_URL",
        DEFAULT_DATABASE_URL,
    )

    run_started_at = utc_timestamp()

    run_id = utc_now().strftime(
        f"database-state-{arguments.mode}-%Y%m%dT%H%M%S%fZ"
    )

    run_directory = REPORTS_DIRECTORY / run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    print()
    print("DATABASE TEST STARTING-STATE PREPARATION")
    print("----------------------------------------")
    print("Run ID:", run_id)
    print("Mode:", arguments.mode)

    git_state = get_git_state()

    if (
        arguments.require_clean_git
        and not git_state["working_tree_clean"]
    ):
        raise RuntimeError(
            "Git working tree is not clean:\n"
            + "\n".join(git_state["working_tree_changes"])
        )

    if arguments.mode == "cold":
        restart_for_cold_run(
            api_base_url,
            arguments.readiness_timeout_seconds,
        )
    else:
        wait_for_postgres(
            arguments.readiness_timeout_seconds
        )
        wait_for_api(
            api_base_url,
            arguments.readiness_timeout_seconds,
        )

    database_state_before_warmup = verify_database_state(
        database_url
    )

    strategy_state = identify_connection_strategy(
        api_base_url
    )

    warmup_result = run_warmup(
        api_base_url,
        arguments.warmup_count,
    )

    if arguments.stabilization_seconds > 0:
        print(
            "Stabilizing for",
            arguments.stabilization_seconds,
            "seconds...",
        )
        time.sleep(arguments.stabilization_seconds)

    database_state_after_warmup = verify_database_state(
        database_url
    )

    runtime_state = capture_runtime_state()

    manifest = {
        "run_id": run_id,
        "preparation_started_at_utc": run_started_at,
        "preparation_completed_at_utc": utc_timestamp(),
        "mode": arguments.mode,
        "api_base_url": api_base_url,
        "warmup_count": arguments.warmup_count,
        "stabilization_seconds": (
            arguments.stabilization_seconds
        ),
        "git": git_state,
        "strategy": strategy_state,
        "database_before_warmup": (
            database_state_before_warmup
        ),
        "warmup": warmup_result,
        "database_after_warmup": (
            database_state_after_warmup
        ),
        "runtime": runtime_state,
        "starting_state_valid": True,
    }

    manifest_path = run_directory / "starting-state.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    latest_path = (
        REPORTS_DIRECTORY / "latest-starting-state-run.txt"
    )

    latest_path.write_text(
        run_id,
        encoding="utf-8",
    )

    print()
    print("STARTING STATE VALID")
    print("--------------------")
    print(
        "Git:",
        git_state["short_commit"],
        git_state["branch"],
    )
    print(
        "Connection strategy:",
        strategy_state["connection_strategy"],
    )
    print(
        "Idle in transaction:",
        database_state_after_warmup[
            "idle_in_transaction_count"
        ],
    )
    print(
        "Warm-up successes:",
        warmup_result["success_count"],
    )
    print("Manifest:", manifest_path)


if __name__ == "__main__":
    main()
