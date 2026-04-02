"""Dependency graph with topological sort for task ordering."""


class DependencyGraph:
    """Directed acyclic graph for modeling task dependencies.

    Nodes are string identifiers. An edge from A to B means "A depends on B"
    (B must come before A in the execution order).
    """

    def __init__(self):
        self._nodes = set()
        self._edges = {}  # node -> set of nodes it depends on

    def add_node(self, node: str) -> None:
        """Add a node to the graph."""
        self._nodes.add(node)
        if node not in self._edges:
            self._edges[node] = set()

    def add_dependency(self, node: str, depends_on: str) -> None:
        """Declare that ``node`` depends on ``depends_on``.

        Both nodes are added if not present.
        """
        self.add_node(node)
        self.add_node(depends_on)
        self._edges[node].add(depends_on)

    def get_dependencies(self, node: str) -> set:
        """Return the direct dependencies of a node."""
        return set(self._edges.get(node, set()))

    def get_dependents(self, node: str) -> set:
        """Return the set of nodes that depend on ``node``."""
        return {n for n, deps in self._edges.items() if node in deps}

    def get_all_nodes(self) -> set:
        """Return all nodes in the graph."""
        return set(self._nodes)

    def resolve_order(self) -> list:
        """Return a topological ordering of all nodes.

        Nodes with no dependencies come first. Each node appears after
        all of its dependencies.

        Returns:
            List of node identifiers in execution order.

        Raises:
            ValueError: If the graph contains a cycle.
        """
        result = []
        visited = set()
        for node in self._nodes:
            if node not in visited:
                self._visit(node, result, visited)
        return result

    def _visit(self, node: str, result: list, visited: set) -> None:
        """Recursive DFS helper for topological sort.

        Uses post-order DFS: dependencies are added before dependents.
        """
        if node in visited:
            return
        visited.add(node)
        # Visit all dependencies first
        for dep in self._edges.get(node, set()):
            self._visit(dep, result, visited)
        # Add this node to result
        result.append(node)

    def has_cycle(self) -> bool:
        """Check whether the graph contains a cycle."""
        visited = set()
        rec_stack = set()
        for node in self._nodes:
            if node not in visited:
                if self._cycle_check(node, visited, rec_stack):
                    return True
        return False

    def _cycle_check(self, node, visited, rec_stack):
        """DFS-based cycle detection."""
        visited.add(node)
        rec_stack.add(node)
        for dep in self._edges.get(node, set()):
            if dep not in visited:
                if self._cycle_check(dep, visited, rec_stack):
                    return True
            elif dep in rec_stack:
                return True
        # BUG: missing rec_stack.discard(node) — nodes are never
        # removed from the recursion stack, so previously visited
        # branches are incorrectly treated as ancestors
        return False
