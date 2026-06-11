def create_investigation_plan(analysis: dict, dependency_graph) -> dict:
    slowest_component = analysis.get("slowest_component")

    if slowest_component is None:
        return {
            "primary_component": None,
            "investigation_targets": [],
            "recommendation": "No bottleneck available for investigation planning.",
        }

    targets = dependency_graph.get_investigation_priority(slowest_component)

    if not targets:
        return {
            "primary_component": slowest_component,
            "investigation_targets": [],
            "recommendation": (
                f"No dependency guidance available for {slowest_component}."
            ),
        }

    return {
        "primary_component": slowest_component,
        "investigation_targets": targets,
        "recommendation": (
            f"Investigate {slowest_component} by reviewing: "
            + ", ".join(targets)
        ),
    }