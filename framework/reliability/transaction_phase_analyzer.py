def calculate_total_elapsed(phases):
    return sum(phase.elapsed_ms for phase in phases)


def find_slowest_phase(phases):
    if not phases:
        return None

    return max(phases, key=lambda phase: phase.elapsed_ms)


def calculate_phase_contributions(phases):
    total = calculate_total_elapsed(phases)

    if total == 0:
        return []

    contributions = []

    for phase in phases:
        percent = (phase.elapsed_ms / total) * 100

        contributions.append(
            {
                "phase": phase.name,
                "component": phase.component,
                "elapsed_ms": phase.elapsed_ms,
                "percent_of_total": round(percent, 2),
                "status": phase.status,
            }
        )

    return contributions


def analyze_transaction_phases(phases):
    total = calculate_total_elapsed(phases)
    slowest = find_slowest_phase(phases)
    contributions = calculate_phase_contributions(phases)

    if slowest is None:
        return {
            "total_elapsed_ms": 0,
            "slowest_phase": None,
            "slowest_component": None,
            "phase_contributions": [],
            "recommendation": "No transaction phases available for analysis.",
        }

    recommendation = (
        f"Investigate {slowest.component} dependency. "
        f"Phase '{slowest.name}' is the largest contributor to transaction latency."
    )

    return {
        "total_elapsed_ms": total,
        "slowest_phase": slowest.name,
        "slowest_component": slowest.component,
        "phase_contributions": contributions,
        "recommendation": recommendation,
    }