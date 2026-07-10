import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
WORK_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "012_data_quality_work_queue.sql"

QUERY_BASELINE_SCRIPT = REPO_ROOT / "scripts" / "validate_query_performance_baseline.sql"
QUERY_TUNING_SCRIPT = REPO_ROOT / "scripts" / "validate_query_performance_tuning_comparison.sql"
QUEUE_METRICS_SCRIPT = REPO_ROOT / "scripts" / "validate_queue_performance_metrics_baseline.sql"
API_BASELINE_SCRIPT = REPO_ROOT / "scripts" / "validate_api_endpoint_performance_baseline.py"


@dataclass
class HealthCheckResult:
    name: str
    status: str
    evidence: list[str]
    missing_evidence: list[str]


def run_command(
    command: list[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
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


def api_service_is_available() -> bool:
    result = run_command(["curl.exe", "http://localhost:8000/health"])

    return result.returncode == 0 and '"status":"UP"' in result.stdout


def run_sql_script(script_path: Path) -> subprocess.CompletedProcess[str]:
    if not script_path.exists():
        raise FileNotFoundError(f"SQL script not found: {script_path}")

    return run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-x",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ],
        input_text=script_path.read_text(encoding="utf-8"),
    )


def apply_sql_schema(schema_path: Path) -> None:
    result = run_sql_script(schema_path)

    if result.returncode != 0:
        raise RuntimeError(
            f"Schema application failed for {schema_path}:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def run_python_script(script_path: Path) -> subprocess.CompletedProcess[str]:
    if not script_path.exists():
        raise FileNotFoundError(f"Python script not found: {script_path}")

    return run_command([sys.executable, str(script_path)])


def evaluate_result(name: str, output: str, required_markers: list[str]) -> HealthCheckResult:
    missing_markers = [marker for marker in required_markers if marker not in output]
    status = "passed" if not missing_markers else "failed"

    evidence = [marker for marker in required_markers if marker in output]

    return HealthCheckResult(
        name=name,
        status=status,
        evidence=evidence,
        missing_evidence=missing_markers,
    )


def print_health_result(result: HealthCheckResult) -> None:
    print(f"{result.name}_status | {result.status}")

    for marker in result.evidence:
        print(f"{result.name}_evidence | {marker}")

    for marker in result.missing_evidence:
        print(f"{result.name}_missing_evidence | {marker}")


def main() -> int:
    print("RELIABILITY_HEALTH_SUMMARY_START")

    if not docker_is_available():
        print("environment_status | failed")
        print("environment_missing_dependency | docker")
        return 1

    if not postgres_service_is_available():
        print("environment_status | failed")
        print("environment_missing_service | postgres")
        return 1

    if not api_service_is_available():
        print("environment_status | failed")
        print("environment_missing_service | api")
        return 1

    print("environment_status | passed")
    print("postgres_service_status | available")
    print("api_service_status | available")

    print("Applying required database schemas...")
    apply_sql_schema(REVIEW_QUEUE_SCHEMA)
    apply_sql_schema(WORK_QUEUE_SCHEMA)

    print("Running query performance baseline validation...")
    query_baseline_result = run_sql_script(QUERY_BASELINE_SCRIPT)

    print("Running query performance tuning comparison validation...")
    query_tuning_result = run_sql_script(QUERY_TUNING_SCRIPT)

    print("Running API endpoint performance baseline validation...")
    api_baseline_result = run_python_script(API_BASELINE_SCRIPT)

    print("Running queue performance metrics baseline validation...")
    queue_metrics_result = run_sql_script(QUEUE_METRICS_SCRIPT)

    if query_baseline_result.returncode != 0:
        print("query_performance_baseline_process_status | failed")
        print(query_baseline_result.stderr)
        return 1

    if query_tuning_result.returncode != 0:
        print("query_performance_tuning_process_status | failed")
        print(query_tuning_result.stderr)
        return 1

    if api_baseline_result.returncode != 0:
        print("api_endpoint_baseline_process_status | failed")
        print(api_baseline_result.stderr)
        return 1

    if queue_metrics_result.returncode != 0:
        print("queue_metrics_baseline_process_status | failed")
        print(queue_metrics_result.stderr)
        return 1

    health_checks = [
        evaluate_result(
            "query_performance_baseline",
            query_baseline_result.stdout,
            [
                "baseline_row_count_assertion | passed",
                "queue_linkage_assertion | passed",
                "queue_status_distribution_assertion | passed",
                "no_tuning_applied_assertion | passed",
                "ROLLBACK",
            ],
        ),
        evaluate_result(
            "query_performance_tuning",
            query_tuning_result.stdout,
            [
                "tuning_result_row_count_assertion | passed",
                "tuning_target_dataset_assertion | passed",
                "tuning_queue_linkage_assertion | passed",
                "tuning_index_created_assertion | passed",
                "pre_post_report_ready_assertion | passed",
                "ROLLBACK",
            ],
        ),
        evaluate_result(
            "api_endpoint_baseline",
            api_baseline_result.stdout,
            [
                "health_status_code_assertion | passed",
                "review_list_status_code_assertion | passed",
                "review_list_payload_assertion | passed",
                "performance_metrics_captured_assertion | passed",
                "API_ENDPOINT_PERFORMANCE_BASELINE_COMPLETE",
            ],
        ),
        evaluate_result(
            "queue_performance_metrics",
            queue_metrics_result.stdout,
            [
                "queue_total_count_assertion | passed",
                "queue_status_distribution_assertion | passed",
                "queue_retry_pressure_assertion | passed",
                "queue_dead_letter_assertion | passed",
                "queue_age_metrics_assertion | passed",
                "queue_processing_age_metrics_assertion | passed",
                "queue_history_metrics_assertion | passed",
                "ROLLBACK",
            ],
        ),
    ]

    print("RELIABILITY HEALTH SUMMARY")
    print("summary_scope | synthetic healthcare-style validation only")
    print("summary_safety | rollback-safe validation data")
    print("summary_threshold_policy | no hard local latency threshold enforced")
    print("summary_layer_coverage | database_query, database_tuning, api_endpoint, queue_health")

    for health_check in health_checks:
        print_health_result(health_check)

    failed_checks = [health_check for health_check in health_checks if health_check.status != "passed"]

    if failed_checks:
        print("overall_reliability_health_summary_status | failed")
        print("RELIABILITY_HEALTH_SUMMARY_COMPLETE")
        return 1

    print("overall_reliability_health_summary_status | passed")
    print("RELIABILITY_HEALTH_SUMMARY_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())