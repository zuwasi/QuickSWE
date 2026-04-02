"""Tests for the reactive data binding system."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.observable_value import ObservableValue
from src.computed import ComputedValue
from src.binding import Binding
from src.scope import Scope
from src.reactive import reactive, computed, bind, batch


# ============================================================
# PASS-TO-PASS: These tests should pass with the existing code
# ============================================================

class TestObservableValueBasic:
    """Basic ObservableValue tests — these should already pass."""

    def test_initial_value(self):
        obs = ObservableValue(42)
        assert obs.get() == 42

    def test_set_and_get(self):
        obs = ObservableValue(10)
        obs.set(20)
        assert obs.get() == 20

    def test_subscribe_notified(self):
        obs = ObservableValue("hello")
        changes = []
        obs.subscribe(lambda old, new: changes.append((old, new)))
        obs.set("world")
        assert changes == [("hello", "world")]

    def test_no_notification_on_same_value(self):
        obs = ObservableValue(5)
        changes = []
        obs.subscribe(lambda old, new: changes.append((old, new)))
        obs.set(5)
        assert changes == []

    def test_unsubscribe(self):
        obs = ObservableValue(0)
        changes = []
        unsub = obs.subscribe(lambda old, new: changes.append(new))
        obs.set(1)
        unsub()
        obs.set(2)
        assert changes == [1]

    def test_name(self):
        obs = ObservableValue(0, name="counter")
        assert obs.name == "counter"

    def test_reactive_convenience(self):
        obs = reactive(99, name="x")
        assert obs.get() == 99
        assert obs.name == "x"


# ============================================================
# FAIL-TO-PASS: These tests require implementing the full system
# ============================================================

@pytest.mark.fail_to_pass
class TestAutoDepTracking:
    """ComputedValue must automatically detect dependencies."""

    def test_basic_computed(self):
        a = ObservableValue(2, name="a")
        b = ObservableValue(3, name="b")
        c = ComputedValue(lambda: a.get() + b.get(), name="sum")
        assert c.get() == 5

    def test_recomputes_on_change(self):
        a = ObservableValue(10)
        c = ComputedValue(lambda: a.get() * 2)
        assert c.get() == 20
        a.set(5)
        assert c.get() == 10

    def test_tracks_multiple_deps(self):
        x = ObservableValue(1)
        y = ObservableValue(2)
        z = ObservableValue(3)
        c = ComputedValue(lambda: x.get() + y.get() + z.get())
        assert c.get() == 6
        y.set(20)
        assert c.get() == 24

    def test_dynamic_dependency_switch(self):
        """Dependencies can change between evaluations."""
        flag = ObservableValue(True)
        a = ObservableValue(10)
        b = ObservableValue(20)
        c = ComputedValue(lambda: a.get() if flag.get() else b.get())
        assert c.get() == 10
        flag.set(False)
        assert c.get() == 20
        # Now changing a should NOT trigger recomputation since c no longer depends on a
        a.set(999)
        assert c.get() == 20  # Still uses b

    def test_no_dependency_on_unread_observable(self):
        """If an observable is never read during compute, it's not a dependency."""
        a = ObservableValue(1)
        b = ObservableValue(2)
        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return a.get() * 10

        c = ComputedValue(compute_fn)
        c.get()  # First evaluation
        initial_count = call_count[0]
        b.set(999)  # b is NOT a dependency
        c.get()
        assert call_count[0] == initial_count  # Should NOT have recomputed


@pytest.mark.fail_to_pass
class TestLazyEvaluation:
    """ComputedValue should be lazy — only compute when .get() is called."""

    def test_not_computed_until_get(self):
        call_count = [0]
        a = ObservableValue(5)

        def fn():
            call_count[0] += 1
            return a.get()

        c = ComputedValue(fn)
        assert call_count[0] == 0  # Not computed yet
        c.get()
        assert call_count[0] == 1

    def test_dirty_but_not_recomputed_until_get(self):
        call_count = [0]
        a = ObservableValue(1)

        def fn():
            call_count[0] += 1
            return a.get() * 2

        c = ComputedValue(fn)
        c.get()  # Initial compute
        count_after_init = call_count[0]
        a.set(2)  # Marks dirty
        a.set(3)  # Still dirty
        a.set(4)  # Still dirty
        assert call_count[0] == count_after_init  # No recompute yet
        assert c.get() == 8  # Only now recomputes, uses latest value
        assert call_count[0] == count_after_init + 1


@pytest.mark.fail_to_pass
class TestDiamondDependency:
    """Diamond: A -> B, A -> C, B -> D, C -> D. D recomputes once per A change."""

    def test_diamond_single_recompute(self):
        a = ObservableValue(1, name="A")
        b = ComputedValue(lambda: a.get() * 2, name="B")
        c_val = ComputedValue(lambda: a.get() * 3, name="C")
        compute_count = [0]

        def compute_d():
            compute_count[0] += 1
            return b.get() + c_val.get()

        d = ComputedValue(compute_d, name="D")
        assert d.get() == 5  # 2 + 3
        compute_count[0] = 0
        a.set(2)
        assert d.get() == 10  # 4 + 6
        assert compute_count[0] == 1  # D only computed ONCE

    def test_deep_diamond(self):
        """A -> B -> D, A -> C -> D, deeper chain."""
        a = ObservableValue(1)
        b = ComputedValue(lambda: a.get() + 1)
        c = ComputedValue(lambda: a.get() + 2)
        d = ComputedValue(lambda: b.get() * c.get())
        assert d.get() == (1 + 1) * (1 + 2)  # 2 * 3 = 6
        a.set(10)
        assert d.get() == (10 + 1) * (10 + 2)  # 11 * 12 = 132


@pytest.mark.fail_to_pass
class TestTwoWayBinding:
    """Binding syncs two ObservableValues bidirectionally."""

    def test_source_to_target(self):
        src = ObservableValue(0)
        tgt = ObservableValue(0)
        b = Binding(src, tgt)
        src.set(42)
        assert tgt.get() == 42

    def test_target_to_source(self):
        src = ObservableValue(0)
        tgt = ObservableValue(0)
        b = Binding(src, tgt)
        tgt.set(99)
        assert src.get() == 99

    def test_no_infinite_loop(self):
        """Changing source updates target, which should NOT re-update source in a loop."""
        src = ObservableValue(0)
        tgt = ObservableValue(0)
        changes = []
        src.subscribe(lambda o, n: changes.append(("src", n)))
        tgt.subscribe(lambda o, n: changes.append(("tgt", n)))
        b = Binding(src, tgt)
        src.set(10)
        # There should be exactly: src changed to 10, tgt changed to 10
        assert tgt.get() == 10
        assert src.get() == 10
        # No infinite loop — limited number of change events
        assert len(changes) <= 4

    def test_binding_with_transform(self):
        celsius = ObservableValue(0.0)
        fahrenheit = ObservableValue(32.0)
        b = Binding(
            celsius, fahrenheit,
            transform=lambda c: c * 9 / 5 + 32,
            reverse_transform=lambda f: (f - 32) * 5 / 9,
        )
        celsius.set(100.0)
        assert abs(fahrenheit.get() - 212.0) < 0.01
        fahrenheit.set(32.0)
        assert abs(celsius.get() - 0.0) < 0.01

    def test_binding_destroy(self):
        src = ObservableValue(0)
        tgt = ObservableValue(0)
        b = Binding(src, tgt)
        # Binding should work before destroy
        src.set(25)
        assert tgt.get() == 25  # Synced
        b.destroy()
        assert not b.is_active
        src.set(50)
        assert tgt.get() == 25  # Not synced anymore — stays at 25


@pytest.mark.fail_to_pass
class TestErrorPropagation:
    """If a compute function raises, the error should propagate on .get()."""

    def test_error_on_get(self):
        def bad_fn():
            raise ValueError("computation failed")

        c = ComputedValue(bad_fn)
        with pytest.raises(ValueError, match="computation failed"):
            c.get()

    def test_error_recovery(self):
        """After dependency changes, if compute succeeds, error clears."""
        a = ObservableValue(-1)

        def fn():
            v = a.get()
            if v < 0:
                raise ValueError("negative")
            return v * 2

        c = ComputedValue(fn)
        with pytest.raises(ValueError):
            c.get()
        a.set(5)
        assert c.get() == 10  # Recovered


@pytest.mark.fail_to_pass
class TestBatchUpdates:
    """Scope.batch() defers recomputations until the batch exits."""

    def test_batch_defers_recomputation(self):
        a = ObservableValue(1)
        b = ObservableValue(2)
        compute_count = [0]

        def fn():
            compute_count[0] += 1
            return a.get() + b.get()

        c = ComputedValue(fn)
        c.get()  # Initial
        compute_count[0] = 0
        with Scope.batch():
            a.set(10)
            b.set(20)
        assert c.get() == 30
        assert compute_count[0] == 1  # Only ONE recompute after batch

    def test_nested_batch(self):
        a = ObservableValue(0)
        c = ComputedValue(lambda: a.get() + 1)
        c.get()  # init
        with Scope.batch():
            a.set(1)
            with Scope.batch():
                a.set(2)
            # Inner batch exits but outer is still active
            # Recompute should NOT happen yet
        assert c.get() == 3  # Only after all batches exit


@pytest.mark.fail_to_pass
class TestChainedComputed:
    """Multiple levels of ComputedValues depending on each other."""

    def test_three_level_chain(self):
        base = ObservableValue(2)
        doubled = ComputedValue(lambda: base.get() * 2)
        quadrupled = ComputedValue(lambda: doubled.get() * 2)
        assert quadrupled.get() == 8
        base.set(5)
        assert quadrupled.get() == 20

    def test_fan_out(self):
        """One observable, many dependents."""
        base = ObservableValue(10)
        computeds = [ComputedValue(lambda i=i: base.get() + i) for i in range(5)]
        assert [c.get() for c in computeds] == [10, 11, 12, 13, 14]
        base.set(100)
        assert [c.get() for c in computeds] == [100, 101, 102, 103, 104]


@pytest.mark.fail_to_pass
class TestConvenienceAPI:
    """Test the top-level reactive module API."""

    def test_reactive_and_computed(self):
        x = reactive(5)
        y = reactive(10)
        total = computed(lambda: x.get() + y.get())
        assert total.get() == 15

    def test_bind_convenience(self):
        a = reactive(0)
        b = reactive(0)
        binding = bind(a, b)
        a.set(7)
        assert b.get() == 7
