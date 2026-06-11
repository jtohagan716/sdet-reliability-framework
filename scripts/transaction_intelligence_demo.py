from framework.reliability.transaction_roadmaps import OPEN_APPOINTMENT
from framework.reliability.transaction_evaluator import (
    evaluate_transaction_variant,
)

from framework.reliability.transaction_phase import (
    TransactionPhase,
)

from framework.reliability.transaction_phase_analyzer import (
    analyze_transaction_phases,
)

from framework.reporting.transaction_phase_reporter import (
    print_transaction_phase_report,
)


print()
print("==================================================")
print("TRANSACTION INTELLIGENCE DEMO")
print("==================================================")
print()

# ------------------------------------
# Transaction Variant
# ------------------------------------

variant = OPEN_APPOINTMENT.get_variant("current_day")

evaluation = evaluate_transaction_variant(
    variant=variant,
    observed_ms=425,
)

print("TRANSACTION")
print("------------------")
print(OPEN_APPOINTMENT.name)
print()

print("VARIANT")
print("------------------")
print(evaluation["variant"])
print()

print("WORKLOAD")
print("------------------")
print(evaluation["workload_profile"])
print()

print("BASELINE")
print("------------------")
print(f'{evaluation["baseline_ms"]} ms')
print()

print("OBSERVED")
print("------------------")
print(f'{evaluation["observed_ms"]} ms')
print()

print("STATUS")
print("------------------")
print(evaluation["status"])
print()

print("RECOMMENDATION")
print("------------------")
print(evaluation["recommendation"])
print()

# ------------------------------------
# Transaction Phases
# ------------------------------------

phases = [

    TransactionPhase(
        "local_cache_lookup",
        "ICD",
        25,
    ),

    TransactionPhase(
        "central_repository_lookup",
        "CDR",
        125,
    ),

    TransactionPhase(
        "response_assembly",
        "CLIENT",
        10,
    ),

]

analysis = analyze_transaction_phases(phases)

print_transaction_phase_report(analysis)