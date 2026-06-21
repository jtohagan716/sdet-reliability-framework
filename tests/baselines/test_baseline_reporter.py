from framework.baselines.baseline_manager import evaluate_latency
from framework.baselines.baseline_reporter import print_baseline_report


def test_baseline_reporter_outputs_analysis():

    result = evaluate_latency(
        current_ms=84,
        baseline_ms=100,
    )

    print_baseline_report(result)

    assert result["status"] == "HEALTHY"