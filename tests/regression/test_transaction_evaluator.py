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
    assert result["recommendation"] == "No action required."


def test_transaction_variant_degraded_when_over_baseline():
    variant = OPEN_APPOINTMENT.get_variant("current_day")

    result = evaluate_transaction_variant(
        variant=variant,
        observed_ms=425,
    )

    assert result["status"] == "DEGRADED"
    assert result["percent_over_baseline"] > 25
    assert "roadmap phases" in result["recommendation"]


def test_transaction_variant_severely_degraded_when_far_over_baseline():
    variant = OPEN_APPOINTMENT.get_variant("current_day")

    result = evaluate_transaction_variant(
        variant=variant,
        observed_ms=700,
    )

    assert result["status"] == "SEVERELY_DEGRADED"
    assert "immediate review" in result["recommendation"]