from framework.reliability.transaction_phase import TransactionPhase
from framework.reliability.transaction_phase_analyzer import analyze_transaction_phases
from framework.reliability.transaction_dependencies import (
    build_open_appointment_dependency_graph,
)
from framework.reliability.investigation_planner import create_investigation_plan


def test_investigation_plan_uses_slowest_component_dependencies():
    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    analysis = analyze_transaction_phases(phases)
    graph = build_open_appointment_dependency_graph()

    plan = create_investigation_plan(analysis, graph)

    assert plan["primary_component"] == "CDR"
    assert plan["investigation_targets"] == [
        "ORACLE",
        "TUXEDO",
        "NETWORK",
    ]
    assert "ORACLE" in plan["recommendation"]