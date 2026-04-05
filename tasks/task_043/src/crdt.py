"""
Conflict-free Replicated Data Types (CRDTs).

Implements G-Counter (grow-only counter), PN-Counter (positive-negative counter),
G-Set (grow-only set), OR-Set (observed-remove set), and LWW-Register
(last-writer-wins register).
"""

from typing import Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
import copy
import time


class GCounter:
    """
    Grow-only counter CRDT.
    
    Each replica maintains its own count. The total value is the sum of all
    replica counts. Merge takes the maximum count for each replica.
    """

    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.counts: Dict[str, int] = {}

    def increment(self, amount: int = 1):
        """Increment this replica's counter."""
        if amount < 0:
            raise ValueError("G-Counter can only be incremented (positive amounts)")
        self.counts[self.replica_id] = self.counts.get(self.replica_id, 0) + amount

    @property
    def value(self) -> int:
        """Get the total counter value."""
        return sum(self.counts.values())

    def merge(self, other: "GCounter") -> "GCounter":
        """Merge another G-Counter into this one. Returns self for chaining."""
        all_replicas = set(self.counts.keys()) | set(other.counts.keys())
        for replica in all_replicas:
            my_count = self.counts.get(replica, 0)
            their_count = other.counts.get(replica, 0)
            self.counts[replica] = min(my_count, their_count)
        return self

    def clone(self) -> "GCounter":
        """Create a deep copy of this counter."""
        new = GCounter(self.replica_id)
        new.counts = dict(self.counts)
        return new

    def __repr__(self):
        return f"GCounter(replica={self.replica_id}, value={self.value}, counts={self.counts})"


class PNCounter:
    """
    Positive-Negative counter CRDT.
    
    Uses two G-Counters: one for increments and one for decrements.
    Value = P.value - N.value
    """

    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.p = GCounter(replica_id)
        self.n = GCounter(replica_id)

    def increment(self, amount: int = 1):
        """Increment the counter."""
        self.p.increment(amount)

    def decrement(self, amount: int = 1):
        """Decrement the counter."""
        self.n.increment(amount)

    @property
    def value(self) -> int:
        """Get the counter value (increments - decrements)."""
        return self.p.value - self.n.value

    def merge(self, other: "PNCounter") -> "PNCounter":
        """Merge another PN-Counter into this one."""
        self.p.merge(other.p)
        self.n.merge(other.n)
        return self

    def clone(self) -> "PNCounter":
        new = PNCounter(self.replica_id)
        new.p = self.p.clone()
        new.n = self.n.clone()
        return new

    def __repr__(self):
        return f"PNCounter(replica={self.replica_id}, value={self.value})"


class GSet:
    """Grow-only set CRDT."""

    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.elements: Set[Any] = set()

    def add(self, element: Any):
        self.elements.add(element)

    def contains(self, element: Any) -> bool:
        return element in self.elements

    @property
    def value(self) -> Set[Any]:
        return frozenset(self.elements)

    def merge(self, other: "GSet") -> "GSet":
        self.elements = self.elements | other.elements
        return self

    def clone(self) -> "GSet":
        new = GSet(self.replica_id)
        new.elements = set(self.elements)
        return new


class ORSet:
    """Observed-Remove set CRDT."""

    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self._tag_counter = 0
        self.elements: Dict[Any, Set[Tuple[str, int]]] = {}

    def _next_tag(self) -> Tuple[str, int]:
        self._tag_counter += 1
        return (self.replica_id, self._tag_counter)

    def add(self, element: Any):
        tag = self._next_tag()
        if element not in self.elements:
            self.elements[element] = set()
        self.elements[element].add(tag)

    def remove(self, element: Any):
        if element in self.elements:
            del self.elements[element]

    def contains(self, element: Any) -> bool:
        return element in self.elements and len(self.elements[element]) > 0

    @property
    def value(self) -> Set[Any]:
        return {e for e, tags in self.elements.items() if tags}

    def merge(self, other: "ORSet") -> "ORSet":
        all_elements = set(self.elements.keys()) | set(other.elements.keys())
        merged = {}
        for elem in all_elements:
            my_tags = self.elements.get(elem, set())
            their_tags = other.elements.get(elem, set())
            combined = my_tags | their_tags
            if combined:
                merged[elem] = combined
        self.elements = merged
        return self

    def clone(self) -> "ORSet":
        new = ORSet(self.replica_id)
        new._tag_counter = self._tag_counter
        new.elements = {k: set(v) for k, v in self.elements.items()}
        return new


class LWWRegister:
    """Last-Writer-Wins register CRDT."""

    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self._value: Any = None
        self._timestamp: float = 0.0
        self._writer: str = ""

    def set(self, value: Any, timestamp: Optional[float] = None):
        if timestamp is None:
            timestamp = time.time()
        if timestamp >= self._timestamp:
            self._value = value
            self._timestamp = timestamp
            self._writer = self.replica_id

    @property
    def value(self) -> Any:
        return self._value

    @property
    def timestamp(self) -> float:
        return self._timestamp

    def merge(self, other: "LWWRegister") -> "LWWRegister":
        if other._timestamp > self._timestamp:
            self._value = other._value
            self._timestamp = other._timestamp
            self._writer = other._writer
        return self

    def clone(self) -> "LWWRegister":
        new = LWWRegister(self.replica_id)
        new._value = self._value
        new._timestamp = self._timestamp
        new._writer = self._writer
        return new


class CRDTStore:
    """A simple CRDT key-value store with replication."""

    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.counters: Dict[str, PNCounter] = {}
        self.sets: Dict[str, ORSet] = {}
        self.registers: Dict[str, LWWRegister] = {}

    def get_counter(self, name: str) -> PNCounter:
        if name not in self.counters:
            self.counters[name] = PNCounter(self.replica_id)
        return self.counters[name]

    def get_set(self, name: str) -> ORSet:
        if name not in self.sets:
            self.sets[name] = ORSet(self.replica_id)
        return self.sets[name]

    def get_register(self, name: str) -> LWWRegister:
        if name not in self.registers:
            self.registers[name] = LWWRegister(self.replica_id)
        return self.registers[name]

    def merge_from(self, other: "CRDTStore"):
        for name, counter in other.counters.items():
            if name in self.counters:
                self.counters[name].merge(counter)
            else:
                self.counters[name] = counter.clone()

        for name, s in other.sets.items():
            if name in self.sets:
                self.sets[name].merge(s)
            else:
                self.sets[name] = s.clone()

        for name, reg in other.registers.items():
            if name in self.registers:
                self.registers[name].merge(reg)
            else:
                self.registers[name] = reg.clone()
