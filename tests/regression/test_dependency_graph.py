from framework.reliability.dependency_graph import (
    DependencyGraph,
    DependencyNode,
)

from framework.reliability.transaction_dependencies import (
    build_open_appointment_dependency_graph,
)


def test_dependency_graph_returns_dependencies():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            name="CDR",
            depends_on=["TUXEDO", "ORACLE", "NETWORK"],
            investigation_priority=["ORACLE", "TUXEDO", "NETWORK"],
        )
    )

    assert graph.get_dependencies("CDR") == [
        "TUXEDO",
        "ORACLE",
        "NETWORK",
    ]


def test_dependency_graph_returns_investigation_priority():
    graph = DependencyGraph()

    graph.add_node(
        DependencyNode(
            name="ICD",
            depends_on=["IIS", "WINDOWS", "ICD_DATABASE"],
            investigation_priority=["IIS", "ICD_DATABASE", "WINDOWS"],
        )
    )

    assert graph.get_investigation_priority("ICD") == [
        "IIS",
        "ICD_DATABASE",
        "WINDOWS",
    ]


def test_open_appointment_dependency_graph_contains_cdr_path():
    graph = build_open_appointment_dependency_graph()

    assert graph.get_dependencies("open_appointment") == [
        "ICD",
        "CDR",
        "CLIENT",
    ]

    assert graph.get_investigation_priority("CDR") == [
        "ORACLE",
        "TUXEDO",
        "NETWORK",
    ]