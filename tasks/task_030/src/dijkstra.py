"""Dijkstra's shortest path algorithm."""

from .priority_queue import MinHeap


def dijkstra(graph, source, target=None):
    """Find shortest paths from source to all nodes (or a specific target).

    Returns:
        distances: dict mapping node -> shortest distance from source
        predecessors: dict mapping node -> previous node on shortest path
    """
    dist = {}
    prev = {}
    pq = MinHeap()
    finalized = set()

    dist[source] = 0
    prev[source] = None
    pq.insert(0, source)

    while not pq.is_empty:
        current_dist, u = pq.extract_min()

        if u in finalized:
            continue
        finalized.add(u)

        if target is not None and u == target:
            break

        for neighbor, weight in graph.neighbors(u):
            new_dist = dist[u] + weight

            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = u
                pq.insert(new_dist, neighbor)

    return dist, prev


def reconstruct_path(predecessors, target):
    """Reconstruct the shortest path from predecessors dict."""
    if target not in predecessors:
        return None

    path = []
    current = target
    visited = set()
    while current is not None:
        if current in visited:
            return None  # cycle detection
        visited.add(current)
        path.append(current)
        current = predecessors.get(current)

    path.reverse()
    return path


def shortest_path(graph, source, target):
    """Find the shortest path between two nodes.

    Returns (distance, path) or (infinity, None) if no path exists.
    """
    dist, prev = dijkstra(graph, source, target)

    if target not in dist:
        return float('inf'), None

    path = reconstruct_path(prev, target)
    return dist[target], path


def all_shortest_paths(graph, source):
    """Find shortest paths from source to all reachable nodes.

    Returns dict mapping node -> (distance, path).
    """
    dist, prev = dijkstra(graph, source)
    result = {}

    for node in dist:
        path = reconstruct_path(prev, node)
        result[node] = (dist[node], path)

    return result
