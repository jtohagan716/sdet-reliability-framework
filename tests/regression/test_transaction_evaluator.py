from framework.reliability.transaction_roadmaps import OPEN_APPOINTMENT
from framework.reliability.transaction_evaluator import evaluate_transaction_variant


def test_transaction_variant_healthy_when_under_baseline():
    variant = OPEN_APPOINTMENT.get_variant("current_day")

    result = evaluate_transaction_variant(
        variant=variant,
        observed_ms=250,
    )

    assert result["status"] == "HEALTHY"
    assert result["baseline_ms"] == 300


def test_transaction_variant_degraded_when_over_baseline():
    variant = OPEN_APPOINTMENT.get_variant("current_day")

    result = evaluate_transaction_variant(
        variant=variant,
        observed_ms=425,
    )

    assert result["status"] == "DEGRADED"
    assert result["percent_over_baseline"] > 25