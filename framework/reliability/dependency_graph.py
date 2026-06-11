from dataclasses import dataclass


@dataclass
class DependencyNode:
    name: str
    depends_on: list[str]
    investigation_priority: list[str]


class DependencyGraph:

    def __init__(self):
        self.nodes = {}

    def add_node(self, node: DependencyNode):
        self.nodes[node.name] = node

    def get_node(self, name: str):
        return self.nodes.get(name)

    def get_dependencies(self, name: str):
        node = self.get_node(name)

        if node is None:
            return []

        return node.depends_on

    def get_investigation_priority(self, name: str):
        node = self.get_node(name)

        if node is None:
            return []

        return node.investigation_priority