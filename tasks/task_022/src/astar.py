"""
A* pathfinding algorithm on a weighted grid graph.

Supports custom heuristics and weighted edges. Grid cells can be
passable (cost >= 1) or blocked (cost = -1).
"""

import heapq
from typing import List, Tuple, Optional, Callable, Dict, Set


class GridGraph:
    """A 2D grid where each cell has a traversal cost."""

    def __init__(self, width: int, height: int, default_cost: int = 1):
        self.width = width
        self.height = height
        self.grid = [[default_cost] * width for _ in range(height)]

    def set_cost(self, row: int, col: int, cost: int):
        self.grid[row][col] = cost

    def set_blocked(self, row: int, col: int):
        self.grid[row][col] = -1

    def is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def is_passable(self, row: int, col: int) -> bool:
        return self.is_valid(row, col) and self.grid[row][col] > 0

    def get_cost(self, row: int, col: int) -> int:
        return self.grid[row][col]

    def neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if self.is_passable(nr, nc):
                result.append((nr, nc))
        return result

    def neighbors_with_diag(self, row: int, col: int) -> List[Tuple[int, int]]:
        result = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if self.is_passable(nr, nc):
                    result.append((nr, nc))
        return result


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def chebyshev_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def euclidean_distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


class AStarPathfinder:
    """A* search on a GridGraph."""

    def __init__(self, graph: GridGraph,
                 heuristic: Callable = manhattan_distance,
                 allow_diagonal: bool = False):
        self.graph = graph
        self.heuristic = heuristic
        self.allow_diagonal = allow_diagonal
        self.nodes_expanded = 0

    def find_path(self, start: Tuple[int, int],
                  goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        if not self.graph.is_passable(*start) or not self.graph.is_passable(*goal):
            return None

        self.nodes_expanded = 0
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        closed_set: Set[Tuple[int, int]] = set()

        h_start = self.heuristic(start, goal)
        f_start = h_start
        counter = 0
        open_heap = [(f_start, counter, start)]

        while open_heap:
            f_current, _, current = heapq.heappop(open_heap)

            if current in closed_set:
                continue

            if current == goal:
                return self._reconstruct_path(came_from, current)

            closed_set.add(current)
            self.nodes_expanded += 1

            if self.allow_diagonal:
                neighbors = self.graph.neighbors_with_diag(*current)
            else:
                neighbors = self.graph.neighbors(*current)

            for neighbor in neighbors:
                if neighbor in closed_set:
                    continue

                move_cost = self.graph.get_cost(*neighbor)
                tentative_g = g_score[current] + move_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    came_from[neighbor] = current
                    h = self.heuristic(neighbor, goal)
                    f = tentative_g + h
                    counter += 1
                    open_heap.append((f, counter, neighbor))
                    heapq.heappush(open_heap, (f, counter, neighbor))

            heapq.heapify(open_heap)

        return None

    def _reconstruct_path(self, came_from: Dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def find_path_cost(self, start: Tuple[int, int],
                       goal: Tuple[int, int]) -> Optional[float]:
        path = self.find_path(start, goal)
        if path is None:
            return None
        cost = 0.0
        for i in range(1, len(path)):
            cost += self.graph.get_cost(*path[i])
        return cost


class BidirectionalAStar:
    """Bidirectional A* search that expands from both start and goal."""

    def __init__(self, graph: GridGraph,
                 heuristic: Callable = manhattan_distance):
        self.graph = graph
        self.heuristic = heuristic
        self.nodes_expanded = 0

    def find_path(self, start: Tuple[int, int],
                  goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        if not self.graph.is_passable(*start) or not self.graph.is_passable(*goal):
            return None
        if start == goal:
            return [start]

        self.nodes_expanded = 0
        g_fwd: Dict = {start: 0}
        g_bwd: Dict = {goal: 0}
        came_fwd: Dict = {}
        came_bwd: Dict = {}
        closed_fwd: Set = set()
        closed_bwd: Set = set()

        counter = 0
        open_fwd = [(self.heuristic(start, goal), counter, start)]
        counter += 1
        open_bwd = [(self.heuristic(goal, start), counter, goal)]

        best_cost = float('inf')
        meeting = None

        while open_fwd and open_bwd:
            if open_fwd[0][0] + open_bwd[0][0] >= best_cost:
                break

            if len(open_fwd) <= len(open_bwd):
                meeting = self._expand(open_fwd, g_fwd, came_fwd, closed_fwd,
                                       g_bwd, closed_bwd, goal, True,
                                       best_cost, meeting)
                if meeting and g_fwd.get(meeting, float('inf')) + g_bwd.get(meeting, float('inf')) < best_cost:
                    best_cost = g_fwd[meeting] + g_bwd[meeting]
            else:
                meeting = self._expand(open_bwd, g_bwd, came_bwd, closed_bwd,
                                       g_fwd, closed_fwd, start, False,
                                       best_cost, meeting)
                if meeting and g_fwd.get(meeting, float('inf')) + g_bwd.get(meeting, float('inf')) < best_cost:
                    best_cost = g_fwd[meeting] + g_bwd[meeting]

        if meeting is None:
            return None

        path_fwd = []
        node = meeting
        while node in came_fwd:
            path_fwd.append(node)
            node = came_fwd[node]
        path_fwd.append(node)
        path_fwd.reverse()

        path_bwd = []
        node = meeting
        while node in came_bwd:
            node = came_bwd[node]
            path_bwd.append(node)

        return path_fwd + path_bwd

    def _expand(self, open_heap, g_this, came_this, closed_this,
                g_other, closed_other, target, is_forward,
                best_cost, meeting):
        counter = open_heap[-1][1] + 1 if open_heap else 0
        _, _, current = heapq.heappop(open_heap)

        if current in closed_this:
            return meeting

        closed_this.add(current)
        self.nodes_expanded += 1

        for neighbor in self.graph.neighbors(*current):
            if neighbor in closed_this:
                continue
            tentative_g = g_this[current] + self.graph.get_cost(*neighbor)
            if neighbor not in g_this or tentative_g < g_this[neighbor]:
                g_this[neighbor] = tentative_g
                came_this[neighbor] = current
                h = self.heuristic(neighbor, target)
                f = tentative_g + h
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

                if neighbor in g_other:
                    total = tentative_g + g_other[neighbor]
                    if total < best_cost:
                        meeting = neighbor

        return meeting
