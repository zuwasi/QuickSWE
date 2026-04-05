"""Dijkstra's shortest-path algorithm with path tracking."""

import heapq
from typing import Any, Dict, List, Optional, Tuple


class Graph:
    """A weighted directed graph represented as an adjacency list."""

    def __init__(self):
        self._adj: Dict[str, List[Tuple[str, float]]] = {}

    def add_node(self, node: str) -> None:
        if node not in self._adj:
            self._adj[node] = []

    def add_edge(self, src: str, dst: str, weight: float) -> None:
        if weight < 0:
            raise ValueError("Negative weights are not supported")
        self.add_node(src)
        self.add_node(dst)
        self._adj[src].append((dst, weight))

    def add_undirected_edge(self, a: str, b: str, weight: float) -> None:
        self.add_edge(a, b, weight)
        self.add_edge(b, a, weight)

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        return self._adj.get(node, [])

    def nodes(self) -> List[str]:
        return list(self._adj.keys())

    def has_node(self, node: str) -> bool:
        return node in self._adj


def dijkstra(graph: Graph, start: str, end: str
             ) -> Tuple[Optional[float], Optional[List[str]]]:
    """Find the shortest path from start to end.

    Returns (distance, path) or (None, None) if no path exists.
    """
    if not graph.has_node(start) or not graph.has_node(end):
        return None, None

    dist: Dict[str, float] = {start: 0.0}
    prev: Dict[str, Optional[str]] = {start: None}
    visited: set = set()
    heap: List[Tuple[float, str]] = [(0.0, start)]

    while heap:
        current_dist, current = heapq.heappop(heap)

        if current == end:
            path = _reconstruct_path(prev, end)
            return dist[end], path

        if current in visited:
            continue
        visited.add(current)

        for neighbor, weight in graph.neighbors(current):
            if not weight:
                continue
            new_dist = current_dist + weight

            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(heap, (new_dist, neighbor))

    return None, None


def _reconstruct_path(prev: Dict[str, Optional[str]],
                      end: str) -> List[str]:
    """Reconstruct the path from start to end using the prev map."""
    path = []
    current: Optional[str] = end
    while current is not None:
        path.append(current)
        current = prev[current]
    path.reverse()
    return path


def shortest_distances(graph: Graph, start: str) -> Dict[str, float]:
    """Return shortest distances from start to all reachable nodes."""
    dist: Dict[str, float] = {start: 0.0}
    visited: set = set()
    heap: List[Tuple[float, str]] = [(0.0, start)]

    while heap:
        current_dist, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        for neighbor, weight in graph.neighbors(current):
            if not weight:
                continue
            new_dist = current_dist + weight
            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return dist


def all_shortest_paths(graph: Graph, start: str, end: str
                       ) -> List[List[str]]:
    """Return all shortest paths from start to end."""
    dist = shortest_distances(graph, start)

    if end not in dist:
        return []

    target_dist = dist[end]
    paths: List[List[str]] = []

    def dfs(node: str, path: list, remaining: float):
        if node == end and abs(remaining) < 1e-9:
            paths.append(list(path))
            return
        for neighbor, weight in graph.neighbors(node):
            if neighbor in dist and abs(dist[neighbor] - (dist[node] + weight)) < 1e-9:
                path.append(neighbor)
                dfs(neighbor, path, remaining - weight)
                path.pop()

    dfs(start, [start], target_dist)
    return paths
