import pytest

from scripts.run_database_connection_study import (
    TIMING_ENDPOINT,
    build_summary,
    execute_worker,
    metric_summary,
    validate_starting_state,
)


class _ImmediateBarrier:
    def wait(self):
        return 0


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.headers = {
            "X-Request-ID": "response-request-id",
        }

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload
        self.requested_urls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, url, headers, timeout):
        self.requested_urls.append(url)
        return _FakeResponse(self._payload)


def _success_payload(
    *,
    connection_hold_ms,
    strategy="bounded_pool",
):
    pool = None

    if strategy == "bounded_pool":
        pool = {
            "statistics": {
                "pool_size": 4,
                "pool_available": 3,
                "requests_waiting": 0,
                "requests_queued": 1,
            }
        }

    return {
        "connection_hold_ms": connection_hold_ms,
        "connection_strategy": strategy,
        "database_phases": {
            "acquire_ms": 0.1,
            "query_ms": 1.0,
            "fetch_ms": 0.1,
            "release_ms": 0.2,
            "total_ms": 101.4,
        },
        "database_resources": {
            "connection_strategy": strategy,
            "pool": pool,
        },
    }


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
        configuration_label="direct",
        mode="warm",
        request_count=2,
        concurrency=1,
        elapsed_seconds=1.0,
        starting_state_run_id="state-run",
        api_log_line_count=6,
    )

    assert summary["configuration_label"] == "direct"
    assert summary["connection_hold_ms"] == 0
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
        configuration_label="dynamic-4-8",
        mode="warm",
        request_count=2,
        concurrency=1,
        elapsed_seconds=1.0,
        starting_state_run_id="state-run",
        api_log_line_count=6,
        connection_hold_ms=100,
    )

    assert summary["connection_hold_ms"] == 100
    assert summary["pool_observations"] == {
        "maximum_pool_size": 8,
        "minimum_available": 0,
        "maximum_requests_waiting": 2,
        "highest_cumulative_requests_queued_since_api_start": 5,
    }


def test_execute_worker_uses_default_endpoint_for_zero_hold(
    monkeypatch,
):
    fake_session = _FakeSession(
        _success_payload(connection_hold_ms=0)
    )

    monkeypatch.setattr(
        "scripts.run_database_connection_study.requests.Session",
        lambda: fake_session,
    )

    rows = execute_worker(
        worker_number=1,
        requests_per_worker=1,
        strategy="bounded_pool",
        run_id="zero-hold-run",
        barrier=_ImmediateBarrier(),
        connect_timeout_seconds=3.0,
        read_timeout_seconds=10.0,
    )

    assert fake_session.requested_urls == [TIMING_ENDPOINT]
    assert rows[0]["outcome"] == "success"
    assert rows[0]["connection_hold_ms"] == 0


def test_execute_worker_sends_and_records_connection_hold(
    monkeypatch,
):
    fake_session = _FakeSession(
        _success_payload(connection_hold_ms=100)
    )

    monkeypatch.setattr(
        "scripts.run_database_connection_study.requests.Session",
        lambda: fake_session,
    )

    rows = execute_worker(
        worker_number=1,
        requests_per_worker=1,
        strategy="bounded_pool",
        run_id="held-run",
        barrier=_ImmediateBarrier(),
        connect_timeout_seconds=3.0,
        read_timeout_seconds=10.0,
        connection_hold_ms=100,
    )

    assert fake_session.requested_urls == [
        f"{TIMING_ENDPOINT}&connection_hold_ms=100"
    ]
    assert rows[0]["outcome"] == "success"
    assert rows[0]["connection_hold_ms"] == 100


def test_execute_worker_detects_hold_response_mismatch(
    monkeypatch,
):
    fake_session = _FakeSession(
        _success_payload(connection_hold_ms=50)
    )

    monkeypatch.setattr(
        "scripts.run_database_connection_study.requests.Session",
        lambda: fake_session,
    )

    rows = execute_worker(
        worker_number=1,
        requests_per_worker=1,
        strategy="bounded_pool",
        run_id="mismatch-run",
        barrier=_ImmediateBarrier(),
        connect_timeout_seconds=3.0,
        read_timeout_seconds=10.0,
        connection_hold_ms=100,
    )

    assert rows[0]["outcome"] == "failure"
    assert rows[0]["error_type"] == "RuntimeError"
    assert (
        "Response connection hold mismatch"
        in rows[0]["error_message"]
    )
