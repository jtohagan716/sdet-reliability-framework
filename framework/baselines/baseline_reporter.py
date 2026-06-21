def print_baseline_report(result: dict) -> None:

    print("")
    print("================================")
    print("BASELINE ANALYSIS")
    print("================================")
    print(f"Current  : {result['currentMs']} ms")
    print(f"Baseline : {result['baselineMs']} ms")
    print(f"Ratio    : {result['ratio']}")
    print(f"Status   : {result['status']}")
    print("================================")
    print("")