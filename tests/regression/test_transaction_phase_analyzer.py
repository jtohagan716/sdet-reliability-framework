from framework.reliability.transaction_phase import TransactionPhase
from framework.reliability.transaction_phase_analyzer import (
    calculate_total_elapsed,
    find_slowest_phase,
    calculate_phase_contributions,
    analyze_transaction_phases,
)


def test_calculate_total_elapsed():
    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    assert calculate_total_elapsed(phases) == 160


def test_find_slowest_phase():
    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    slowest = find_slowest_phase(phases)

    assert slowest.name == "central_repository_lookup"
    assert slowest.component == "CDR"


def test_calculate_phase_contributions():
    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    contributions = calculate_phase_contributions(phases)

    cdr = next(
        item for item in contributions
        if item["component"] == "CDR"
    )

    assert cdr["percent_of_total"] == 78.12


def test_analyze_transaction_phases_identifies_bottleneck():
    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    result = analyze_transaction_phases(phases)

    assert result["total_elapsed_ms"] == 160
    assert result["slowest_phase"] == "central_repository_lookup"
    assert result["slowest_component"] == "CDR"
    assert "CDR" in result["recommendation"]