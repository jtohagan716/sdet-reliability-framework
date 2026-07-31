from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import scripts.run_foreground_background_workload as workload_runner


def build_arguments(
    **overrides: Any,
) -> argparse.Namespace:
    """Build valid command-line arguments with optional overrides."""

    values: dict[str, Any] = {
        "expected_pool_topology": "shared_pool",
        "foreground_request_count": 20,
        "foreground_concurrency": 4,
        "foreground_connection_hold_ms": 0,
        "background_request_count": 4,
        "background_concurrency": 2,
        "background_batch_size": 2,
        "connect_timeout_seconds": 3.0,
        "read_timeout_seconds": 15.0,
    }

    values.update(overrides)

    return argparse.Namespace(**values)

@pytest.mark.parametrize(
    ("pool_topology", "expected_scenario"),
    (
        ("shared_pool", "shared_pool_mixed_workload"),
        ("isolated_pools", "isolated_pools_mixed_workload"),
    ),
)
def test_build_scenario_name_identifies_pool_topology(
    pool_topology: str,
    expected_scenario: str,
) -> None:
    """Scenario evidence must identify the topology under test."""

    assert (
        workload_runner.build_scenario_name(pool_topology)
        == expected_scenario
    )


@pytest.mark.parametrize(
    ("pool_topology", "expected_run_id"),
    (
        (
            "shared_pool",
            (
                "foreground-background-shared-pool-"
                "20260730T181500123456Z"
            ),
        ),
        (
            "isolated_pools",
            (
                "foreground-background-isolated-pools-"
                "20260730T181500123456Z"
            ),
        ),
    ),
)
def test_build_run_id_is_deterministic_and_topology_aware(
    pool_topology: str,
    expected_run_id: str,
) -> None:
    """A fixed timestamp must produce a repeatable topology-aware ID."""

    generated_at = datetime(
        2026,
        7,
        30,
        18,
        15,
        0,
        123456,
        tzinfo=UTC,
    )

    run_id = workload_runner.build_run_id(
        pool_topology=pool_topology,
        generated_at=generated_at,
    )

    assert run_id == expected_run_id


@pytest.mark.parametrize(
    "builder",
    (
        workload_runner.build_scenario_name,
        lambda pool_topology: workload_runner.build_run_id(
            pool_topology=pool_topology,
            generated_at=datetime(
                2026,
                7,
                30,
                tzinfo=UTC,
            ),
        ),
    ),
)
def test_evidence_naming_rejects_unsupported_topology(
    builder: Any,
) -> None:
    """Unsupported topologies must never create misleading evidence."""

    with pytest.raises(
        ValueError,
        match="Unsupported database pool topology: unknown_pool",
    ):
        builder("unknown_pool")

def test_parse_arguments_defaults_to_shared_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The original shared-pool scenario remains the CLI default."""

    monkeypatch.setattr(
        "sys.argv",
        ["run_foreground_background_workload.py"],
    )

    arguments = workload_runner.parse_arguments()

    assert arguments.expected_pool_topology == "shared_pool"


def test_extract_pool_statistics_rejects_unexpected_topology() -> None:
    """Pool evidence must come from the requested runtime topology."""

    payload = {
        "database_resources": {
            "connection_strategy": "bounded_pool",
            "pool_topology": "isolated_pools",
            "workload": "foreground",
            "pool": {
                "name": "interactive-api-pool",
                "configuration": {
                    "min_size": 4,
                    "max_size": 8,
                    "timeout_seconds": 5.0,
                    "startup_timeout_seconds": 30.0,
                    "max_waiting": 40,
                },
                "statistics": {
                    "pool_size": 4,
                    "pool_available": 3,
                    "requests_waiting": 1,
                },
            },
        },
    }

    with pytest.raises(
        RuntimeError,
        match=(
            "Expected database pool topology 'shared_pool', "
            "but the API reported 'isolated_pools'"
        ),
    ):
        workload_runner.extract_pool_statistics(
            payload,
            expected_pool_topology="shared_pool",
        )


def test_extract_pool_statistics_preserves_missing_requests_queued() -> None:
    """An unavailable queue metric must not be reported as measured zero."""

    payload = {
        "database_resources": {
            "connection_strategy": "bounded_pool",
            "pool_topology": "shared_pool",
            "workload": "foreground",
            "pool": {
                "name": "interactive-api-pool",
                "configuration": {
                    "min_size": 4,
                    "max_size": 8,
                    "timeout_seconds": 5.0,
                    "startup_timeout_seconds": 30.0,
                    "max_waiting": 40,
                },
                "statistics": {
                    "pool_size": 4,
                    "pool_available": 3,
                    "requests_waiting": 1,
                },
            },
        },
    }

    statistics = workload_runner.extract_pool_statistics(
        payload,
        expected_pool_topology="shared_pool",
    )

    assert statistics["requests_queued"] is None
    assert statistics["pool_topology"] == "shared_pool"


def build_pool_evidence_row(
    *,
    workload_type: str,
    pool_name: str,
    minimum_size: int,
    maximum_size: int,
    maximum_waiting: int,
) -> dict[str, object]:
    """Build one successful runtime pool-configuration evidence row."""

    return {
        "outcome": "success",
        "workload_type": workload_type,
        "pool_name": pool_name,
        "pool_min_size": minimum_size,
        "pool_max_size": maximum_size,
        "pool_timeout_seconds": 5.0,
        "pool_startup_timeout_seconds": 30.0,
        "pool_max_waiting": maximum_waiting,
    }


def test_observed_pool_configuration_counts_shared_pool_once() -> None:
    """Shared workloads must contribute one physical pool budget."""

    rows = [
        build_pool_evidence_row(
            workload_type="foreground",
            pool_name="interactive-api-pool",
            minimum_size=4,
            maximum_size=8,
            maximum_waiting=40,
        ),
        build_pool_evidence_row(
            workload_type="background",
            pool_name="interactive-api-pool",
            minimum_size=4,
            maximum_size=8,
            maximum_waiting=40,
        ),
    ]

    observed = workload_runner.observed_pool_configuration(rows)

    assert observed["unique_pool_count"] == 1
    assert observed["combined_min_size"] == 4
    assert observed["combined_max_size"] == 8
    assert observed["foreground"] == observed["background"]


def test_observed_pool_configuration_combines_isolated_budgets() -> None:
    """Isolated foreground and background pools must both be counted."""

    rows = [
        build_pool_evidence_row(
            workload_type="foreground",
            pool_name="interactive-api-pool",
            minimum_size=3,
            maximum_size=6,
            maximum_waiting=40,
        ),
        build_pool_evidence_row(
            workload_type="background",
            pool_name="background-worker-pool",
            minimum_size=1,
            maximum_size=2,
            maximum_waiting=10,
        ),
    ]

    observed = workload_runner.observed_pool_configuration(rows)

    assert observed["unique_pool_count"] == 2
    assert observed["combined_min_size"] == 4
    assert observed["combined_max_size"] == 8
    assert (
        observed["foreground"]["pool_name"]
        == "interactive-api-pool"
    )
    assert (
        observed["background"]["pool_name"]
        == "background-worker-pool"
    )


def test_observed_pool_configuration_rejects_conflicting_rows() -> None:
    """One workload cannot report multiple runtime pool budgets."""

    rows = [
        build_pool_evidence_row(
            workload_type="foreground",
            pool_name="interactive-api-pool",
            minimum_size=4,
            maximum_size=8,
            maximum_waiting=40,
        ),
        build_pool_evidence_row(
            workload_type="foreground",
            pool_name="interactive-api-pool",
            minimum_size=4,
            maximum_size=9,
            maximum_waiting=40,
        ),
    ]

    with pytest.raises(
        RuntimeError,
        match=(
            "Foreground evidence contains conflicting "
            "pool configurations"
        ),
    ):
        workload_runner.observed_pool_configuration(rows)


def test_extract_pool_statistics_rejects_missing_configuration() -> None:
    """Incomplete runtime pool configuration cannot become evidence."""

    payload = {
        "database_resources": {
            "connection_strategy": "bounded_pool",
            "pool_topology": "shared_pool",
            "workload": "foreground",
            "pool": {
                "name": "interactive-api-pool",
                "configuration": {
                    "min_size": 4,
                    "max_size": 8,
                    "timeout_seconds": 5.0,
                    "startup_timeout_seconds": 30.0,
                },
                "statistics": {
                    "pool_size": 4,
                    "pool_available": 3,
                    "requests_waiting": 0,
                },
            },
        },
    }

    with pytest.raises(
        RuntimeError,
        match=(
            "Bounded-pool response is missing configuration fields: "
            "max_waiting"
        ),
    ):
        workload_runner.extract_pool_statistics(
            payload,
            expected_pool_topology="shared_pool",
        )


def test_validate_pool_topology_rejects_runtime_mismatch() -> None:
    """Requested and observed pool topologies must agree."""

    with pytest.raises(
        RuntimeError,
        match=(
            "Expected database pool topology 'shared_pool', "
            "but the API reported 'isolated_pools'"
        ),
    ):
        workload_runner.validate_pool_topology(
            expected_pool_topology="shared_pool",
            observed_pool_topology="isolated_pools",
        )


def test_build_configuration_uses_deterministic_worker_distribution() -> None:
    """Each worker must receive an exact, repeatable request count."""

    configuration = workload_runner.build_configuration(
        build_arguments()
    )

    assert configuration.expected_pool_topology == "shared_pool"

    assert configuration.foreground.request_count == 20
    assert configuration.foreground.concurrency == 4
    assert configuration.foreground.requests_per_worker == 5

    assert configuration.background.request_count == 4
    assert configuration.background.concurrency == 2
    assert configuration.background.requests_per_worker == 2

    assert configuration.background_batch_size == 2
    assert configuration.required_encounter_count == 8
    assert configuration.total_concurrency == 6


def test_foreground_request_count_must_be_positive() -> None:
    """A workload cannot run without at least one request."""

    with pytest.raises(
        ValueError,
        match="foreground request count must be greater than zero",
    ):
        workload_runner.build_configuration(
            build_arguments(
                foreground_request_count=0,
            )
        )


def test_foreground_concurrency_must_be_positive() -> None:
    """A workload cannot run without at least one worker."""

    with pytest.raises(
        ValueError,
        match="foreground concurrency must be greater than zero",
    ):
        workload_runner.build_configuration(
            build_arguments(
                foreground_concurrency=0,
            )
        )


def test_foreground_requests_must_divide_evenly() -> None:
    """Worker request assignments must remain deterministic."""

    with pytest.raises(
        ValueError,
        match=(
            "foreground request count must be divisible by "
            "foreground concurrency"
        ),
    ):
        workload_runner.build_configuration(
            build_arguments(
                foreground_request_count=19,
                foreground_concurrency=4,
            )
        )


@pytest.mark.parametrize(
    "batch_size",
    [
        0,
        101,
    ],
)
def test_background_batch_size_must_be_within_endpoint_limits(
    batch_size: int,
) -> None:
    """The runner must reject unsupported batch sizes early."""

    with pytest.raises(
        ValueError,
        match="background batch size must be between 1 and 100",
    ):
        workload_runner.build_configuration(
            build_arguments(
                background_batch_size=batch_size,
            )
        )


def test_metric_summary_uses_nearest_rank_percentiles() -> None:
    """Metric calculations must remain stable and reproducible."""

    summary = workload_runner.metric_summary(
        [
            10.0,
            20.0,
            30.0,
            40.0,
            50.0,
        ]
    )

    assert summary == {
        "count": 5,
        "minimum_ms": 10.0,
        "mean_ms": 30.0,
        "p50_ms": 30.0,
        "p95_ms": 50.0,
        "p99_ms": 50.0,
        "maximum_ms": 50.0,
    }


def test_metric_summary_returns_explicit_empty_shape() -> None:
    """Empty measurements must not produce misleading zero latency."""

    summary = workload_runner.metric_summary([])

    assert summary == {
        "count": 0,
        "minimum_ms": None,
        "mean_ms": None,
        "p50_ms": None,
        "p95_ms": None,
        "p99_ms": None,
        "maximum_ms": None,
    }


def build_success_row(
    *,
    workload_type: str,
    sequence_number: int,
    client_elapsed_ms: float,
    database_total_ms: float,
) -> dict[str, object]:
    """Build the minimum successful row needed by phase summaries."""

    return {
        "workload_type": workload_type,
        "sequence_number": sequence_number,
        "outcome": "success",
        "client_elapsed_ms": client_elapsed_ms,
        "database_total_ms": database_total_ms,
    }


def test_classify_request_phase_distinguishes_first_request() -> None:
    """The first request must remain separate from steady-state work."""

    assert (
        workload_runner.classify_request_phase(1)
        == "first_request"
    )

    assert (
        workload_runner.classify_request_phase(2)
        == "later_requests"
    )

    assert (
        workload_runner.classify_request_phase(10)
        == "later_requests"
    )


def test_classify_request_phase_rejects_invalid_sequence() -> None:
    """Request sequence numbers must be positive."""

    with pytest.raises(
        ValueError,
        match="sequence number must be greater than zero",
    ):
        workload_runner.classify_request_phase(0)


def test_summarize_request_phases_separates_warmup_effect() -> None:
    """First-wave and later-request measurements stay independent."""

    rows = [
        build_success_row(
            workload_type="foreground",
            sequence_number=1,
            client_elapsed_ms=100.0,
            database_total_ms=25.0,
        ),
        build_success_row(
            workload_type="foreground",
            sequence_number=2,
            client_elapsed_ms=30.0,
            database_total_ms=20.0,
        ),
        build_success_row(
            workload_type="foreground",
            sequence_number=3,
            client_elapsed_ms=40.0,
            database_total_ms=20.0,
        ),
        build_success_row(
            workload_type="background",
            sequence_number=1,
            client_elapsed_ms=160.0,
            database_total_ms=80.0,
        ),
        build_success_row(
            workload_type="background",
            sequence_number=2,
            client_elapsed_ms=90.0,
            database_total_ms=70.0,
        ),
    ]

    summary = workload_runner.summarize_request_phases(rows)

    foreground_first = summary["foreground"]["first_request"]

    assert foreground_first["count"] == 1
    assert foreground_first["average_client_ms"] == 100.0
    assert foreground_first["average_database_ms"] == 25.0
    assert (
        foreground_first["average_outside_database_ms"]
        == 75.0
    )

    foreground_later = summary["foreground"]["later_requests"]

    assert foreground_later["count"] == 2
    assert foreground_later["average_client_ms"] == 35.0
    assert foreground_later["average_database_ms"] == 20.0
    assert (
        foreground_later["average_outside_database_ms"]
        == 15.0
    )

    background_first = summary["background"]["first_request"]

    assert background_first["count"] == 1
    assert background_first["average_client_ms"] == 160.0
    assert background_first["average_database_ms"] == 80.0
    assert (
        background_first["average_outside_database_ms"]
        == 80.0
    )

    background_later = summary["background"]["later_requests"]

    assert background_later["count"] == 1
    assert background_later["average_client_ms"] == 90.0
    assert background_later["average_database_ms"] == 70.0
    assert (
        background_later["average_outside_database_ms"]
        == 20.0
    )


def build_empty_metric_summary() -> dict[str, float | int | None]:
    """Build an explicit empty latency summary for report tests."""

    return {
        "count": 0,
        "minimum_ms": None,
        "mean_ms": None,
        "p50_ms": None,
        "p95_ms": None,
        "p99_ms": None,
        "maximum_ms": None,
    }


def build_empty_workload_summary() -> dict[str, Any]:
    """Build the workload structure expected by report generation."""

    return {
        "request_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "success_rate_percent": 0.0,
        "throughput_requests_per_second": 0.0,
        "metrics": {
            "client_elapsed_ms": build_empty_metric_summary(),
            "database_acquire_ms": build_empty_metric_summary(),
            "database_query_ms": build_empty_metric_summary(),
            "database_fetch_ms": build_empty_metric_summary(),
            "database_release_ms": build_empty_metric_summary(),
            "database_total_ms": build_empty_metric_summary(),
        },
        "pool_observations": {
            "peak_pool_size": None,
            "minimum_pool_available": None,
            "peak_requests_waiting": None,
            "peak_requests_queued": None,
        },
        "database_work": {
            "selected_count": 0,
            "updated_count": 0,
            "audit_count": 0,
        },
        "failures": [],
    }



def test_observed_pool_topology_returns_verified_runtime_value() -> None:
    """Successful request evidence identifies the runtime topology."""

    rows = [
        {
            "outcome": "success",
            "pool_topology": "isolated_pools",
        },
        {
            "outcome": "success",
            "pool_topology": "isolated_pools",
        },
        {
            "outcome": "failure",
            "pool_topology": "shared_pool",
        },
    ]

    assert (
        workload_runner.observed_pool_topology(rows)
        == "isolated_pools"
    )


def test_observed_pool_topology_returns_none_without_successes() -> None:
    """A failed run must not invent observed topology evidence."""

    rows = [
        {
            "outcome": "failure",
            "pool_topology": "",
        }
    ]

    assert workload_runner.observed_pool_topology(rows) is None


def test_observed_pool_topology_rejects_conflicting_evidence() -> None:
    """One run cannot credibly report two successful topologies."""

    rows = [
        {
            "outcome": "success",
            "pool_topology": "shared_pool",
        },
        {
            "outcome": "success",
            "pool_topology": "isolated_pools",
        },
    ]

    with pytest.raises(
        RuntimeError,
        match=(
            "Run contains conflicting observed pool topologies: "
            "isolated_pools, shared_pool"
        ),
    ):
        workload_runner.observed_pool_topology(rows)

def build_empty_phase_summary() -> dict[str, Any]:
    """Build an empty first-request or later-request summary."""

    return {
        "count": 0,
        "average_client_ms": None,
        "average_database_ms": None,
        "average_outside_database_ms": None,
    }


def build_request_phase_report_summary() -> dict[str, Any]:
    """Build both workload phase structures required by Markdown."""

    return {
        "foreground": {
            "first_request": build_empty_phase_summary(),
            "later_requests": build_empty_phase_summary(),
        },
        "background": {
            "first_request": build_empty_phase_summary(),
            "later_requests": build_empty_phase_summary(),
        },
    }


def test_write_run_artifacts_creates_reviewable_evidence(
    tmp_path: Path,
) -> None:
    """One run produces raw, machine-readable, and human reports."""

    run_directory = tmp_path / "example-run"
    run_directory.mkdir()

    rows = [
        {
            field_name: ""
            for field_name in workload_runner.CSV_FIELD_NAMES
        }
    ]

    rows[0].update(
        {
            "run_id": "example-run",
            "workload_type": "foreground",
            "worker_number": 1,
            "sequence_number": 1,
            "request_phase": "first_request",
            "request_number": 1,
            "request_id": "example-request",
            "client_elapsed_ms": 10.0,
            "outcome": "success",
            "pool_topology": "isolated_pools",
            "encounter_ids": [],
        }
    )

    report = {
        "run_id": "example-run",
        "scenario": "shared_pool_mixed_workload",
        "api_base_url": "http://localhost:8000",
        "expected_connection_strategy": "bounded_pool",
        "expected_pool_topology": "isolated_pools",
        "observed_pool_topology": "isolated_pools",
        "observed_pool_configuration": {
            "foreground": {
                "pool_name": "interactive-api-pool",
                "min_size": 3,
                "max_size": 6,
                "timeout_seconds": 5.0,
                "startup_timeout_seconds": 30.0,
                "max_waiting": 40,
            },
            "background": {
                "pool_name": "background-worker-pool",
                "min_size": 1,
                "max_size": 2,
                "timeout_seconds": 5.0,
                "startup_timeout_seconds": 30.0,
                "max_waiting": 10,
            },
            "unique_pool_count": 2,
            "combined_min_size": 4,
            "combined_max_size": 8,
        },
        "configuration": {
            "foreground": {
                "request_count": 1,
                "concurrency": 1,
                "requests_per_worker": 1,
                "connection_hold_ms": 0,
            },
            "background": {
                "request_count": 1,
                "concurrency": 1,
                "requests_per_worker": 1,
                "batch_size": 1,
                "required_encounter_count": 1,
            },
            "combined": {
                "total_concurrency": 2,
                "connect_timeout_seconds": 3.0,
                "read_timeout_seconds": 15.0,
            },
        },
        "dataset": {
            "record_count": 1,
        },
        "execution": {
            "started_at_utc": "2026-07-21T18:00:00+00:00",
            "finished_at_utc": "2026-07-21T18:00:01+00:00",
            "fatal_error": "",
        },
        "summary": {
            "elapsed_seconds": 1.0,
            "total_request_count": 1,
            "total_success_count": 1,
            "total_failure_count": 0,
            "foreground": build_empty_workload_summary(),
            "background": build_empty_workload_summary(),
            "request_phases": (
                build_request_phase_report_summary()
            ),
        },
        "cleanup": {
            "encounters_deleted": 1,
            "audit_rows_deleted": 2,
        },
        "cleanup_error": "",
    }

    paths = workload_runner.write_run_artifacts(
        run_directory=run_directory,
        rows=rows,
        report=report,
    )

    assert paths["request_csv"].is_file()
    assert paths["json_report"].is_file()
    assert paths["markdown_report"].is_file()

    with paths["request_csv"].open(
        encoding="utf-8",
        newline="",
    ) as csv_file:
        csv_rows = list(csv.DictReader(csv_file))

    assert len(csv_rows) == 1
    assert csv_rows[0]["request_id"] == "example-request"
    assert csv_rows[0]["request_phase"] == "first_request"
    assert csv_rows[0]["pool_topology"] == "isolated_pools"

    json_report = json.loads(
        paths["json_report"].read_text(
            encoding="utf-8",
        )
    )

    assert json_report["run_id"] == "example-run"
    assert (
        json_report["expected_pool_topology"]
        == "isolated_pools"
    )
    assert (
        json_report["observed_pool_topology"]
        == "isolated_pools"
    )
    assert (
        json_report["observed_pool_configuration"][
            "combined_max_size"
        ]
        == 8
    )

    markdown_report = paths["markdown_report"].read_text(
        encoding="utf-8",
    )

    assert (
        "# Foreground vs. Background Workload Run"
        in markdown_report
    )

    assert (
        "## First-request versus later-request behavior"
        in markdown_report
    )

    assert "`request-results.csv`" in markdown_report
    assert (
        "Pool topology expected: `isolated_pools`"
        in markdown_report
    )
    assert (
        "Pool topology observed: `isolated_pools`"
        in markdown_report
    )
    assert (
        "uses the configured bounded connection-pool topology"
        in markdown_report
    )
    assert (
        "use the same bounded database connection pool"
        not in markdown_report
    )
