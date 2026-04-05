import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.consistent_hash import ConsistentHashRing


def make_fixed_ring():
    """Create a ring with deterministic hash values for testing."""
    mapping = {
        "A#vn0": 100,
        "B#vn0": 300,
        "C#vn0": 500,
    }

    def fixed_hash(key):
        if key in mapping:
            return mapping[key]
        return sum(ord(c) * (i + 1) for i, c in enumerate(key)) % 1000

    ring = ConsistentHashRing(num_virtual=1, hash_func=fixed_hash)
    ring.add_node("A")
    ring.add_node("B")
    ring.add_node("C")
    return ring, fixed_hash


class TestConsistentHashPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_add_and_get_single_node(self):
        ring = ConsistentHashRing(num_virtual=10)
        ring.add_node("server1")
        assert ring.get_node("any_key") == "server1"

    def test_empty_ring_returns_none(self):
        ring = ConsistentHashRing()
        assert ring.get_node("key") is None

    def test_remove_node(self):
        ring = ConsistentHashRing(num_virtual=10)
        ring.add_node("s1")
        ring.add_node("s2")
        ring.remove_node("s1")
        for i in range(20):
            assert ring.get_node(f"key_{i}") == "s2"


@pytest.mark.fail_to_pass
class TestConsistentHashFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_wrap_around_to_first_node(self):
        """Key with hash > max ring hash should wrap to the first node."""
        ring, fixed_hash = make_fixed_ring()
        ring._hash_func = lambda k: 600
        node = ring.get_node("wrap_key")
        assert node == "A", f"Expected 'A' (first node on ring), got '{node}'"

    def test_key_exactly_at_max_hash(self):
        """Key with hash == max ring hash should go to C (exact match wraps past it)."""
        ring, fixed_hash = make_fixed_ring()
        ring._hash_func = lambda k: 500
        node = ring.get_node("exact_max")
        assert node == "A", f"Key at max hash should wrap to first node 'A', got '{node}'"

    def test_consistent_assignment_with_ring_wrap(self):
        """Multiple keys past the end of the ring should all go to A (first node)."""
        ring, fixed_hash = make_fixed_ring()
        for hash_val in [501, 600, 700, 999]:
            ring._hash_func = lambda k, h=hash_val: h
            node = ring.get_node(f"key_{hash_val}")
            assert node == "A", (
                f"Key with hash {hash_val} should wrap to 'A', got '{node}'")
