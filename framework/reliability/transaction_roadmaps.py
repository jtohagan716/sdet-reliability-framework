from framework.reliability.transaction_model import (
    TransactionDefinition,
    TransactionVariant,
)


OPEN_APPOINTMENT = TransactionDefinition(
    name="open_appointment",
    description=(
        "Models the Open Appointment module as a transaction family. "
        "Performance expectations vary based on user-selected date range, "
        "provider scope, and expected appointment volume."
    ),
    variants=[
        TransactionVariant(
            name="current_day",
            workload_profile="LOW",
            expected_volume="single day appointment schedule",
            baseline_ms=300,
        ),
        TransactionVariant(
            name="current_week",
            workload_profile="MEDIUM",
            expected_volume="weekly appointment schedule",
            baseline_ms=900,
        ),
        TransactionVariant(
            name="current_month",
            workload_profile="HIGH",
            expected_volume="monthly appointment schedule",
            baseline_ms=2500,
        ),
    ],
)