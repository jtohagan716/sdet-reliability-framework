from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


EXPECTED_RUNS_PER_TOPOLOGY = 3
SHARED_POOL = "shared_pool"
ISOLATED_POOLS = "isolated_pools"

DEFAULT_JSON_OUTPUT = Path(
    "reports/database-pool-topology-comparison.json"
)
DEFAULT_MARKDOWN_OUTPUT = Path(
    "reports/database_pool_topology_comparison.md"
)


def nested_value(
    source: dict[str, Any],
    *path: str,
) -> Any:
    """Return a required value from a nested report structure."""

    current: Any = source

    for key in path:
        if not isinstance(current, dict) or key not in current:
            joined_path = ".".join(path)
            raise ValueError(
                f"Report is missing required field: {joined_path}"
            )

        current = current[key]

    return current


def load_report(path: Path) -> dict[str, Any]:
    """Load one workload report from JSON."""

    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(
            f"Report does not exist: {path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Report contains invalid JSON: {path}"
        ) from error

    if not isinstance(report, dict):
        raise ValueError(
            f"Report root must be a JSON object: {path}"
        )

    return report


def validate_runtime_pool_configuration(
    report: dict[str, Any],
    *,
    expected_topology: str,
) -> dict[str, Any]:
    """Validate the runtime-reported physical pool budget."""

    runtime_configuration = nested_value(
        report,
        "observed_pool_configuration",
    )

    if not isinstance(runtime_configuration, dict):
        raise ValueError(
            "observed_pool_configuration must be an object"
        )

    unique_pools: dict[str, dict[str, Any]] = {}

    for workload_type in ("foreground", "background"):
        pool_configuration = runtime_configuration.get(
            workload_type
        )

        if not isinstance(pool_configuration, dict):
            raise ValueError(
                f"Runtime {workload_type} pool configuration "
                "is unavailable"
            )

        pool_name = str(
            pool_configuration.get("pool_name", "")
        ).strip()

        if not pool_name:
            raise ValueError(
                f"Runtime {workload_type} pool name is unavailable"
            )

        normalized_configuration = {
            "pool_name": pool_name,
            "min_size": int(
                pool_configuration["min_size"]
            ),
            "max_size": int(
                pool_configuration["max_size"]
            ),
            "timeout_seconds": float(
                pool_configuration["timeout_seconds"]
            ),
            "startup_timeout_seconds": float(
                pool_configuration[
                    "startup_timeout_seconds"
                ]
            ),
            "max_waiting": int(
                pool_configuration["max_waiting"]
            ),
        }

        existing = unique_pools.get(pool_name)

        if (
            existing is not None
            and existing != normalized_configuration
        ):
            raise ValueError(
                f"Pool {pool_name!r} has conflicting runtime "
                "configurations"
            )

        unique_pools[pool_name] = normalized_configuration

    expected_pool_count = (
        1 if expected_topology == SHARED_POOL else 2
    )

    if len(unique_pools) != expected_pool_count:
        raise ValueError(
            f"Topology {expected_topology!r} should report "
            f"{expected_pool_count} physical pool(s), but reported "
            f"{len(unique_pools)}"
        )

    calculated_minimum = sum(
        int(configuration["min_size"])
        for configuration in unique_pools.values()
    )
    calculated_maximum = sum(
        int(configuration["max_size"])
        for configuration in unique_pools.values()
    )

    reported_pool_count = int(
        runtime_configuration["unique_pool_count"]
    )
    reported_minimum = int(
        runtime_configuration["combined_min_size"]
    )
    reported_maximum = int(
        runtime_configuration["combined_max_size"]
    )

    if reported_pool_count != len(unique_pools):
        raise ValueError(
            "Reported unique pool count does not match the "
            "runtime pool configurations"
        )

    if reported_minimum != calculated_minimum:
        raise ValueError(
            "Reported combined minimum pool size does not match "
            "the runtime pool configurations"
        )

    if reported_maximum != calculated_maximum:
        raise ValueError(
            "Reported combined maximum pool size does not match "
            "the runtime pool configurations"
        )

    return {
        "foreground": runtime_configuration["foreground"],
        "background": runtime_configuration["background"],
        "unique_pool_count": reported_pool_count,
        "combined_min_size": reported_minimum,
        "combined_max_size": reported_maximum,
    }


def validate_report(
    report: dict[str, Any],
    *,
    expected_topology: str,
) -> None:
    """Reject incomplete or invalid experimental evidence."""

    run_id = str(report.get("run_id", "")).strip()

    if not run_id:
        raise ValueError("Report contains no run_id")

    expected = report.get("expected_pool_topology")
    observed = report.get("observed_pool_topology")

    if expected != expected_topology:
        raise ValueError(
            f"Run {run_id} expected topology {expected!r}, "
            f"not {expected_topology!r}"
        )

    if observed != expected_topology:
        raise ValueError(
            f"Run {run_id} observed topology {observed!r}, "
            f"not {expected_topology!r}"
        )

    failure_count = int(
        nested_value(
            report,
            "summary",
            "total_failure_count",
        )
    )

    if failure_count != 0:
        raise ValueError(
            f"Run {run_id} contains {failure_count} request "
            "failure(s)"
        )

    fatal_error = str(
        nested_value(
            report,
            "execution",
            "fatal_error",
        )
        or ""
    ).strip()

    if fatal_error:
        raise ValueError(
            f"Run {run_id} contains a fatal error: {fatal_error}"
        )

    cleanup_error = str(
        report.get("cleanup_error", "") or ""
    ).strip()

    if cleanup_error:
        raise ValueError(
            f"Run {run_id} contains a cleanup error: "
            f"{cleanup_error}"
        )

    configuration = report.get("configuration")

    if not isinstance(configuration, dict):
        raise ValueError(
            f"Run {run_id} contains no workload configuration"
        )

    foreground_expected = int(
        nested_value(
            configuration,
            "foreground",
            "request_count",
        )
    )
    background_expected = int(
        nested_value(
            configuration,
            "background",
            "request_count",
        )
    )

    foreground_observed = int(
        nested_value(
            report,
            "summary",
            "foreground",
            "request_count",
        )
    )
    background_observed = int(
        nested_value(
            report,
            "summary",
            "background",
            "request_count",
        )
    )

    if foreground_observed != foreground_expected:
        raise ValueError(
            f"Run {run_id} foreground request count does not "
            "match its workload configuration"
        )

    if background_observed != background_expected:
        raise ValueError(
            f"Run {run_id} background request count does not "
            "match its workload configuration"
        )

    validate_runtime_pool_configuration(
        report,
        expected_topology=expected_topology,
    )


def validate_report_group(
    reports: list[dict[str, Any]],
    *,
    expected_topology: str,
) -> None:
    """Validate one complete topology trial group."""

    if len(reports) != EXPECTED_RUNS_PER_TOPOLOGY:
        raise ValueError(
            f"Expected {EXPECTED_RUNS_PER_TOPOLOGY} "
            f"{expected_topology} reports, received "
            f"{len(reports)}"
        )

    run_ids: set[str] = set()

    for report in reports:
        validate_report(
            report,
            expected_topology=expected_topology,
        )

        run_id = str(report["run_id"])

        if run_id in run_ids:
            raise ValueError(
                f"Duplicate report supplied: {run_id}"
            )

        run_ids.add(run_id)


def workload_signature(
    report: dict[str, Any],
) -> str:
    """Return a canonical representation of workload parameters."""

    configuration = nested_value(
        report,
        "configuration",
    )

    return json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
    )


def extract_run_metrics(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Extract one run's comparison measurements."""

    return {
        "run_id": report["run_id"],
        "elapsed_seconds": float(
            nested_value(
                report,
                "execution",
                "elapsed_seconds",
            )
        ),
        "foreground_p50_ms": float(
            nested_value(
                report,
                "summary",
                "foreground",
                "metrics",
                "client_elapsed_ms",
                "p50_ms",
            )
        ),
        "foreground_p95_ms": float(
            nested_value(
                report,
                "summary",
                "foreground",
                "metrics",
                "client_elapsed_ms",
                "p95_ms",
            )
        ),
        "foreground_acquire_p95_ms": float(
            nested_value(
                report,
                "summary",
                "foreground",
                "metrics",
                "database_acquire_ms",
                "p95_ms",
            )
        ),
        "foreground_later_average_ms": float(
            nested_value(
                report,
                "summary",
                "request_phases",
                "foreground",
                "later_requests",
                "average_client_ms",
            )
        ),
        "background_p95_ms": float(
            nested_value(
                report,
                "summary",
                "background",
                "metrics",
                "client_elapsed_ms",
                "p95_ms",
            )
        ),
        "foreground_peak_requests_waiting": int(
            nested_value(
                report,
                "summary",
                "foreground",
                "pool_observations",
                "peak_requests_waiting",
            )
        ),
    }


def rounded_mean(values: list[float]) -> float:
    """Return a consistently rounded arithmetic mean."""

    return round(statistics.fmean(values), 3)


def aggregate_runs(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate comparable measurements across repeated runs."""

    runs = [
        extract_run_metrics(report)
        for report in reports
    ]

    numeric_metrics = (
        "elapsed_seconds",
        "foreground_p50_ms",
        "foreground_p95_ms",
        "foreground_acquire_p95_ms",
        "foreground_later_average_ms",
        "background_p95_ms",
    )

    means: dict[str, float] = {}
    ranges: dict[str, dict[str, float]] = {}

    for metric_name in numeric_metrics:
        values = [
            float(run[metric_name])
            for run in runs
        ]

        means[metric_name] = rounded_mean(values)
        ranges[metric_name] = {
            "minimum": round(min(values), 3),
            "maximum": round(max(values), 3),
        }

    return {
        "run_count": len(runs),
        "means": means,
        "ranges": ranges,
        "foreground_waiting_trial_count": sum(
            1
            for run in runs
            if int(
                run["foreground_peak_requests_waiting"]
            )
            > 0
        ),
        "runs": runs,
    }


def percent_change(
    baseline: float,
    comparison: float,
) -> float | None:
    """Return comparison change relative to baseline."""

    if baseline == 0:
        return None

    return round(
        ((comparison - baseline) / baseline) * 100,
        3,
    )


def build_comparison(
    *,
    shared_reports: list[dict[str, Any]],
    isolated_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate and compare shared versus isolated pool evidence."""

    validate_report_group(
        shared_reports,
        expected_topology=SHARED_POOL,
    )
    validate_report_group(
        isolated_reports,
        expected_topology=ISOLATED_POOLS,
    )

    all_reports = shared_reports + isolated_reports
    signatures = {
        workload_signature(report)
        for report in all_reports
    }

    if len(signatures) != 1:
        raise ValueError(
            "Reports do not use an identical workload configuration"
        )

    runtime_configurations = [
        validate_runtime_pool_configuration(
            report,
            expected_topology=(
                SHARED_POOL
                if report["observed_pool_topology"]
                == SHARED_POOL
                else ISOLATED_POOLS
            ),
        )
        for report in all_reports
    ]

    combined_minimum_sizes = {
        int(configuration["combined_min_size"])
        for configuration in runtime_configurations
    }
    combined_maximum_sizes = {
        int(configuration["combined_max_size"])
        for configuration in runtime_configurations
    }

    if len(combined_minimum_sizes) != 1:
        raise ValueError(
            "Reports do not use an equal combined minimum "
            "connection budget"
        )

    if len(combined_maximum_sizes) != 1:
        raise ValueError(
            "Reports do not use an equal combined maximum "
            "connection budget"
        )

    shared = aggregate_runs(shared_reports)
    isolated = aggregate_runs(isolated_reports)

    shared_means = shared["means"]
    isolated_means = isolated["means"]

    metric_changes = {
        metric_name: percent_change(
            float(shared_means[metric_name]),
            float(isolated_means[metric_name]),
        )
        for metric_name in shared_means
    }

    shared_acquire = float(
        shared_means["foreground_acquire_p95_ms"]
    )
    isolated_acquire = float(
        isolated_means["foreground_acquire_p95_ms"]
    )

    acquire_reduction_percent = (
        round(
            (
                (shared_acquire - isolated_acquire)
                / shared_acquire
            )
            * 100,
            3,
        )
        if shared_acquire > 0
        else None
    )

    shared_runtime = validate_runtime_pool_configuration(
        shared_reports[0],
        expected_topology=SHARED_POOL,
    )
    isolated_runtime = validate_runtime_pool_configuration(
        isolated_reports[0],
        expected_topology=ISOLATED_POOLS,
    )

    return {
        "study": {
            "name": (
                "Shared versus isolated PostgreSQL "
                "connection pools"
            ),
            "runs_per_topology": EXPECTED_RUNS_PER_TOPOLOGY,
            "total_run_count": len(all_reports),
            "workload_configuration": shared_reports[0][
                "configuration"
            ],
            "equal_connection_budget": {
                "combined_min_size": next(
                    iter(combined_minimum_sizes)
                ),
                "combined_max_size": next(
                    iter(combined_maximum_sizes)
                ),
            },
        },
        "runtime_pool_configurations": {
            SHARED_POOL: shared_runtime,
            ISOLATED_POOLS: isolated_runtime,
        },
        "results": {
            SHARED_POOL: shared,
            ISOLATED_POOLS: isolated,
            "isolated_vs_shared_percent_change": (
                metric_changes
            ),
            "foreground_acquire_p95_reduction_percent": (
                acquire_reduction_percent
            ),
        },
        "findings": {
            "isolated_reduced_foreground_acquisition": (
                isolated_acquire < shared_acquire
            ),
            "isolated_reduced_waiting_trials": (
                isolated[
                    "foreground_waiting_trial_count"
                ]
                < shared[
                    "foreground_waiting_trial_count"
                ]
            ),
            "isolated_reduced_foreground_p95": (
                isolated_means["foreground_p95_ms"]
                < shared_means["foreground_p95_ms"]
            ),
        },
        "source_run_ids": {
            SHARED_POOL: [
                report["run_id"]
                for report in shared_reports
            ],
            ISOLATED_POOLS: [
                report["run_id"]
                for report in isolated_reports
            ],
        },
    }


def markdown_number(value: float | int | None) -> str:
    """Format a numeric Markdown table value."""

    if value is None:
        return "n/a"

    if isinstance(value, int):
        return str(value)

    return f"{value:.3f}"


def render_markdown(
    comparison: dict[str, Any],
) -> str:
    """Render a human-readable comparison report."""

    study = comparison["study"]
    results = comparison["results"]
    shared = results[SHARED_POOL]
    isolated = results[ISOLATED_POOLS]
    shared_means = shared["means"]
    isolated_means = isolated["means"]
    changes = results[
        "isolated_vs_shared_percent_change"
    ]
    findings = comparison["findings"]
    runtime = comparison[
        "runtime_pool_configurations"
    ]
    workload = study["workload_configuration"]

    lines = [
        "# Database Pool Topology Comparison",
        "",
        "## Study design",
        "",
        (
            "- Repeated measured runs per topology: "
            f"{study['runs_per_topology']}"
        ),
        (
            "- Combined connection budget: "
            f"minimum {study['equal_connection_budget']['combined_min_size']}, "
            f"maximum {study['equal_connection_budget']['combined_max_size']}"
        ),
        (
            "- Foreground requests per run: "
            f"{workload['foreground']['request_count']}"
        ),
        (
            "- Foreground concurrency: "
            f"{workload['foreground']['concurrency']}"
        ),
        (
            "- Foreground connection hold: "
            f"{workload['foreground']['connection_hold_ms']} ms"
        ),
        (
            "- Background requests per run: "
            f"{workload['background']['request_count']}"
        ),
        (
            "- Background concurrency: "
            f"{workload['background']['concurrency']}"
        ),
        (
            "- Background batch size: "
            f"{workload['background']['batch_size']}"
        ),
        "",
        "## Runtime-verified pool budgets",
        "",
        "| Topology | Physical pools | Foreground max | "
        "Background max | Combined max |",
        "|---|---:|---:|---:|---:|",
        (
            "| Shared pool | "
            f"{runtime[SHARED_POOL]['unique_pool_count']} | "
            f"{runtime[SHARED_POOL]['foreground']['max_size']} | "
            f"{runtime[SHARED_POOL]['background']['max_size']} | "
            f"{runtime[SHARED_POOL]['combined_max_size']} |"
        ),
        (
            "| Isolated pools | "
            f"{runtime[ISOLATED_POOLS]['unique_pool_count']} | "
            f"{runtime[ISOLATED_POOLS]['foreground']['max_size']} | "
            f"{runtime[ISOLATED_POOLS]['background']['max_size']} | "
            f"{runtime[ISOLATED_POOLS]['combined_max_size']} |"
        ),
        "",
        "The shared foreground and background values refer to the "
        "same physical pool and are counted once in the combined budget.",
        "",
        "## Three-run averages",
        "",
        "| Metric | Shared pool | Isolated pools | "
        "Isolated vs. shared |",
        "|---|---:|---:|---:|",
    ]

    metric_rows = (
        (
            "Elapsed seconds",
            "elapsed_seconds",
        ),
        (
            "Foreground p50 ms",
            "foreground_p50_ms",
        ),
        (
            "Foreground p95 ms",
            "foreground_p95_ms",
        ),
        (
            "Foreground acquire p95 ms",
            "foreground_acquire_p95_ms",
        ),
        (
            "Foreground later-request average ms",
            "foreground_later_average_ms",
        ),
        (
            "Background p95 ms",
            "background_p95_ms",
        ),
    )

    for label, metric_name in metric_rows:
        change = changes[metric_name]
        formatted_change = (
            "n/a"
            if change is None
            else f"{change:+.3f}%"
        )

        lines.append(
            f"| {label} | "
            f"{markdown_number(shared_means[metric_name])} | "
            f"{markdown_number(isolated_means[metric_name])} | "
            f"{formatted_change} |"
        )

    lines.extend(
        [
            (
                "| Trials with observed foreground waiting | "
                f"{shared['foreground_waiting_trial_count']} | "
                f"{isolated['foreground_waiting_trial_count']} | "
                "— |"
            ),
            "",
            "## Per-run measurements",
            "",
            "| Topology | Run ID | Foreground p50 ms | "
            "Foreground p95 ms | Acquire p95 ms | "
            "Background p95 ms | Foreground waiting peak |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )

    for topology, topology_results in (
        (SHARED_POOL, shared),
        (ISOLATED_POOLS, isolated),
    ):
        for run in topology_results["runs"]:
            lines.append(
                f"| `{topology}` | `{run['run_id']}` | "
                f"{run['foreground_p50_ms']:.3f} | "
                f"{run['foreground_p95_ms']:.3f} | "
                f"{run['foreground_acquire_p95_ms']:.3f} | "
                f"{run['background_p95_ms']:.3f} | "
                f"{run['foreground_peak_requests_waiting']} |"
            )

    acquire_reduction = results[
        "foreground_acquire_p95_reduction_percent"
    ]

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "With the same runtime-verified maximum budget of "
                f"{study['equal_connection_budget']['combined_max_size']} "
                "PostgreSQL connections, isolated pools "
                f"reduced average foreground acquisition p95 by "
                f"{markdown_number(acquire_reduction)}%."
            ),
            (
                "Observed foreground waiting occurred in "
                f"{shared['foreground_waiting_trial_count']} of "
                f"{shared['run_count']} shared-pool trials and "
                f"{isolated['foreground_waiting_trial_count']} of "
                f"{isolated['run_count']} isolated-pool trials."
            ),
        ]
    )

    if findings["isolated_reduced_foreground_p95"]:
        lines.append(
            "The isolation benefit also produced a lower average "
            "end-to-end foreground p95 under this workload."
        )
    else:
        lines.append(
            "The isolation benefit did not produce a lower average "
            "end-to-end foreground p95 under this workload."
        )

    lines.extend(
        [
            "",
            "The evidence supports a workload-isolation conclusion, "
            "not a general claim that isolated pools always improve "
            "overall response time.",
            "",
            "## Limitations",
            "",
            "- The study used a local Windows and Docker environment.",
            "- Each topology was measured in three formal runs.",
            "- The workload was synthetic and intentionally controlled.",
            "- Pool waiting counters are sampled runtime observations.",
            "- Results should not be generalized to unrelated workloads.",
            "",
            "## Source runs",
            "",
            "### Shared pool",
            "",
        ]
    )

    for run_id in comparison["source_run_ids"][SHARED_POOL]:
        lines.append(f"- `{run_id}`")

    lines.extend(
        [
            "",
            "### Isolated pools",
            "",
        ]
    )

    for run_id in comparison[
        "source_run_ids"
    ][ISOLATED_POOLS]:
        lines.append(f"- `{run_id}`")

    lines.append("")

    return "\n".join(lines)


def write_comparison_artifacts(
    comparison: dict[str, Any],
    *,
    json_output: Path,
    markdown_output: Path,
) -> None:
    """Write deterministic JSON and Markdown comparison artifacts."""

    json_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    markdown_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_output.write_text(
        json.dumps(
            comparison,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    markdown_output.write_text(
        render_markdown(comparison),
        encoding="utf-8",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line report paths and output destinations."""

    parser = argparse.ArgumentParser(
        description=(
            "Compare repeated shared-pool and isolated-pool "
            "mixed-workload reports."
        )
    )
    parser.add_argument(
        "--shared-report",
        action="append",
        required=True,
        type=Path,
        help=(
            "Path to one formal shared-pool run-report.json. "
            "Specify exactly three times."
        ),
    )
    parser.add_argument(
        "--isolated-report",
        action="append",
        required=True,
        type=Path,
        help=(
            "Path to one formal isolated-pools run-report.json. "
            "Specify exactly three times."
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=DEFAULT_MARKDOWN_OUTPUT,
    )

    return parser.parse_args()


def main() -> int:
    """Load reports, validate the experiment, and write evidence."""

    arguments = parse_arguments()

    comparison = build_comparison(
        shared_reports=[
            load_report(path)
            for path in arguments.shared_report
        ],
        isolated_reports=[
            load_report(path)
            for path in arguments.isolated_report
        ],
    )

    write_comparison_artifacts(
        comparison,
        json_output=arguments.json_output,
        markdown_output=arguments.markdown_output,
    )

    print("Database pool topology comparison generated.")
    print("JSON:", arguments.json_output)
    print("Markdown:", arguments.markdown_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
