"""Utility functions for dependency graph operations."""

from .dependency_graph import DependencyGraph


def build_graph_from_dict(spec: dict) -> DependencyGraph:
    """Build a DependencyGraph from a dictionary specification.

    Args:
        spec: Mapping of node -> list of dependencies.
              Example: {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}

    Returns:
        A populated DependencyGraph.
    """
    graph = DependencyGraph()
    for node, deps in spec.items():
        graph.add_node(node)
        for dep in deps:
            graph.add_dependency(node, dep)
    return graph


def find_roots(graph: DependencyGraph) -> set:
    """Find nodes with no dependencies (entry points)."""
    all_nodes = graph.get_all_nodes()
    return {n for n in all_nodes if not graph.get_dependencies(n)}


def find_leaves(graph: DependencyGraph) -> set:
    """Find nodes that nothing depends on (exit points)."""
    all_nodes = graph.get_all_nodes()
    return {n for n in all_nodes if not graph.get_dependents(n)}


def get_all_transitive_dependencies(graph: DependencyGraph, node: str) -> set:
    """Get all transitive dependencies of a node (recursive)."""
    result = set()
    _collect_deps(graph, node, result)
    return result


def _collect_deps(graph, node, result):
    for dep in graph.get_dependencies(node):
        if dep not in result:
            result.add(dep)
            _collect_deps(graph, dep, result)
