from framework.reliability.transaction_roadmaps import OPEN_APPOINTMENT


def test_open_appointment_has_expected_variants():
    assert OPEN_APPOINTMENT.name == "open_appointment"

    current_day = OPEN_APPOINTMENT.get_variant("current_day")
    current_week = OPEN_APPOINTMENT.get_variant("current_week")
    current_month = OPEN_APPOINTMENT.get_variant("current_month")

    assert current_day.workload_profile == "LOW"
    assert current_week.workload_profile == "MEDIUM"
    assert current_month.workload_profile == "HIGH"

    assert current_day.baseline_ms < current_week.baseline_ms
    assert current_week.baseline_ms < current_month.baseline_ms