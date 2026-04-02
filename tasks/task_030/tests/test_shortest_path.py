"""Tests for shortest path algorithm."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import WeightedGraph
from src.dijkstra import dijkstra, shortest_path, reconstruct_path
from src.priority_queue import MinHeap
from src.path_finder import PathFinder
from src.visualizer import GraphVisualizer


@pytest.mark.fail_to_pass
class TestPathFinderCorrectness:
    """Tests that verify PathFinder produces correct shortest paths.

    These tests FAIL because PathFinder has a "fast path" optimization
    that returns the direct edge weight between source and target without
    running Dijkstra. This is incorrect when the shortest path goes through
    intermediate nodes and is shorter than the direct edge.
    """

    def test_indirect_path_shorter_than_direct(self):
        """When indirect path is shorter than direct edge, should return indirect."""
        pf = PathFinder()

        # Direct A -> C costs 10
        pf.add_road('A', 'C', 10, bidirectional=False)
        # Indirect A -> B -> C costs 2 + 3 = 5
        pf.add_road('A', 'B', 2, bidirectional=False)
        pf.add_road('B', 'C', 3, bidirectional=False)

        dist, path = pf.find_shortest_path('A', 'C')

        assert dist == 5, (
            f"Expected shortest distance 5 (A->B->C), got {dist}. "
            f"PathFinder returned the direct edge weight instead of the "
            f"actual shortest path distance."
        )
        assert path == ['A', 'B', 'C'], f"Expected path A->B->C, got {path}"

    def test_triangle_inequality_violation(self):
        """In a triangle, the indirect 2-hop path can be shorter than the direct edge."""
        pf = PathFinder()

        # Triangle: X-Y-Z with edges:
        # X->Y: 1, Y->Z: 1, X->Z: 5 (direct is worse)
        pf.add_road('X', 'Y', 1, bidirectional=False)
        pf.add_road('Y', 'Z', 1, bidirectional=False)
        pf.add_road('X', 'Z', 5, bidirectional=False)

        dist, path = pf.find_shortest_path('X', 'Z')

        assert dist == 2, (
            f"Expected distance 2 (X->Y->Z), got {dist}. "
            f"Direct edge X->Z with weight 5 was incorrectly used."
        )

    def test_complex_network_with_shortcut(self):
        """Complex network where direct edge exists but indirect is shorter."""
        pf = PathFinder()

        # Build network
        pf.add_road('start', 'end', 100, bidirectional=False)  # Direct but expensive
        pf.add_road('start', 'A', 1, bidirectional=False)
        pf.add_road('A', 'B', 1, bidirectional=False)
        pf.add_road('B', 'C', 1, bidirectional=False)
        pf.add_road('C', 'end', 1, bidirectional=False)

        dist, path = pf.find_shortest_path('start', 'end')

        assert dist == 4, (
            f"Expected distance 4 (start->A->B->C->end), got {dist}. "
            f"The direct edge start->end with weight 100 was used instead."
        )
        assert path == ['start', 'A', 'B', 'C', 'end'], f"Wrong path: {path}"

    def test_bidirectional_with_shortcut(self):
        """Bidirectional edges where indirect path is shorter."""
        pf = PathFinder()

        # Bidirectional triangle
        pf.add_road('P', 'Q', 1)  # bidirectional
        pf.add_road('Q', 'R', 1)  # bidirectional
        pf.add_road('P', 'R', 10)  # bidirectional, direct but expensive

        dist, path = pf.find_shortest_path('P', 'R')

        assert dist == 2, (
            f"Expected distance 2 (P->Q->R), got {dist}. "
            f"Bidirectional direct edge P->R with weight 10 was used."
        )


class TestDijkstraDirectlyWorks:
    """Tests that verify Dijkstra algorithm works correctly when called directly.
    These should always pass — the bug is in PathFinder, not Dijkstra.
    """

    def test_linear_path(self):
        g = WeightedGraph()
        g.add_edge('A', 'B', 1)
        g.add_edge('B', 'C', 2)
        g.add_edge('C', 'D', 3)

        dist, _ = dijkstra(g, 'A')
        assert dist['D'] == 6

    def test_single_edge(self):
        g = WeightedGraph()
        g.add_edge('X', 'Y', 5)
        dist, _ = dijkstra(g, 'X')
        assert dist['Y'] == 5

    def test_diamond_graph(self):
        g = WeightedGraph()
        g.add_edge('A', 'B', 1)
        g.add_edge('B', 'D', 2)
        g.add_edge('A', 'C', 5)
        g.add_edge('C', 'D', 1)
        g.add_edge('B', 'C', 1)

        dist, _ = dijkstra(g, 'A')
        assert dist['D'] == 3
        assert dist['C'] == 2

    def test_no_path(self):
        g = WeightedGraph()
        g.add_edge('A', 'B', 1)
        g.add_node('C')
        dist, _ = dijkstra(g, 'A')
        assert 'C' not in dist

    def test_path_reconstruction(self):
        g = WeightedGraph()
        g.add_edge('A', 'B', 1)
        g.add_edge('B', 'C', 1)
        _, prev = dijkstra(g, 'A')
        path = reconstruct_path(prev, 'C')
        assert path == ['A', 'B', 'C']

    def test_indirect_shorter_than_direct(self):
        """Dijkstra should correctly find indirect path even when direct edge exists."""
        g = WeightedGraph()
        g.add_edge('A', 'C', 10)  # Direct but expensive
        g.add_edge('A', 'B', 2)
        g.add_edge('B', 'C', 3)

        dist, prev = dijkstra(g, 'A')
        assert dist['C'] == 5  # Via B, not direct
        path = reconstruct_path(prev, 'C')
        assert path == ['A', 'B', 'C']


class TestMinHeapWorks:
    """Tests for MinHeap. Should always pass."""

    def test_basic_insert_extract(self):
        h = MinHeap()
        h.insert(3, 'c')
        h.insert(1, 'a')
        h.insert(2, 'b')
        assert h.extract_min() == (1, 'a')
        assert h.extract_min() == (2, 'b')
        assert h.extract_min() == (3, 'c')

    def test_empty_heap(self):
        h = MinHeap()
        assert h.is_empty
        with pytest.raises(IndexError):
            h.extract_min()

    def test_duplicate_priorities(self):
        h = MinHeap()
        h.insert(1, 'first')
        h.insert(1, 'second')
        # Both should be extractable
        results = [h.extract_min(), h.extract_min()]
        items = [r[1] for r in results]
        assert 'first' in items
        assert 'second' in items


class TestPathFinderSimpleCases:
    """Tests for PathFinder with simple graphs where no shortcut exists.
    These should always pass.
    """

    def test_simple_two_node_path(self):
        pf = PathFinder()
        pf.add_road('A', 'B', 5)
        dist, path = pf.find_shortest_path('A', 'B')
        assert dist == 5
        assert path == ['A', 'B']

    def test_no_direct_edge(self):
        """When there's no direct edge, PathFinder must run Dijkstra."""
        pf = PathFinder()
        pf.add_road('A', 'B', 1, bidirectional=False)
        pf.add_road('B', 'C', 2, bidirectional=False)

        dist, path = pf.find_shortest_path('A', 'C')
        assert dist == 3
        assert path == ['A', 'B', 'C']


class TestVisualizerWorks:
    """Tests for graph visualizer. Should always pass."""

    def test_render_simple_graph(self):
        g = WeightedGraph()
        g.add_edge('A', 'B', 1)
        g.add_edge('B', 'C', 2)

        viz = GraphVisualizer(g)
        result = viz.render()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_path(self):
        g = WeightedGraph()
        g.add_edge('X', 'Y', 5)

        viz = GraphVisualizer(g)
        result = viz.render_with_path(['X', 'Y'], dist=5)
        assert 'Path: X -> Y' in result
        assert 'Distance: 5' in result
