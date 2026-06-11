from datetime import datetime

from framework.reliability.synthetic_journeys import (
    CREATE_AND_SIGN_ENCOUNTER,
    OPEN_APPOINTMENT_MODULE,
)

from framework.reliability.transaction_roadmaps import OPEN_APPOINTMENT
from framework.reliability.transaction_evaluator import evaluate_transaction_variant
from framework.reliability.transaction_phase import TransactionPhase
from framework.reliability.transaction_phase_analyzer import analyze_transaction_phases
from framework.reliability.transaction_dependencies import (
    build_open_appointment_dependency_graph,
)
from framework.reliability.investigation_planner import create_investigation_plan
from framework.reliability.incident_timeline import IncidentTimeline, TimelineEvent
from framework.reliability.evidence_correlator import correlate_evidence
from framework.reliability.incident_state_engine import determine_incident_state


def print_header(title):
    print("\n==================================================")
    print(title)
    print("==================================================")


def main():
    print_header("SDET RELIABILITY FRAMEWORK DEMO")

    print("Synthetic Journeys")
    print("------------------")
    print(f"{CREATE_AND_SIGN_ENCOUNTER.name} | Role: {CREATE_AND_SIGN_ENCOUNTER.role} | Steps: {CREATE_AND_SIGN_ENCOUNTER.step_count()}")
    print(f"{OPEN_APPOINTMENT_MODULE.name} | Role: {OPEN_APPOINTMENT_MODULE.role} | Steps: {OPEN_APPOINTMENT_MODULE.step_count()}")

    print_header("TRANSACTION EVALUATION")

    variant = OPEN_APPOINTMENT.get_variant("current_day")

    transaction_result = evaluate_transaction_variant(
        variant=variant,
        observed_ms=425,
    )

    print(f"Transaction: {OPEN_APPOINTMENT.name}")
    print(f"Variant: {transaction_result['variant']}")
    print(f"Workload: {transaction_result['workload_profile']}")
    print(f"Baseline: {transaction_result['baseline_ms']} ms")
    print(f"Observed: {transaction_result['observed_ms']} ms")
    print(f"Status: {transaction_result['status']}")
    print(f"Recommendation: {transaction_result['recommendation']}")

    print_header("TRANSACTION PHASE ANALYSIS")

    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    phase_analysis = analyze_transaction_phases(phases)

    print(f"Total Elapsed: {phase_analysis['total_elapsed_ms']} ms")
    print(f"Slowest Phase: {phase_analysis['slowest_phase']}")
    print(f"Slowest Component: {phase_analysis['slowest_component']}")
    print(f"Recommendation: {phase_analysis['recommendation']}")

    print_header("INVESTIGATION PLAN")

    graph = build_open_appointment_dependency_graph()

    plan = create_investigation_plan(
        analysis=phase_analysis,
        dependency_graph=graph,
    )

    print(f"Primary Component: {plan['primary_component']}")
    print(f"Investigation Targets: {', '.join(plan['investigation_targets'])}")
    print(f"Recommendation: {plan['recommendation']}")

    print_header("INCIDENT TIMELINE AND EVIDENCE CORRELATION")

    timeline = IncidentTimeline()

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 5),
            source="ARM_CLIENT",
            signal_type="CLIENT_TIMING",
            severity="WARN",
            message="Open Appointment latency exceeded baseline.",
        )
    )

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 6),
            source="TUXEDO_EMH",
            signal_type="MIDDLEWARE_ERROR",
            severity="ERROR",
            message="Error recorded by Error Message Handler.",
        )
    )

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 7),
            source="CDRPLUS.ERROR_LOG",
            signal_type="APPLICATION_ERROR",
            severity="ERROR",
            message="Open Appointment application error detected.",
        )
    )

    correlation = correlate_evidence(timeline)

    print(f"Evidence Sources: {', '.join(correlation['sources'])}")
    print(f"Source Count: {correlation['source_count']}")
    print(f"Confidence: {correlation['confidence']}")

    print_header("INCIDENT STATE")

    incident = determine_incident_state(
        enterprise_wide=True,
        single_mtf=False,
        single_provider=False,
        slow_component="CDR",
    )

    print(f"State: {incident.state}")
    print(f"Severity: {incident.severity}")
    print(f"Scope: {incident.scope}")
    print(f"Confidence: {incident.confidence}")
    print(f"Primary Owner: {incident.primary_owner}")

    print_header("FRAMEWORK DEMO COMPLETE")


if __name__ == "__main__":
    main()