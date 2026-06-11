from framework.reliability.transaction_phase import TransactionPhase
from framework.reliability.transaction_phase_analyzer import analyze_transaction_phases
from framework.reporting.transaction_phase_reporter import print_transaction_phase_report


def test_transaction_phase_reporter_outputs_analysis(capsys):
    phases = [
        TransactionPhase("local_cache_lookup", "ICD", 25),
        TransactionPhase("central_repository_lookup", "CDR", 125),
        TransactionPhase("response_assembly", "CLIENT", 10),
    ]

    analysis = analyze_transaction_phases(phases)

    print_transaction_phase_report(analysis)

    captured = capsys.readouterr()

    assert "TRANSACTION PHASE ANALYSIS" in captured.out
    assert "PRIMARY BOTTLENECK" in captured.out
    assert "central_repository_lookup" in captured.out
    assert "CDR" in captured.out
    assert "RECOMMENDATION" in captured.out