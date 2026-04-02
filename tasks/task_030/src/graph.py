"""Weighted graph implementation."""

from collections import defaultdict


class Edge:
    """Represents a weighted edge in a graph."""

    def __init__(self, source, target, weight=1.0):
        if weight < 0:
            raise ValueError(f"Edge weight must be non-negative, got {weight}")
        self.source = source
        self.target = target
        self.weight = weight

    def __repr__(self):
        return f"Edge({self.source} -> {self.target}, w={self.weight})"


class WeightedGraph:
    """Weighted directed graph using adjacency list representation."""

    def __init__(self):
        self._adjacency = defaultdict(list)
        self._nodes = set()
        self._edge_count = 0

    @property
    def node_count(self):
        return len(self._nodes)

    @property
    def edge_count(self):
        return self._edge_count

    def add_node(self, node):
        """Add a node to the graph."""
        self._nodes.add(node)

    def add_edge(self, source, target, weight=1.0):
        """Add a directed edge from source to target with given weight.

        BUG: Does not check for duplicate edges. If add_edge is called
        multiple times with the same source/target, multiple edges are
        created. This is intentional for multigraphs but causes issues
        when add_undirected_edge is used (see below).
        """
        self._nodes.add(source)
        self._nodes.add(target)
        edge = Edge(source, target, weight)
        self._adjacency[source].append(edge)
        self._edge_count += 1

    def add_undirected_edge(self, node1, node2, weight=1.0):
        """Add an undirected edge (two directed edges).

        BUG: This calls add_edge twice, which is correct. But there's
        a subtle issue: if called multiple times with the same nodes
        but different weights, ALL edges are kept. The neighbors()
        method returns all of them, and Dijkstra processes all of them.
        This isn't the main bug though — the main bug is in dijkstra.py.
        """
        self.add_edge(node1, node2, weight)
        self.add_edge(node2, node1, weight)

    def neighbors(self, node):
        """Return list of (neighbor, weight) tuples for a node."""
        return [(e.target, e.weight) for e in self._adjacency.get(node, [])]

    def edges_from(self, node):
        """Return all edges from a node."""
        return list(self._adjacency.get(node, []))

    def has_node(self, node):
        """Check if a node exists."""
        return node in self._nodes

    def has_edge(self, source, target):
        """Check if an edge exists."""
        for edge in self._adjacency.get(source, []):
            if edge.target == target:
                return True
        return False

    def get_weight(self, source, target):
        """Get the weight of an edge."""
        for edge in self._adjacency.get(source, []):
            if edge.target == target:
                return edge.weight
        raise ValueError(f"No edge from {source} to {target}")

    def nodes(self):
        """Return all nodes."""
        return set(self._nodes)

    def all_edges(self):
        """Return all edges."""
        edges = []
        for source in self._adjacency:
            edges.extend(self._adjacency[source])
        return edges

    def degree(self, node):
        """Return the out-degree of a node."""
        return len(self._adjacency.get(node, []))

    def reverse(self):
        """Return a new graph with all edges reversed."""
        g = WeightedGraph()
        for edge in self.all_edges():
            g.add_edge(edge.target, edge.source, edge.weight)
        return g

    def __repr__(self):
        return f"WeightedGraph(nodes={self.node_count}, edges={self.edge_count})"
