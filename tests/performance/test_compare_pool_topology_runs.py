from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "compare_pool_topology_runs.py"
)


def load_comparator() -> ModuleType:
    """Load the comparison script as an importable test module."""

    specification = importlib.util.spec_from_file_location(
        "compare_pool_topology_runs",
        SCRIPT_PATH,
    )

    if specification is None or specification.loader is None:
        raise RuntimeError(
            "Could not load compare_pool_topology_runs.py"
        )

    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    return module


comparator = load_comparator()


def build_runtime_pool_configuration(
    topology: str,
) -> dict[str, object]:
    """Build one runtime-verified pool configuration fixture."""

    if topology == comparator.SHARED_POOL:
        shared_pool = {
            "pool_name": "interactive-api-pool",
            "min_size": 4,
            "max_size": 8,
            "timeout_seconds": 5.0,
            "startup_timeout_seconds": 30.0,
            "max_waiting": 40,
        }

        return {
            "foreground": copy.deepcopy(shared_pool),
            "background": copy.deepcopy(shared_pool),
            "unique_pool_count": 1,
            "combined_min_size": 4,
            "combined_max_size": 8,
        }

    return {
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
    }


def build_report(
    *,
    topology: str,
    trial_number: int,
    foreground_p50_ms: float,
    foreground_p95_ms: float,
    foreground_acquire_p95_ms: float,
    background_p95_ms: float,
    foreground_waiting: int,
) -> dict[str, object]:
    """Build one complete synthetic mixed-workload report."""

    topology_label = topology.replace("_", "-")

    return {
        "run_id": (
            f"foreground-background-{topology_label}-"
            f"trial-{trial_number}"
        ),
        "expected_pool_topology": topology,
        "observed_pool_topology": topology,
        "observed_pool_configuration": (
            build_runtime_pool_configuration(topology)
        ),
        "configuration": {
            "foreground": {
                "request_count": 60,
                "concurrency": 6,
                "requests_per_worker": 10,
                "connection_hold_ms": 100,
            },
            "background": {
                "request_count": 20,
                "concurrency": 4,
                "requests_per_worker": 5,
                "batch_size": 2,
                "required_encounter_count": 40,
            },
            "combined": {
                "total_concurrency": 10,
                "connect_timeout_seconds": 3.0,
                "read_timeout_seconds": 15.0,
            },
        },
        "execution": {
            "elapsed_seconds": 1.25,
            "fatal_error": "",
        },
        "summary": {
            "total_failure_count": 0,
            "foreground": {
                "request_count": 60,
                "metrics": {
                    "client_elapsed_ms": {
                        "p50_ms": foreground_p50_ms,
                        "p95_ms": foreground_p95_ms,
                    },
                    "database_acquire_ms": {
                        "p95_ms": foreground_acquire_p95_ms,
                    },
                },
                "pool_observations": {
                    "peak_requests_waiting": foreground_waiting,
                },
            },
            "background": {
                "request_count": 20,
                "metrics": {
                    "client_elapsed_ms": {
                        "p95_ms": background_p95_ms,
                    },
                },
            },
            "request_phases": {
                "foreground": {
                    "later_requests": {
                        "average_client_ms": foreground_p50_ms
                        + 5.0,
                    },
                },
            },
        },
        "cleanup_error": "",
    }


def build_valid_report_groups() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Build three valid reports for each topology."""

    shared_reports = [
        build_report(
            topology=comparator.SHARED_POOL,
            trial_number=1,
            foreground_p50_ms=110.0,
            foreground_p95_ms=150.0,
            foreground_acquire_p95_ms=10.0,
            background_p95_ms=90.0,
            foreground_waiting=1,
        ),
        build_report(
            topology=comparator.SHARED_POOL,
            trial_number=2,
            foreground_p50_ms=120.0,
            foreground_p95_ms=160.0,
            foreground_acquire_p95_ms=12.0,
            background_p95_ms=95.0,
            foreground_waiting=1,
        ),
        build_report(
            topology=comparator.SHARED_POOL,
            trial_number=3,
            foreground_p50_ms=115.0,
            foreground_p95_ms=170.0,
            foreground_acquire_p95_ms=14.0,
            background_p95_ms=100.0,
            foreground_waiting=1,
        ),
    ]

    isolated_reports = [
        build_report(
            topology=comparator.ISOLATED_POOLS,
            trial_number=1,
            foreground_p50_ms=118.0,
            foreground_p95_ms=165.0,
            foreground_acquire_p95_ms=0.1,
            background_p95_ms=100.0,
            foreground_waiting=0,
        ),
        build_report(
            topology=comparator.ISOLATED_POOLS,
            trial_number=2,
            foreground_p50_ms=122.0,
            foreground_p95_ms=175.0,
            foreground_acquire_p95_ms=0.2,
            background_p95_ms=110.0,
            foreground_waiting=0,
        ),
        build_report(
            topology=comparator.ISOLATED_POOLS,
            trial_number=3,
            foreground_p50_ms=126.0,
            foreground_p95_ms=185.0,
            foreground_acquire_p95_ms=0.3,
            background_p95_ms=120.0,
            foreground_waiting=0,
        ),
    ]

    return shared_reports, isolated_reports


def test_build_comparison_aggregates_valid_equal_budget_runs() -> None:
    """Valid repeated trials must produce deterministic evidence."""

    shared_reports, isolated_reports = (
        build_valid_report_groups()
    )

    comparison = comparator.build_comparison(
        shared_reports=shared_reports,
        isolated_reports=isolated_reports,
    )

    assert comparison["study"]["total_run_count"] == 6
    assert (
        comparison["study"]["equal_connection_budget"][
            "combined_max_size"
        ]
        == 8
    )

    shared_results = comparison["results"][
        comparator.SHARED_POOL
    ]
    isolated_results = comparison["results"][
        comparator.ISOLATED_POOLS
    ]

    assert (
        shared_results["means"][
            "foreground_acquire_p95_ms"
        ]
        == 12.0
    )
    assert (
        isolated_results["means"][
            "foreground_acquire_p95_ms"
        ]
        == 0.2
    )
    assert shared_results["foreground_waiting_trial_count"] == 3
    assert isolated_results["foreground_waiting_trial_count"] == 0

    assert comparison["findings"][
        "isolated_reduced_foreground_acquisition"
    ]
    assert comparison["findings"][
        "isolated_reduced_waiting_trials"
    ]
    assert not comparison["findings"][
        "isolated_reduced_foreground_p95"
    ]


def test_build_comparison_rejects_mismatched_workload() -> None:
    """Topology must be the only changed experimental variable."""

    shared_reports, isolated_reports = (
        build_valid_report_groups()
    )

    isolated_reports[0]["configuration"]["foreground"][
        "request_count"
    ] = 61

    isolated_reports[0]["summary"]["foreground"][
        "request_count"
    ] = 61

    with pytest.raises(
        ValueError,
        match=(
            "Reports do not use an identical workload "
            "configuration"
        ),
    ):
        comparator.build_comparison(
            shared_reports=shared_reports,
            isolated_reports=isolated_reports,
        )


def test_build_comparison_rejects_unequal_connection_budget() -> None:
    """Pool topology comparisons require equal total capacity."""

    shared_reports, isolated_reports = (
        build_valid_report_groups()
    )

    for report in isolated_reports:
        runtime = report["observed_pool_configuration"]

        runtime["foreground"]["max_size"] = 7
        runtime["combined_max_size"] = 9

    with pytest.raises(
        ValueError,
        match=(
            "Reports do not use an equal combined maximum "
            "connection budget"
        ),
    ):
        comparator.build_comparison(
            shared_reports=shared_reports,
            isolated_reports=isolated_reports,
        )


def test_build_comparison_rejects_failed_run() -> None:
    """A formal comparison cannot include request failures."""

    shared_reports, isolated_reports = (
        build_valid_report_groups()
    )

    shared_reports[1]["summary"]["total_failure_count"] = 1

    with pytest.raises(
        ValueError,
        match="contains 1 request failure",
    ):
        comparator.build_comparison(
            shared_reports=shared_reports,
            isolated_reports=isolated_reports,
        )


def test_build_comparison_rejects_duplicate_report() -> None:
    """Each formal trial must represent a unique run."""

    shared_reports, isolated_reports = (
        build_valid_report_groups()
    )

    shared_reports[2]["run_id"] = shared_reports[1]["run_id"]

    with pytest.raises(
        ValueError,
        match="Duplicate report supplied",
    ):
        comparator.build_comparison(
            shared_reports=shared_reports,
            isolated_reports=isolated_reports,
        )


def test_render_markdown_states_bounded_conclusion() -> None:
    """The report must distinguish isolation from latency improvement."""

    shared_reports, isolated_reports = (
        build_valid_report_groups()
    )

    comparison = comparator.build_comparison(
        shared_reports=shared_reports,
        isolated_reports=isolated_reports,
    )

    markdown = comparator.render_markdown(comparison)

    assert "# Database Pool Topology Comparison" in markdown
    assert "Runtime-verified pool budgets" in markdown
    assert (
        "did not produce a lower average end-to-end "
        "foreground p95"
        in markdown
    )
    assert (
        "not a general claim that isolated pools always improve "
        "overall response time"
        in markdown
    )
