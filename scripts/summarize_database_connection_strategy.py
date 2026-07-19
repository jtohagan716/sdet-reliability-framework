from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIRECTORY = ROOT / "reports" / "test-runs"

OUTPUT_JSON = (
    ROOT
    / "reports"
    / "database-connection-strategy-summary.json"
)

OUTPUT_MARKDOWN = (
    ROOT
    / "docs"
    / "database-connection-study-results.md"
)

RUNS = (
    {
        "configuration": "direct",
        "strategy": "connection_per_operation",
        "run_id": (
            "database-connection-direct-warm-"
            "20260713T040803565352Z"
        ),
    },
    {
        "configuration": "direct",
        "strategy": "connection_per_operation",
        "run_id": (
            "database-connection-direct-warm-"
            "20260713T040820256959Z"
        ),
    },
    {
        "configuration": "direct",
        "strategy": "connection_per_operation",
        "run_id": (
            "database-connection-direct-warm-"
            "20260713T040914257042Z"
        ),
    },
    {
        "configuration": "dynamic-4-8",
        "strategy": "bounded_pool",
        "run_id": (
            "database-connection-dynamic-4-8-warm-"
            "20260713T034133134290Z"
        ),
    },
    {
        "configuration": "dynamic-4-8",
        "strategy": "bounded_pool",
        "run_id": (
            "database-connection-dynamic-4-8-warm-"
            "20260713T034758812402Z"
        ),
    },
    {
        "configuration": "dynamic-4-8",
        "strategy": "bounded_pool",
        "run_id": (
            "database-connection-dynamic-4-8-warm-"
            "20260713T035004463609Z"
        ),
    },
    {
        "configuration": "fixed-8",
        "strategy": "bounded_pool",
        "run_id": (
            "database-connection-fixed-8-warm-"
            "20260713T034327375212Z"
        ),
    },
    {
        "configuration": "fixed-8",
        "strategy": "bounded_pool",
        "run_id": (
            "database-connection-fixed-8-warm-"
            "20260713T034512016994Z"
        ),
    },
    {
        "configuration": "fixed-8",
        "strategy": "bounded_pool",
        "run_id": (
            "database-connection-fixed-8-warm-"
            "20260713T035143063941Z"
        ),
    },
)

CONFIGURATIONS = (
    "direct",
    "dynamic-4-8",
    "fixed-8",
)

METRICS = {
    "throughput_rps": (
        "requests_per_second",
    ),
    "client_mean_ms": (
        "metrics",
        "client_elapsed_ms",
        "mean_ms",
    ),
    "client_p95_ms": (
        "metrics",
        "client_elapsed_ms",
        "p95_ms",
    ),
    "acquire_mean_ms": (
        "metrics",
        "acquire_ms",
        "mean_ms",
    ),
    "acquire_p95_ms": (
        "metrics",
        "acquire_ms",
        "p95_ms",
    ),
    "database_total_mean_ms": (
        "metrics",
        "total_ms",
        "mean_ms",
    ),
    "database_total_p95_ms": (
        "metrics",
        "total_ms",
        "p95_ms",
    ),
}


def nested_value(
    data: dict[str, Any],
    path: tuple[str, ...],
) -> Any:
    value: Any = data

    for key in path:
        value = value[key]

    return value


def median(values: list[float]) -> float:
    return round(statistics.median(values), 3)


def percentage_gain(
    comparison: float,
    baseline: float,
) -> float:
    return round(
        ((comparison / baseline) - 1.0) * 100,
        3,
    )


def percentage_reduction(
    comparison: float,
    baseline: float,
) -> float:
    return round(
        (1.0 - (comparison / baseline)) * 100,
        3,
    )


def load_runs() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for definition in RUNS:
        run_id = definition["run_id"]
        summary_path = (
            RUN_DIRECTORY
            / run_id
            / "summary.json"
        )

        if not summary_path.exists():
            raise FileNotFoundError(
                f"Missing run summary: {summary_path}"
            )

        summary = json.loads(
            summary_path.read_text(encoding="utf-8")
        )

        expectations = {
            "run_id": run_id,
            "configuration_label": (
                definition["configuration"]
            ),
            "strategy": definition["strategy"],
            "mode": "warm",
            "request_count": 200,
            "concurrency": 20,
            "success_count": 200,
            "failure_count": 0,
        }

        for field_name, expected in expectations.items():
            actual = summary.get(field_name)

            if actual != expected:
                raise RuntimeError(
                    f"{run_id}: expected {field_name}="
                    f"{expected!r}, received {actual!r}"
                )

        result: dict[str, Any] = {
            "run_id": run_id,
            "configuration": (
                definition["configuration"]
            ),
            "strategy": definition["strategy"],
        }

        for metric_name, metric_path in METRICS.items():
            result[metric_name] = float(
                nested_value(summary, metric_path)
            )

        pool = summary.get("pool_observations")

        result["peak_waiters"] = (
            None
            if pool is None
            else int(
                pool["maximum_requests_waiting"]
            )
        )

        results.append(result)

    return results


def aggregate_configuration(
    runs: list[dict[str, Any]],
    configuration: str,
) -> dict[str, Any]:
    selected = [
        run
        for run in runs
        if run["configuration"] == configuration
    ]

    if len(selected) != 3:
        raise RuntimeError(
            f"Expected 3 {configuration} runs, "
            f"found {len(selected)}"
        )

    result: dict[str, Any] = {
        "configuration": configuration,
        "run_count": len(selected),
        "run_ids": [
            run["run_id"]
            for run in selected
        ],
    }

    for metric_name in METRICS:
        values = [
            float(run[metric_name])
            for run in selected
        ]

        result[metric_name] = {
            "median": median(values),
            "minimum": round(min(values), 3),
            "maximum": round(max(values), 3),
        }

    waiter_values = [
        float(run["peak_waiters"])
        for run in selected
        if run["peak_waiters"] is not None
    ]

    result["peak_waiters"] = (
        None
        if not waiter_values
        else {
            "median": median(waiter_values),
            "minimum": round(min(waiter_values), 3),
            "maximum": round(max(waiter_values), 3),
        }
    )

    return result


def compare_with_direct(
    pooled: dict[str, Any],
    direct: dict[str, Any],
) -> dict[str, float]:
    return {
        "throughput_gain_percent": percentage_gain(
            pooled["throughput_rps"]["median"],
            direct["throughput_rps"]["median"],
        ),
        "client_p95_reduction_percent": (
            percentage_reduction(
                pooled["client_p95_ms"]["median"],
                direct["client_p95_ms"]["median"],
            )
        ),
        "acquire_p95_reduction_percent": (
            percentage_reduction(
                pooled["acquire_p95_ms"]["median"],
                direct["acquire_p95_ms"]["median"],
            )
        ),
        "database_total_p95_reduction_percent": (
            percentage_reduction(
                pooled[
                    "database_total_p95_ms"
                ]["median"],
                direct[
                    "database_total_p95_ms"
                ]["median"],
            )
        ),
    }


def main() -> None:
    runs = load_runs()

    aggregates = {
        configuration: aggregate_configuration(
            runs,
            configuration,
        )
        for configuration in CONFIGURATIONS
    }

    direct = aggregates["direct"]
    dynamic = aggregates["dynamic-4-8"]
    fixed = aggregates["fixed-8"]

    comparisons = {
        "dynamic_4_8_relative_to_direct": (
            compare_with_direct(dynamic, direct)
        ),
        "fixed_8_relative_to_direct": (
            compare_with_direct(fixed, direct)
        ),
        "fixed_8_relative_to_dynamic_4_8": {
            "throughput_gain_percent": percentage_gain(
                fixed["throughput_rps"]["median"],
                dynamic["throughput_rps"]["median"],
            ),
            "client_p95_reduction_percent": (
                percentage_reduction(
                    fixed["client_p95_ms"]["median"],
                    dynamic["client_p95_ms"]["median"],
                )
            ),
            "acquire_p95_reduction_percent": (
                percentage_reduction(
                    fixed["acquire_p95_ms"]["median"],
                    dynamic["acquire_p95_ms"]["median"],
                )
            ),
            "database_total_p95_reduction_percent": (
                percentage_reduction(
                    fixed[
                        "database_total_p95_ms"
                    ]["median"],
                    dynamic[
                        "database_total_p95_ms"
                    ]["median"],
                )
            ),
        },
    }

    output = {
        "study_valid": True,
        "repetitions_per_configuration": 3,
        "request_count_per_run": 200,
        "concurrency": 20,
        "runs": runs,
        "aggregates": aggregates,
        "comparisons": comparisons,
    }

    OUTPUT_JSON.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Database Connection Strategy Study",
        "",
        "## Test design",
        "",
        "- Warm steady-state workload",
        "- 200 requests per run",
        "- 20 concurrent workers",
        "- Three repetitions per configuration",
        "- Zero request failures across all nine runs",
        "- Median used for configuration comparisons",
        "",
        "## Median results",
        "",
        (
            "| Configuration | Throughput | Client mean | "
            "Client p95 | Acquire mean | Acquire p95 | "
            "DB total mean | DB total p95 |"
        ),
        (
            "|---|---:|---:|---:|---:|---:|---:|---:|"
        ),
    ]

    for configuration in CONFIGURATIONS:
        values = aggregates[configuration]

        lines.append(
            "| "
            f"{configuration} | "
            f"{values['throughput_rps']['median']} | "
            f"{values['client_mean_ms']['median']} | "
            f"{values['client_p95_ms']['median']} | "
            f"{values['acquire_mean_ms']['median']} | "
            f"{values['acquire_p95_ms']['median']} | "
            f"{values['database_total_mean_ms']['median']} | "
            f"{values['database_total_p95_ms']['median']} |"
        )

    dynamic_comparison = comparisons[
        "dynamic_4_8_relative_to_direct"
    ]

    fixed_comparison = comparisons[
        "fixed_8_relative_to_direct"
    ]

    lines.extend(
        [
            "",
            "## Pooled strategies relative to direct",
            "",
            "### Dynamic 4-8",
            "",
            (
                "- Throughput gain: "
                f"{dynamic_comparison['throughput_gain_percent']}%"
            ),
            (
                "- Client p95 reduction: "
                f"{dynamic_comparison['client_p95_reduction_percent']}%"
            ),
            (
                "- Acquire p95 reduction: "
                f"{dynamic_comparison['acquire_p95_reduction_percent']}%"
            ),
            (
                "- Database-total p95 reduction: "
                f"{dynamic_comparison['database_total_p95_reduction_percent']}%"
            ),
            "",
            "### Fixed 8",
            "",
            (
                "- Throughput gain: "
                f"{fixed_comparison['throughput_gain_percent']}%"
            ),
            (
                "- Client p95 reduction: "
                f"{fixed_comparison['client_p95_reduction_percent']}%"
            ),
            (
                "- Acquire p95 reduction: "
                f"{fixed_comparison['acquire_p95_reduction_percent']}%"
            ),
            (
                "- Database-total p95 reduction: "
                f"{fixed_comparison['database_total_p95_reduction_percent']}%"
            ),
            "",
            "## Decision",
            "",
            (
                "Use the bounded connection pool for the application "
                "workload. Creating one physical PostgreSQL connection "
                "per operation was the dominant database cost under "
                "concurrency."
            ),
            "",
            (
                "Retain a dynamic minimum of 4 and maximum of 8 as the "
                "project default. Fixed 8 did not demonstrate a clean "
                "database-latency advantage and permanently consumes "
                "four additional idle PostgreSQL sessions."
            ),
            "",
            "## Limitations",
            "",
            (
                "- Results apply to this local containerized workload "
                "and synthetic patient lookup."
            ),
            (
                "- Host scheduling and container contention introduced "
                "visible run-to-run variation."
            ),
            (
                "- The warm-up can grow the dynamic pool before the "
                "measured workload, so this study does not prove the "
                "optimal minimum pool size."
            ),
            (
                "- Production pool sizing must also account for API "
                "replica count and the PostgreSQL connection budget."
            ),
        ]
    )

    markdown = "\n".join(lines) + "\n"

    OUTPUT_MARKDOWN.write_text(
        markdown,
        encoding="utf-8",
    )

    print(markdown)
    print(f"JSON: {OUTPUT_JSON}")
    print(f"Markdown: {OUTPUT_MARKDOWN}")


if __name__ == "__main__":
    main()
