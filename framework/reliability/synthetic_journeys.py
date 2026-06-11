from framework.reliability.synthetic_journey import (
    SyntheticJourney,
    SyntheticStep,
)


CREATE_AND_SIGN_ENCOUNTER = SyntheticJourney(
    name="create_and_sign_encounter",
    role="PROVIDER",
    description=(
        "Synthetic journey representing a provider workflow from encounter "
        "creation through encounter signing."
    ),
    signal_source="SYNTHETIC_BACKEND_CANARY",
    steps=[
        SyntheticStep(
            name="create_encounter",
            action="Create a new patient encounter",
            expected_result="Encounter is created successfully",
        ),
        SyntheticStep(
            name="document_encounter",
            action="Add clinical documentation",
            expected_result="Documentation is saved successfully",
        ),
        SyntheticStep(
            name="sign_encounter",
            action="Sign the encounter",
            expected_result="Encounter is signed successfully",
        ),
    ],
)


OPEN_APPOINTMENT_MODULE = SyntheticJourney(
    name="open_appointment_module",
    role="CLERK",
    description=(
        "Synthetic journey representing opening the appointment module "
        "and validating schedule visibility."
    ),
    signal_source="SYNTHETIC_UI_CANARY",
    steps=[
        SyntheticStep(
            name="open_appointment_module",
            action="Open appointment module",
            expected_result="Appointment module loads successfully",
        ),
        SyntheticStep(
            name="validate_schedule",
            action="Verify appointment schedule is visible",
            expected_result="Schedule is displayed successfully",
        ),
    ],
)