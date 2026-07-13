import pytest

from scripts.run_database_connection_study import (
    build_summary,
    metric_summary,
    validate_starting_state,
)


def test_metric_summary_reports_expected_values():
    summary = metric_summary(
        [10.0, 20.0, 30.0, 40.0, 50.0]
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


def test_metric_summary_handles_empty_input():
    summary = metric_summary([])

    assert summary["count"] == 0
    assert summary["minimum_ms"] is None
    assert summary["mean_ms"] is None
    assert summary["p95_ms"] is None
    assert summary["maximum_ms"] is None


def test_validate_starting_state_accepts_valid_manifest():
    manifest = {
        "starting_state_valid": True,
        "strategy": {
            "connection_strategy": (
                "connection_per_operation"
            )
        },
        "database_after_warmup": {
            "idle_in_transaction_count": 0
        },
    }

    validate_starting_state(
        manifest,
        "connection_per_operation",
    )


def test_validate_starting_state_rejects_strategy_mismatch():
    manifest = {
        "starting_state_valid": True,
        "strategy": {
            "connection_strategy": "bounded_pool"
        },
        "database_after_warmup": {
            "idle_in_transaction_count": 0
        },
    }

    with pytest.raises(
        RuntimeError,
        match="Starting-state strategy mismatch",
    ):
        validate_starting_state(
            manifest,
            "connection_per_operation",
        )


def test_validate_starting_state_rejects_open_transaction():
    manifest = {
        "starting_state_valid": True,
        "strategy": {
            "connection_strategy": (
                "connection_per_operation"
            )
        },
        "database_after_warmup": {
            "idle_in_transaction_count": 1
        },
    }

    with pytest.raises(
        RuntimeError,
        match="idle-in-transaction",
    ):
        validate_starting_state(
            manifest,
            "connection_per_operation",
        )


def test_build_summary_reports_direct_strategy_results():
    rows = [
        {
            "outcome": "success",
            "client_elapsed_ms": 30.0,
            "acquire_ms": 20.0,
            "query_ms": 5.0,
            "fetch_ms": 0.1,
            "release_ms": 0.5,
            "database_total_ms": 25.6,
            "pool_size": "",
            "pool_available": "",
            "requests_waiting": "",
            "requests_queued": "",
            "request_id": "request-1",
            "error_type": "",
            "error_message": "",
        },
        {
            "outcome": "success",
            "client_elapsed_ms": 40.0,
            "acquire_ms": 25.0,
            "query_ms": 6.0,
            "fetch_ms": 0.1,
            "release_ms": 0.6,
            "database_total_ms": 31.7,
            "pool_size": "",
            "pool_available": "",
            "requests_waiting": "",
            "requests_queued": "",
            "request_id": "request-2",
            "error_type": "",
            "error_message": "",
        },
    ]

    summary = build_summary(
        rows=rows,
        run_id="direct-test-run",
        strategy="connection_per_operation",
        mode="warm",
        request_count=2,
        concurrency=1,
        elapsed_seconds=1.0,
        starting_state_run_id="state-run",
        api_log_line_count=6,
    )

    assert summary["success_count"] == 2
    assert summary["failure_count"] == 0
    assert summary["pool_observations"] is None
    assert (
        summary["metrics"]["acquire_ms"]["mean_ms"]
        == 22.5
    )


def test_build_summary_reports_pool_observations():
    rows = [
        {
            "outcome": "success",
            "client_elapsed_ms": 15.0,
            "acquire_ms": 0.5,
            "query_ms": 5.0,
            "fetch_ms": 0.1,
            "release_ms": 0.4,
            "database_total_ms": 6.0,
            "pool_size": 6,
            "pool_available": 2,
            "requests_waiting": 1,
            "requests_queued": 3,
            "request_id": "request-1",
            "error_type": "",
            "error_message": "",
        },
        {
            "outcome": "success",
            "client_elapsed_ms": 18.0,
            "acquire_ms": 1.0,
            "query_ms": 6.0,
            "fetch_ms": 0.1,
            "release_ms": 0.5,
            "database_total_ms": 7.6,
            "pool_size": 8,
            "pool_available": 0,
            "requests_waiting": 2,
            "requests_queued": 5,
            "request_id": "request-2",
            "error_type": "",
            "error_message": "",
        },
    ]

    summary = build_summary(
        rows=rows,
        run_id="pool-test-run",
        strategy="bounded_pool",
        mode="warm",
        request_count=2,
        concurrency=1,
        elapsed_seconds=1.0,
        starting_state_run_id="state-run",
        api_log_line_count=6,
    )

    assert summary["pool_observations"] == {
        "maximum_pool_size": 8,
        "minimum_available": 0,
        "maximum_requests_waiting": 2,
        "highest_cumulative_requests_queued_since_api_start": 5,
    }
