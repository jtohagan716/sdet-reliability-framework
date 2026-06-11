from framework.reliability.synthetic_journeys import (
    CREATE_AND_SIGN_ENCOUNTER,
    OPEN_APPOINTMENT_MODULE,
)


def test_create_and_sign_encounter_journey():
    journey = CREATE_AND_SIGN_ENCOUNTER

    assert journey.name == "create_and_sign_encounter"
    assert journey.role == "PROVIDER"
    assert journey.signal_source == "SYNTHETIC_BACKEND_CANARY"
    assert journey.step_count() == 3


def test_open_appointment_module_journey():
    journey = OPEN_APPOINTMENT_MODULE

    assert journey.name == "open_appointment_module"
    assert journey.role == "CLERK"
    assert journey.signal_source == "SYNTHETIC_UI_CANARY"
    assert journey.step_count() == 2