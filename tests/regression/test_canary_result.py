from framework.reliability.canary_result import CanaryResult


def test_canary_result():
    result = CanaryResult(
        journey_name="create_and_sign_encounter",
        status="PASS",
        duration_ms=450,
        signal="HEALTHY",
        recommendation="No action required.",
    )

    assert result.status == "PASS"
    assert result.signal == "HEALTHY"
    assert result.duration_ms == 450