"""
Reactive dataflow computation engine.

Provides Signal (mutable source) and Computed (derived) nodes that form a
dependency graph. Changes to signals automatically propagate to computed nodes.
"""

from typing import Any, Callable, List, Optional, Set, Dict
from dataclasses import dataclass, field
from collections import defaultdict


class ReactiveContext:
    """Global context for tracking reactive dependencies."""

    _instance: Optional["ReactiveContext"] = None

    def __init__(self):
        self._tracking_stack: List["Computed"] = []
        self._batch_depth = 0
        self._pending_updates: List["Signal"] = []
        self._all_nodes: List["ReactiveNode"] = []
        self._update_log: List[tuple] = []

    @classmethod
    def get(cls) -> "ReactiveContext":
        if cls._instance is None:
            cls._instance = ReactiveContext()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = ReactiveContext()

    def start_tracking(self, computed: "Computed"):
        self._tracking_stack.append(computed)

    def stop_tracking(self):
        if self._tracking_stack:
            self._tracking_stack.pop()

    def record_dependency(self, source: "ReactiveNode"):
        if self._tracking_stack:
            current = self._tracking_stack[-1]
            source.add_dependent(current)
            current.add_dependency(source)

    def log_update(self, node_name: str, old_value: Any, new_value: Any):
        self._update_log.append((node_name, old_value, new_value))

    def get_update_log(self) -> List[tuple]:
        return list(self._update_log)

    def clear_log(self):
        self._update_log = []


class ReactiveNode:
    """Base class for reactive nodes."""

    _id_counter = 0

    def __init__(self, name: str = ""):
        ReactiveNode._id_counter += 1
        self.id = ReactiveNode._id_counter
        self.name = name or f"node_{self.id}"
        self._dependents: List["ReactiveNode"] = []
        self._dependencies: List["ReactiveNode"] = []
        self._value: Any = None

    @property
    def value(self) -> Any:
        ctx = ReactiveContext.get()
        ctx.record_dependency(self)
        return self._value

    def add_dependent(self, node: "ReactiveNode"):
        if node not in self._dependents:
            self._dependents.append(node)

    def remove_dependent(self, node: "ReactiveNode"):
        if node in self._dependents:
            self._dependents.remove(node)

    def add_dependency(self, node: "ReactiveNode"):
        if node not in self._dependencies:
            self._dependencies.append(node)

    def clear_dependencies(self):
        for dep in self._dependencies:
            dep.remove_dependent(self)
        self._dependencies = []

    def _notify_dependents(self):
        """Notify all dependents that this node's value has changed."""
        for dep in list(self._dependents):
            dep._update()


class Signal(ReactiveNode):
    """A mutable source value in the reactive graph."""

    def __init__(self, initial_value: Any, name: str = ""):
        super().__init__(name)
        self._value = initial_value

    def set(self, new_value: Any):
        """Set a new value and propagate changes."""
        if self._value != new_value:
            old = self._value
            self._value = new_value
            ctx = ReactiveContext.get()
            ctx.log_update(self.name, old, new_value)
            self._notify_dependents()

    def update(self, fn: Callable[[Any], Any]):
        """Update value using a function."""
        self.set(fn(self._value))


class Computed(ReactiveNode):
    """A derived value computed from other reactive nodes."""

    def __init__(self, compute_fn: Callable[[], Any], name: str = ""):
        super().__init__(name)
        self._compute_fn = compute_fn
        self._stale = True
        self._computing = False
        self._initial_compute()

    def _initial_compute(self):
        """Compute the initial value and track dependencies."""
        self._recompute()

    def _recompute(self):
        """Recompute the value, tracking dependencies."""
        if self._computing:
            raise RuntimeError(f"Circular dependency detected at {self.name}")

        self._computing = True
        self.clear_dependencies()

        ctx = ReactiveContext.get()
        ctx.start_tracking(self)
        try:
            new_value = self._compute_fn()
        finally:
            ctx.stop_tracking()
            self._computing = False

        old = self._value
        self._value = new_value
        self._stale = False

        if old != new_value:
            ctx.log_update(self.name, old, new_value)
            return True
        return False

    def _update(self):
        """Called when a dependency changes."""
        changed = self._recompute()
        if changed:
            self._notify_dependents()

    @property
    def value(self) -> Any:
        ctx = ReactiveContext.get()
        ctx.record_dependency(self)
        if self._stale:
            self._recompute()
        return self._value


class Effect:
    """Side effect that runs when dependencies change."""

    def __init__(self, fn: Callable[[], None], name: str = ""):
        self.name = name or "effect"
        self.fn = fn
        self._dependencies: List[ReactiveNode] = []
        self._run_count = 0
        self._values_seen: List[Any] = []
        self._run()

    def _run(self):
        ctx = ReactiveContext.get()
        # Create a temporary computed to track dependencies
        self._cleanup()

        tracker = Computed(lambda: (self.fn(), None)[1], name=f"{self.name}_tracker")
        self._tracker = tracker
        self._run_count += 1

    def _cleanup(self):
        if hasattr(self, '_tracker'):
            self._tracker.clear_dependencies()

    @property
    def run_count(self) -> int:
        return self._run_count


class Memo(Computed):
    """Memoized computed value — only recomputes when dependencies change."""

    def __init__(self, compute_fn: Callable[[], Any], equals_fn: Optional[Callable] = None,
                 name: str = ""):
        self._equals_fn = equals_fn or (lambda a, b: a == b)
        super().__init__(compute_fn, name)

    def _recompute(self):
        if self._computing:
            raise RuntimeError(f"Circular dependency at {self.name}")

        self._computing = True
        self.clear_dependencies()

        ctx = ReactiveContext.get()
        ctx.start_tracking(self)
        try:
            new_value = self._compute_fn()
        finally:
            ctx.stop_tracking()
            self._computing = False

        old = self._value
        if old is not None and self._equals_fn(old, new_value):
            self._stale = False
            return False

        self._value = new_value
        self._stale = False
        ctx.log_update(self.name, old, new_value)
        return True


def create_signal(value: Any, name: str = "") -> Signal:
    return Signal(value, name)


def create_computed(fn: Callable[[], Any], name: str = "") -> Computed:
    return Computed(fn, name)


def create_memo(fn: Callable[[], Any], name: str = "") -> Memo:
    return Memo(fn, name=name)


def batch(fn: Callable[[], None]):
    """Execute multiple signal updates as a single batch."""
    fn()
