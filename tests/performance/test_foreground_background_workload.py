"""Fast tests for the mixed foreground/background workload runner."""

import pytest

from scripts.run_foreground_background_workload import (
    MixedWorkloadConfiguration,
    WorkloadConfiguration,
    metric_summary,
)


def build_valid_configuration() -> MixedWorkloadConfiguration:
    """Return a small valid configuration used by multiple tests."""

    return MixedWorkloadConfiguration(
        foreground=WorkloadConfiguration(
            request_count=20,
            concurrency=4,
        ),
        background=WorkloadConfiguration(
            request_count=4,
            concurrency=2,
        ),
        foreground_connection_hold_ms=0,
        background_batch_size=2,
        connect_timeout_seconds=3.0,
        read_timeout_seconds=15.0,
    )


def test_configuration_calculates_deterministic_work_distribution() -> None:
    """Verify worker distribution and encounter demand calculations."""

    configuration = build_valid_configuration()

    configuration.validate()

    assert configuration.foreground.requests_per_worker == 5
    assert configuration.background.requests_per_worker == 2
    assert configuration.required_encounter_count == 8
    assert configuration.total_concurrency == 6


@pytest.mark.parametrize(
    (
        "request_count",
        "concurrency",
        "expected_message",
    ),
    [
        (0, 4, "request count must be greater than zero"),
        (20, 0, "concurrency must be greater than zero"),
        (
            21,
            4,
            "request count must be divisible by foreground concurrency",
        ),
    ],
)
def test_foreground_configuration_rejects_invalid_worker_distribution(
    request_count: int,
    concurrency: int,
    expected_message: str,
) -> None:
    """Verify malformed foreground workloads fail before execution."""

    configuration = build_valid_configuration()

    invalid_configuration = MixedWorkloadConfiguration(
        foreground=WorkloadConfiguration(
            request_count=request_count,
            concurrency=concurrency,
        ),
        background=configuration.background,
        foreground_connection_hold_ms=(
            configuration.foreground_connection_hold_ms
        ),
        background_batch_size=configuration.background_batch_size,
        connect_timeout_seconds=configuration.connect_timeout_seconds,
        read_timeout_seconds=configuration.read_timeout_seconds,
    )

    with pytest.raises(ValueError, match=expected_message):
        invalid_configuration.validate()


@pytest.mark.parametrize(
    "batch_size",
    [0, 101],
)
def test_configuration_rejects_invalid_background_batch_size(
    batch_size: int,
) -> None:
    """Verify background batches remain within the API contract."""

    configuration = build_valid_configuration()

    invalid_configuration = MixedWorkloadConfiguration(
        foreground=configuration.foreground,
        background=configuration.background,
        foreground_connection_hold_ms=(
            configuration.foreground_connection_hold_ms
        ),
        background_batch_size=batch_size,
        connect_timeout_seconds=configuration.connect_timeout_seconds,
        read_timeout_seconds=configuration.read_timeout_seconds,
    )

    with pytest.raises(
        ValueError,
        match="background batch size must be between 1 and 100",
    ):
        invalid_configuration.validate()


def test_metric_summary_uses_repeatable_nearest_rank_percentiles() -> None:
    """Verify latency summaries remain deterministic."""

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


def test_metric_summary_handles_no_successful_measurements() -> None:
    """Verify an empty result set has an explicit summary shape."""

    assert metric_summary([]) == {
        "count": 0,
        "minimum_ms": None,
        "mean_ms": None,
        "p50_ms": None,
        "p95_ms": None,
        "p99_ms": None,
        "maximum_ms": None,
    }