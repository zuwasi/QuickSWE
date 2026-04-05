import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.topo_sort import topological_sort, CyclicGraphError


def _is_valid_order(order, graph):
    """Check that every node appears after all its dependencies."""
    pos = {node: i for i, node in enumerate(order)}
    for node, deps in graph.items():
        for dep in deps:
            if pos.get(dep, -1) >= pos.get(node, -1):
                return False
    return True


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_simple_cycle_detection():
    """A -> B -> A must raise CyclicGraphError."""
    graph = {
        "A": ["B"],
        "B": ["A"],
    }
    with pytest.raises(CyclicGraphError):
        topological_sort(graph)


@pytest.mark.fail_to_pass
def test_three_node_cycle_detection():
    """A -> B -> C -> A must raise CyclicGraphError."""
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
    }
    with pytest.raises(CyclicGraphError):
        topological_sort(graph)


@pytest.mark.fail_to_pass
def test_self_cycle_detection():
    """A self-loop must raise CyclicGraphError."""
    graph = {
        "X": ["X"],
    }
    with pytest.raises(CyclicGraphError):
        topological_sort(graph)


@pytest.mark.fail_to_pass
def test_cycle_in_subgraph():
    """A cycle buried in a larger graph must still be detected."""
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["D"],
        "D": ["B"],
        "E": [],
    }
    with pytest.raises(CyclicGraphError):
        topological_sort(graph)


# ─── pass_to_pass ───────────────────────────────────────────────

def test_linear_chain():
    """Simple linear chain A->B->C."""
    graph = {"A": ["B"], "B": ["C"], "C": []}
    order = topological_sort(graph)
    assert order.index("C") < order.index("B") < order.index("A")


def test_independent_nodes():
    """Nodes with no dependencies."""
    graph = {"A": [], "B": [], "C": []}
    order = topological_sort(graph)
    assert set(order) == {"A", "B", "C"}


def test_empty_graph():
    """Empty graph returns empty list."""
    assert topological_sort({}) == []
