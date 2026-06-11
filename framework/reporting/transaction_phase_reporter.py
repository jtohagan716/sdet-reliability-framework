def print_transaction_phase_report(analysis: dict):
    print("\n==================================================")
    print("TRANSACTION PHASE ANALYSIS")
    print("==================================================")

    print(f"Total Transaction Time: {analysis['total_elapsed_ms']} ms")
    print("")

    print("PHASE CONTRIBUTIONS")
    print("-------------------")

    for phase in analysis["phase_contributions"]:
        print(
            f"{phase['phase']} | "
            f"Component: {phase['component']} | "
            f"Elapsed: {phase['elapsed_ms']} ms | "
            f"Contribution: {phase['percent_of_total']}% | "
            f"Status: {phase['status']}"
        )

    print("")
    print("PRIMARY BOTTLENECK")
    print("------------------")
    print(f"Phase: {analysis['slowest_phase']}")
    print(f"Component: {analysis['slowest_component']}")
    print("")

    print("RECOMMENDATION")
    print("--------------")
    print(analysis["recommendation"])

    print("==================================================")