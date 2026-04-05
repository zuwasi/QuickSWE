"""Topological sort using DFS with cycle detection."""

from typing import Any, Dict, List, Optional, Set


class CyclicGraphError(Exception):
    """Raised when the graph contains a cycle."""
    pass


def topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """Return a topological ordering of nodes in a directed acyclic graph.

    Args:
        graph: Adjacency list mapping node -> list of nodes it depends on
               (i.e. edges point from a node to its dependencies).

    Returns:
        A list where every node appears after its dependencies.

    Raises:
        CyclicGraphError: if the graph contains a cycle.
    """
    all_nodes: Set[str] = set(graph.keys())
    for deps in graph.values():
        for dep in deps:
            all_nodes.add(dep)

    visited: Set[str] = set()
    result: List[str] = []

    def dfs(node: str):
        if node in visited:
            return
        visited.add(node)

        for dep in graph.get(node, []):
            dfs(dep)

        result.append(node)

    for node in sorted(all_nodes):
        if node not in visited:
            dfs(node)

    return result


def topological_sort_kahn(graph: Dict[str, List[str]]) -> List[str]:
    """Kahn's algorithm (BFS-based) topological sort.

    Args:
        graph: Adjacency list mapping node -> list of nodes it depends on.
    """
    all_nodes: Set[str] = set(graph.keys())
    for deps in graph.values():
        for dep in deps:
            all_nodes.add(dep)

    in_degree: Dict[str, int] = {n: 0 for n in all_nodes}
    reverse: Dict[str, List[str]] = {n: [] for n in all_nodes}

    for node, deps in graph.items():
        for dep in deps:
            reverse[dep].append(node)
            in_degree[node] += 1

    queue = sorted([n for n in all_nodes if in_degree[n] == 0])
    result: List[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for dependent in sorted(reverse.get(node, [])):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
        queue.sort()

    if len(result) != len(all_nodes):
        raise CyclicGraphError("Graph contains a cycle")

    return result


def dependency_levels(graph: Dict[str, List[str]]
                      ) -> List[List[str]]:
    """Group nodes into levels where each level depends only on prior levels."""
    order = topological_sort(graph)

    all_nodes: Set[str] = set(graph.keys())
    for deps in graph.values():
        for dep in deps:
            all_nodes.add(dep)

    node_level: Dict[str, int] = {}
    for node in order:
        deps = graph.get(node, [])
        if not deps:
            node_level[node] = 0
        else:
            node_level[node] = max(node_level.get(d, 0) for d in deps) + 1

    max_level = max(node_level.values()) if node_level else 0
    levels: List[List[str]] = [[] for _ in range(max_level + 1)]
    for node, level in node_level.items():
        levels[level].append(node)

    return [sorted(level) for level in levels if level]


def is_dag(graph: Dict[str, List[str]]) -> bool:
    """Return True if the graph is a DAG."""
    try:
        topological_sort(graph)
        return True
    except CyclicGraphError:
        return False
