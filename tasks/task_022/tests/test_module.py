import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.astar import GridGraph, AStarPathfinder, manhattan_distance


class TestAStarPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_simple_straight_path(self):
        g = GridGraph(5, 1)
        pf = AStarPathfinder(g)
        path = pf.find_path((0, 0), (0, 4))
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (0, 4)

    def test_blocked_returns_none(self):
        g = GridGraph(3, 3)
        g.set_blocked(0, 1)
        g.set_blocked(1, 1)
        g.set_blocked(2, 1)
        pf = AStarPathfinder(g)
        path = pf.find_path((0, 0), (0, 2))
        assert path is None

    def test_start_equals_goal(self):
        g = GridGraph(3, 3)
        pf = AStarPathfinder(g)
        path = pf.find_path((1, 1), (1, 1))
        assert path == [(1, 1)]


@pytest.mark.fail_to_pass
class TestAStarFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_10x10_expansion_count(self):
        g = GridGraph(10, 10)
        pf = AStarPathfinder(g)
        path = pf.find_path((0, 0), (9, 9))
        assert path is not None
        assert len(path) == 19
        assert pf.nodes_expanded < 50, (
            f"10x10 uniform grid: expanded {pf.nodes_expanded} nodes (expected < 50)")

    def test_15x15_expansion_count(self):
        g = GridGraph(15, 15)
        pf = AStarPathfinder(g)
        path = pf.find_path((0, 0), (14, 14))
        assert path is not None
        assert len(path) == 29
        assert pf.nodes_expanded < 100, (
            f"15x15 uniform grid: expanded {pf.nodes_expanded} nodes (expected < 100)")

    def test_20x20_expansion_count(self):
        g = GridGraph(20, 20)
        pf = AStarPathfinder(g)
        path = pf.find_path((0, 0), (19, 19))
        assert path is not None
        assert len(path) == 39
        assert pf.nodes_expanded < 200, (
            f"20x20 uniform grid: expanded {pf.nodes_expanded} nodes (expected < 200)")

    def test_obstacle_grid_expansion(self):
        g = GridGraph(15, 15)
        for r in range(2, 13):
            g.set_blocked(r, 7)
        pf = AStarPathfinder(g)
        path = pf.find_path((7, 0), (7, 14))
        assert path is not None
        cost = sum(g.get_cost(*p) for p in path[1:])
        assert cost <= 26
        assert pf.nodes_expanded < 80, (
            f"15x15 with wall: expanded {pf.nodes_expanded} nodes (expected < 80)")
