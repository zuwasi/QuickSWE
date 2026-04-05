# Task 022: A* Pathfinder Tie-Breaking Bug

## Problem

An A* pathfinding implementation returns suboptimal paths because it does not
properly break ties when multiple nodes have the same f-cost. When f-costs are
equal, the algorithm should prefer the node with the higher g-cost (closer to the
goal), but currently it uses arbitrary ordering from the heap, which can lead to
exploring nodes further from the goal first and returning longer paths.

## Expected Behavior

When two nodes in the open set have the same f-cost (f = g + h), the one with
the higher g-cost should be expanded first. This ensures the algorithm finds the
truly optimal path rather than a valid but suboptimal one.

## Files

- `src/astar.py` — A* pathfinding on a weighted grid graph
