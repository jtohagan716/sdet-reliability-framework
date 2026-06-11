from framework.reliability.dependency_graph import (
    DependencyGraph,
    DependencyNode,
)


def build_open_appointment_dependency_graph():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            name="open_appointment",
            depends_on=["ICD", "CDR", "CLIENT"],
            investigation_priority=["CDR", "ICD", "CLIENT"],
        )
    )

    graph.add_node(
        DependencyNode(
            name="CDR",
            depends_on=["TUXEDO", "ORACLE", "NETWORK"],
            investigation_priority=["ORACLE", "TUXEDO", "NETWORK"],
        )
    )

    graph.add_node(
        DependencyNode(
            name="ICD",
            depends_on=["IIS", "WINDOWS", "ICD_DATABASE"],
            investigation_priority=["IIS", "ICD_DATABASE", "WINDOWS"],
        )
    )

    graph.add_node(
        DependencyNode(
            name="CLIENT",
            depends_on=["RENDERING", "LOCAL_CONFIG", "NETWORK"],
            investigation_priority=["LOCAL_CONFIG", "RENDERING", "NETWORK"],
        )
    )

    return graph