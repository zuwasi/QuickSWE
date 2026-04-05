import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dijkstra import Graph, dijkstra, shortest_distances


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_zero_weight_edge_correct_distance():
    """Graph with zero-weight edge must return correct shortest distance."""
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 0)
    g.add_edge("A", "C", 2)

    dist, path = dijkstra(g, "A", "C")
    assert dist == 1, f"Expected distance 1, got {dist}"
    assert path == ["A", "B", "C"]


@pytest.mark.fail_to_pass
def test_zero_weight_does_not_reprocess_visited():
    """Zero-weight edges must not cause already-visited nodes to be reprocessed
    and corrupt the path."""
    g = Graph()
    g.add_edge("S", "A", 1)
    g.add_edge("S", "B", 2)
    g.add_edge("A", "B", 0)
    g.add_edge("B", "T", 1)

    dist, path = dijkstra(g, "S", "T")
    assert dist == 2, f"Expected distance 2, got {dist}"
    assert path == ["S", "A", "B", "T"]


@pytest.mark.fail_to_pass
def test_multiple_zero_weight_edges():
    """Chain of zero-weight edges must compute correctly."""
    g = Graph()
    g.add_edge("A", "B", 0)
    g.add_edge("B", "C", 0)
    g.add_edge("C", "D", 0)
    g.add_edge("A", "D", 1)

    dist, path = dijkstra(g, "A", "D")
    assert dist == 0, f"Expected 0, got {dist}"
    assert path == ["A", "B", "C", "D"]


@pytest.mark.fail_to_pass
def test_stale_entry_does_not_override_shorter_path():
    """A stale heap entry for a visited node must not corrupt results."""
    g = Graph()
    g.add_edge("S", "A", 5)
    g.add_edge("S", "B", 1)
    g.add_edge("B", "A", 0)
    g.add_edge("A", "T", 1)

    dist, path = dijkstra(g, "S", "T")
    assert dist == 2, f"Expected 2, got {dist}"
    assert path == ["S", "B", "A", "T"]


# ─── pass_to_pass ───────────────────────────────────────────────

def test_simple_path():
    """Basic shortest path with positive weights."""
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    dist, path = dijkstra(g, "A", "C")
    assert dist == 3
    assert path == ["A", "B", "C"]


def test_no_path():
    """No path returns (None, None)."""
    g = Graph()
    g.add_node("X")
    g.add_node("Y")
    dist, path = dijkstra(g, "X", "Y")
    assert dist is None
    assert path is None


def test_same_start_end():
    """Distance from a node to itself is 0."""
    g = Graph()
    g.add_node("A")
    dist, path = dijkstra(g, "A", "A")
    assert dist == 0
    assert path == ["A"]
