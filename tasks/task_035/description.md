# Task 035: Segment Tree Lazy Propagation Bug

## Problem

A segment tree with lazy propagation has a bug in its `range_query` method.
When querying a range, the method does not push pending lazy updates to
children before recursing. This causes the query to return stale values
because children still hold outdated sums while the parent's lazy value
hasn't been propagated.

## Expected Behavior

Before recursing into children during a query, any pending lazy value at the
current node must be pushed down to its children. This ensures child nodes
have up-to-date values before their sums are computed.

## Files

- `src/segment_tree.py` — Segment tree with range update and range query via lazy propagation
