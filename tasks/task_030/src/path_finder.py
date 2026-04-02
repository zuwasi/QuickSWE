"""PathFinder combining graph construction and shortest path queries."""

from .graph import WeightedGraph
from .dijkstra import shortest_path, all_shortest_paths


class PathFinder:
    """High-level API for finding shortest paths in weighted graphs."""

    def __init__(self):
        self._graph = WeightedGraph()
        self._path_cache = {}
        self._distance_overrides = {}

    @property
    def graph(self):
        return self._graph

    def add_road(self, city1, city2, distance, bidirectional=True):
        """Add a road between two cities.

        BUG: When adding a road, we also store a "distance override" that
        maps (city1, city2) -> distance. This was meant for direct edge
        lookup optimization. But when bidirectional=True, we only store
        the override for (city1, city2), not (city2, city1). This doesn't
        affect the graph itself (which correctly has both edges), but it
        affects find_shortest_path when the override is used.

        Actually, the REAL bug is more subtle: the distance_overrides are
        checked in find_shortest_path BEFORE running Dijkstra. If a direct
        edge exists between source and target, we return the direct edge
        weight as a "shortcut" without checking if there's a shorter path
        through intermediate nodes. This is wrong for graphs where the
        indirect path is shorter than the direct edge.
        """
        if bidirectional:
            self._graph.add_undirected_edge(city1, city2, distance)
        else:
            self._graph.add_edge(city1, city2, distance)
        # Store direct distance for "fast lookup"
        self._distance_overrides[(city1, city2)] = distance
        if bidirectional:
            self._distance_overrides[(city2, city1)] = distance
        self._path_cache.clear()

    def add_roads(self, roads):
        """Add multiple roads. Each road is (city1, city2, distance, bidirectional?)."""
        for road in roads:
            if len(road) == 3:
                city1, city2, dist = road
                self.add_road(city1, city2, dist)
            else:
                city1, city2, dist, bidir = road
                self.add_road(city1, city2, dist, bidir)

    def find_shortest_path(self, source, target):
        """Find the shortest path between source and target.

        Returns:
            (distance, path_list) or (inf, None) if no path exists

        BUG: Checks distance_overrides first as a "fast path" optimization.
        If a direct edge exists from source to target, returns that distance
        immediately without running Dijkstra. This is wrong when the shortest
        path goes through intermediate nodes and is shorter than the direct edge.
        """
        cache_key = (source, target)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        # BUG: "Optimization" that shortcuts Dijkstra for direct edges.
        # This returns the direct edge weight even when a shorter indirect
        # path exists through other nodes.
        if cache_key in self._distance_overrides:
            direct_dist = self._distance_overrides[cache_key]
            result = (direct_dist, [source, target])
            self._path_cache[cache_key] = result
            return result

        result = shortest_path(self._graph, source, target)
        self._path_cache[cache_key] = result
        return result

    def find_all_from(self, source):
        """Find shortest paths from source to all reachable nodes."""
        return all_shortest_paths(self._graph, source)

    def is_reachable(self, source, target):
        """Check if target is reachable from source."""
        dist, _ = self.find_shortest_path(source, target)
        return dist < float('inf')

    def get_distance(self, source, target):
        """Get just the distance (no path)."""
        dist, _ = self.find_shortest_path(source, target)
        return dist

    def get_path(self, source, target):
        """Get just the path (no distance)."""
        _, path = self.find_shortest_path(source, target)
        return path

    def find_nearest(self, source, targets):
        """Find the nearest target from a set of targets."""
        best_dist = float('inf')
        best_target = None
        best_path = None

        for target in targets:
            dist, path = self.find_shortest_path(source, target)
            if dist < best_dist:
                best_dist = dist
                best_target = target
                best_path = path

        return best_target, best_dist, best_path

    def clear_cache(self):
        """Clear the path cache."""
        self._path_cache.clear()

    def summary(self):
        """Return a summary of the graph."""
        return {
            'nodes': self._graph.node_count,
            'edges': self._graph.edge_count,
            'cached_paths': len(self._path_cache),
        }

    def __repr__(self):
        return (
            f"PathFinder(nodes={self._graph.node_count}, "
            f"edges={self._graph.edge_count})"
        )
