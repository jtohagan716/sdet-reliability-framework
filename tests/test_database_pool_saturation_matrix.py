import argparse
import json
from pathlib import Path

import pytest

import scripts.run_database_pool_saturation_matrix as matrix


class _CompletedProcess:
    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode


def _study_summary(connection_hold_ms: int) -> dict:
    return {
        "run_id": "study-run",
        "connection_hold_ms": connection_hold_ms,
        "concurrency": 4,
        "request_count": 8,
        "success_count": 8,
        "failure_count": 0,
        "requests_per_second": 25.0,
        "metrics": {
            "client_elapsed_ms": {
                "p50_ms": 110.0,
                "p95_ms": 120.0,
                "p99_ms": 125.0,
            },
            "acquire_ms": {
                "p50_ms": 0.1,
                "p95_ms": 0.2,
                "p99_ms": 0.3,
            },
            "total_ms": {
                "p95_ms": 105.0,
            },
        },
        "pool_observations": {
            "maximum_pool_size": 4,
            "minimum_available": 0,
            "maximum_requests_waiting": 0,
            (
                "highest_cumulative_requests_queued_"
                "since_api_start"
            ): 2,
        },
    }


def _recovery_state() -> dict:
    return {
        "pool_size": 4,
        "pool_available": 4,
        "requests_waiting": 0,
        "idle_in_transaction": 0,
        "recovered": True,
    }


def test_run_study_passes_connection_hold_to_runner(
    monkeypatch,
    tmp_path,
):
    evidence_directory = tmp_path / "study-evidence"
    evidence_directory.mkdir()

    summary_path = evidence_directory / "summary.json"
    summary_path.write_text(
        json.dumps(_study_summary(100)),
        encoding="utf-8",
    )

    observed_command = []

    def fake_run(command, **kwargs):
        observed_command.extend(command)
        return _CompletedProcess(
            "Evidence directory: "
            f"{evidence_directory}\n"
        )

    monkeypatch.setattr(matrix.subprocess, "run", fake_run)

    summary, returned_directory = matrix.run_study(
        concurrency=4,
        repetition=1,
        request_count=8,
        warmup_count=2,
        stabilization_seconds=0,
        connect_timeout_seconds=3,
        read_timeout_seconds=10,
        connection_hold_ms=100,
    )

    hold_index = observed_command.index(
        "--connection-hold-ms"
    )

    assert observed_command[hold_index + 1] == "100"
    assert (
        "saturation-h0100ms-c04-r01"
        in observed_command
    )
    assert summary["connection_hold_ms"] == 100
    assert returned_directory == evidence_directory


def test_run_study_rejects_connection_hold_mismatch(
    monkeypatch,
    tmp_path,
):
    evidence_directory = tmp_path / "study-evidence"
    evidence_directory.mkdir()

    (evidence_directory / "summary.json").write_text(
        json.dumps(_study_summary(50)),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        matrix.subprocess,
        "run",
        lambda *args, **kwargs: _CompletedProcess(
            "Evidence directory: "
            f"{evidence_directory}\n"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Study summary connection hold mismatch",
    ):
        matrix.run_study(
            concurrency=4,
            repetition=1,
            request_count=8,
            warmup_count=2,
            stabilization_seconds=0,
            connect_timeout_seconds=3,
            read_timeout_seconds=10,
            connection_hold_ms=100,
        )


def test_flatten_result_records_connection_hold():
    flattened = matrix.flatten_result(
        summary=_study_summary(100),
        evidence_directory=Path("evidence"),
        repetition=2,
        recovery=_recovery_state(),
    )

    assert flattened["connection_hold_ms"] == 100
    assert flattened["concurrency"] == 4
    assert flattened["repetition"] == 2
    assert flattened["recovered"] is True


def test_markdown_report_records_connection_hold(
    tmp_path,
):
    report_path = tmp_path / "report.md"

    matrix.write_markdown_report(
        matrix_run_id="matrix-run",
        connection_hold_ms=250,
        summaries=[
            {
                "concurrency": 4,
                "median_requests_per_second": 20.0,
                "median_client_p95_ms": 120.0,
                "median_acquire_p95_ms": 0.2,
                "median_database_total_p95_ms": 105.0,
                "maximum_requests_waiting": 0,
                "total_failures": 0,
                "all_runs_recovered": True,
            }
        ],
        path=report_path,
    )

    report = report_path.read_text(encoding="utf-8")

    assert "Connection hold: 250 ms" in report
    assert "Matrix run ID: `matrix-run`" in report


def test_parse_arguments_defaults_connection_hold_to_zero(
    monkeypatch,
):
    monkeypatch.setattr(
        matrix.sys,
        "argv",
        ["run_database_pool_saturation_matrix.py"],
    )

    arguments = matrix.parse_arguments()

    assert arguments.connection_hold_ms == 0


def test_parse_arguments_accepts_connection_hold(
    monkeypatch,
):
    monkeypatch.setattr(
        matrix.sys,
        "argv",
        [
            "run_database_pool_saturation_matrix.py",
            "--connection-hold-ms",
            "100",
        ],
    )

    arguments = matrix.parse_arguments()

    assert arguments.connection_hold_ms == 100


def test_main_rejects_excessive_connection_hold(
    monkeypatch,
):
    arguments = argparse.Namespace(
        concurrencies=[4],
        repetitions=1,
        request_count=8,
        connection_hold_ms=1001,
        warmup_count=2,
        stabilization_seconds=0,
        recovery_seconds=0,
        connect_timeout_seconds=3,
        read_timeout_seconds=10,
        api_ready_timeout_seconds=10,
    )

    monkeypatch.setattr(
        matrix,
        "parse_arguments",
        lambda: arguments,
    )

    with pytest.raises(
        ValueError,
        match="--connection-hold-ms must be between 0 and 1000",
    ):
        matrix.main()
