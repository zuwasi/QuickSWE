import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.crdt import GCounter, PNCounter, GSet, ORSet, LWWRegister


class TestBasicCRDT:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_gcounter_single_replica(self):
        c = GCounter("r1")
        c.increment(5)
        c.increment(3)
        assert c.value == 8

    @pytest.mark.pass_to_pass
    def test_gset_merge(self):
        s1 = GSet("r1")
        s2 = GSet("r2")
        s1.add("a")
        s2.add("b")
        s1.merge(s2)
        assert s1.contains("a")
        assert s1.contains("b")

    @pytest.mark.pass_to_pass
    def test_lww_register(self):
        r1 = LWWRegister("r1")
        r1.set("hello", timestamp=1.0)
        r1.set("world", timestamp=2.0)
        assert r1.value == "world"


class TestGCounterMerge:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_gcounter_merge_takes_max(self):
        """Merge should take the maximum count per replica."""
        c1 = GCounter("r1")
        c2 = GCounter("r2")

        c1.increment(5)  # r1: {r1: 5}
        c2.increment(3)  # r2: {r2: 3}

        # Both replicas receive each other's state
        c1_clone = c1.clone()
        c1.merge(c2)
        c2.merge(c1_clone)

        # Now c1 increments again
        c1.increment(2)  # r1: {r1: 7, r2: 3}

        # Merge again: c2 should see r1's updated count
        c2.merge(c1)
        assert c2.value == 10, (
            f"After merge, value should be 7+3=10, got {c2.value}"
        )

    @pytest.mark.fail_to_pass
    def test_gcounter_merge_idempotent(self):
        """Merging same state multiple times should not decrease value."""
        c1 = GCounter("r1")
        c1.increment(10)

        c2 = GCounter("r2")
        c2.increment(5)

        c1.merge(c2)
        val_after_first = c1.value

        c1.merge(c2)
        val_after_second = c1.value

        assert val_after_second == val_after_first, (
            f"Merge should be idempotent: {val_after_first} != {val_after_second}"
        )
        assert val_after_second == 15

    @pytest.mark.fail_to_pass
    def test_pncounter_merge_correct(self):
        """PN-Counter merge depends on correct G-Counter merge."""
        pn1 = PNCounter("r1")
        pn2 = PNCounter("r2")

        pn1.increment(10)
        pn2.increment(5)
        pn2.decrement(2)

        pn1.merge(pn2)

        # r1 incremented 10, r2 incremented 5, r2 decremented 2
        # value = (10+5) - (0+2) = 13
        assert pn1.value == 13, f"PN-Counter should be 13, got {pn1.value}"
