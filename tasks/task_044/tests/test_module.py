import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.reactive import (
    Signal, Computed, ReactiveContext, create_signal, create_computed,
)


@pytest.fixture(autouse=True)
def reset_context():
    ReactiveContext.reset()
    yield
    ReactiveContext.reset()


class TestBasicReactivity:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_signal_read_write(self):
        s = Signal(10, name="s")
        assert s.value == 10
        s.set(20)
        assert s.value == 20

    @pytest.mark.pass_to_pass
    def test_computed_basic(self):
        a = Signal(3, name="a")
        b = Signal(4, name="b")
        c = Computed(lambda: a.value + b.value, name="c")
        assert c.value == 7
        a.set(10)
        assert c.value == 14

    @pytest.mark.pass_to_pass
    def test_chain_propagation(self):
        a = Signal(1, name="a")
        b = Computed(lambda: a.value * 2, name="b")
        c = Computed(lambda: b.value + 10, name="c")
        assert c.value == 12
        a.set(5)
        assert c.value == 20


class TestDiamondDependency:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_diamond_no_glitch(self):
        """
        Diamond: A -> B -> D
                 A -> C -> D
        D should never see inconsistent (B_new, C_old) or (B_old, C_new).
        """
        a = Signal(1, name="a")
        b = Computed(lambda: a.value * 2, name="b")
        c = Computed(lambda: a.value * 3, name="c")

        intermediate_values = []

        d = Computed(lambda: (
            intermediate_values.append(b.value + c.value),
            b.value + c.value
        )[1], name="d")

        intermediate_values.clear()
        a.set(2)

        # With a=2: b=4, c=6, d should be 10
        assert d.value == 10

        # D should have been computed at most ONCE during this update
        # (not once with stale C and once with updated C)
        assert len(intermediate_values) <= 1, (
            f"D was computed {len(intermediate_values)} times, expected at most 1. "
            f"Values seen: {intermediate_values}"
        )

    @pytest.mark.fail_to_pass
    def test_diamond_consistent_values(self):
        """All intermediate computations of D should see consistent state."""
        a = Signal(0, name="a")
        b = Computed(lambda: a.value + 1, name="b")
        c = Computed(lambda: a.value + 1, name="c")

        observed_pairs = []
        d = Computed(lambda: (
            observed_pairs.append((b.value, c.value)),
            b.value + c.value
        )[1], name="d")

        observed_pairs.clear()
        a.set(10)

        for b_val, c_val in observed_pairs:
            assert b_val == c_val, (
                f"D saw inconsistent values: b={b_val}, c={c_val}. "
                f"All observations: {observed_pairs}"
            )

    @pytest.mark.fail_to_pass
    def test_wide_diamond_single_update(self):
        """
        A fans out to B, C, E. All feed into F.
        F should compute exactly once per A update.
        """
        a = Signal(1, name="a")
        b = Computed(lambda: a.value + 1, name="b")
        c = Computed(lambda: a.value + 2, name="c")
        e = Computed(lambda: a.value + 3, name="e")

        f_count = []
        f = Computed(lambda: (
            f_count.append(1),
            b.value + c.value + e.value
        )[1], name="f")

        f_count.clear()
        a.set(10)

        assert f.value == 11 + 12 + 13
        assert len(f_count) == 1, (
            f"F recomputed {len(f_count)} times, expected exactly 1"
        )

    @pytest.mark.fail_to_pass
    def test_nested_diamond(self):
        """
        A -> B -> D -> F
        A -> C -> D -> F
        A -> C -> E -> F
        """
        a = Signal(1, name="a")
        b = Computed(lambda: a.value * 2, name="b")
        c = Computed(lambda: a.value * 3, name="c")
        d = Computed(lambda: b.value + c.value, name="d")
        e = Computed(lambda: c.value * 2, name="e")

        f_computations = []
        f = Computed(lambda: (
            f_computations.append(d.value + e.value),
            d.value + e.value
        )[1], name="f")

        f_computations.clear()
        a.set(2)

        # a=2: b=4, c=6, d=10, e=12, f=22
        assert f.value == 22
        assert len(f_computations) == 1, (
            f"F computed {len(f_computations)} times with values {f_computations}, expected 1"
        )
