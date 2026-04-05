"""
Deadlock detector using a wait-for graph.

Threads acquire and release locks. The wait-for graph tracks which threads
are waiting on which other threads. Deadlocks are detected by finding cycles
in the wait-for graph.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class LockInfo:
    """Information about a lock."""
    lock_id: str
    owner: Optional[str] = None
    waiters: List[str] = field(default_factory=list)
    reentrant: bool = False
    hold_count: int = 0


@dataclass
class ThreadInfo:
    """Information about a thread."""
    thread_id: str
    held_locks: List[str] = field(default_factory=list)
    waiting_for: Optional[str] = None
    state: str = "running"


class WaitForGraph:
    """
    Directed graph representing wait-for relationships between threads.
    Edge (A, B) means thread A is waiting for thread B.
    """

    def __init__(self):
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        self.nodes: Set[str] = set()

    def add_node(self, node: str):
        self.nodes.add(node)

    def add_edge(self, from_node: str, to_node: str):
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        self.edges[from_node].add(to_node)

    def remove_edge(self, from_node: str, to_node: str):
        if from_node in self.edges:
            self.edges[from_node].discard(to_node)

    def remove_node(self, node: str):
        self.nodes.discard(node)
        self.edges.pop(node, None)
        for frm in list(self.edges.keys()):
            self.edges[frm].discard(node)

    def get_successors(self, node: str) -> Set[str]:
        return self.edges.get(node, set())

    def has_edge(self, from_node: str, to_node: str) -> bool:
        return to_node in self.edges.get(from_node, set())

    def find_cycle(self) -> Optional[List[str]]:
        """
        Find a cycle in the graph using DFS.
        Returns the cycle as a list of nodes, or None if no cycle exists.
        """
        visited: Set[str] = set()

        for start in self.nodes:
            if start in visited:
                continue
            path: List[str] = []
            result = self._dfs_cycle(start, visited, path)
            if result is not None:
                return result

        return None

    def _dfs_cycle(self, node: str, visited: Set[str],
                   path: List[str]) -> Optional[List[str]]:
        visited.add(node)
        path.append(node)

        for neighbor in self.get_successors(node):
            if neighbor in path:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]

            if neighbor not in visited:
                result = self._dfs_cycle(neighbor, visited, path)
                if result is not None:
                    return result

        path.pop()
        return None

    def detect_deadlock(self) -> Optional[List[str]]:
        """Detect if there is a deadlock (cycle in wait-for graph)."""
        return self.find_cycle()

    def __repr__(self):
        edges_str = []
        for frm, tos in self.edges.items():
            for to in tos:
                edges_str.append(f"{frm} -> {to}")
        return f"WaitForGraph({', '.join(edges_str)})"


class LockManager:
    """Manages locks and detects deadlocks."""

    def __init__(self, enable_deadlock_detection: bool = True):
        self._mutex = threading.RLock()
        self.locks: Dict[str, LockInfo] = {}
        self.threads: Dict[str, ThreadInfo] = {}
        self.wfg = WaitForGraph()
        self.detect_enabled = enable_deadlock_detection
        self._deadlock_history: List[List[str]] = []

    def register_thread(self, thread_id: str):
        with self._mutex:
            if thread_id not in self.threads:
                self.threads[thread_id] = ThreadInfo(thread_id=thread_id)
                self.wfg.add_node(thread_id)

    def register_lock(self, lock_id: str, reentrant: bool = False):
        with self._mutex:
            if lock_id not in self.locks:
                self.locks[lock_id] = LockInfo(lock_id=lock_id, reentrant=reentrant)

    def try_acquire(self, thread_id: str, lock_id: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Try to acquire a lock. Returns (success, deadlock_cycle).
        If deadlock would occur, returns (False, cycle).
        """
        with self._mutex:
            self._ensure_registered(thread_id, lock_id)
            lock = self.locks[lock_id]
            thread = self.threads[thread_id]

            if lock.owner is None:
                lock.owner = thread_id
                lock.hold_count = 1
                thread.held_locks.append(lock_id)
                return (True, None)

            if lock.owner == thread_id:
                if lock.reentrant:
                    lock.hold_count += 1
                    return (True, None)
                # Non-reentrant lock re-acquired by same thread
                # Add self-edge for tracking
                self.wfg.add_edge(thread_id, thread_id)
                thread.waiting_for = lock_id

                if self.detect_enabled:
                    cycle = self.wfg.detect_deadlock()
                    if cycle:
                        self.wfg.remove_edge(thread_id, thread_id)
                        thread.waiting_for = None
                        self._deadlock_history.append(cycle)
                        return (False, cycle)

                self.wfg.remove_edge(thread_id, thread_id)
                thread.waiting_for = None
                return (False, None)

            # Another thread holds the lock
            self.wfg.add_edge(thread_id, lock.owner)
            thread.waiting_for = lock_id

            if self.detect_enabled:
                cycle = self.wfg.detect_deadlock()
                if cycle:
                    self.wfg.remove_edge(thread_id, lock.owner)
                    thread.waiting_for = None
                    self._deadlock_history.append(cycle)
                    return (False, cycle)

            lock.waiters.append(thread_id)
            return (False, None)

    def release(self, thread_id: str, lock_id: str):
        with self._mutex:
            if lock_id not in self.locks:
                raise ValueError(f"Unknown lock: {lock_id}")
            lock = self.locks[lock_id]
            if lock.owner != thread_id:
                raise ValueError(f"Thread {thread_id} does not hold lock {lock_id}")

            lock.hold_count -= 1
            if lock.hold_count > 0:
                return

            lock.owner = None
            thread = self.threads[thread_id]
            if lock_id in thread.held_locks:
                thread.held_locks.remove(lock_id)

            # Remove wait-for edges to this thread for this lock
            for waiter_id in lock.waiters:
                self.wfg.remove_edge(waiter_id, thread_id)
                waiter = self.threads.get(waiter_id)
                if waiter:
                    waiter.waiting_for = None

            # Grant to first waiter
            if lock.waiters:
                next_thread_id = lock.waiters.pop(0)
                lock.owner = next_thread_id
                lock.hold_count = 1
                next_thread = self.threads.get(next_thread_id)
                if next_thread:
                    next_thread.held_locks.append(lock_id)
                    next_thread.waiting_for = None
                    next_thread.state = "running"

    def acquire_blocking(self, thread_id: str, lock_id: str) -> Optional[List[str]]:
        """Acquire lock, blocking if necessary. Returns deadlock cycle if detected."""
        success, cycle = self.try_acquire(thread_id, lock_id)
        if cycle:
            return cycle
        # In a real system, would block here. For simulation, just return.
        return None

    def _ensure_registered(self, thread_id: str, lock_id: str):
        if thread_id not in self.threads:
            self.register_thread(thread_id)
        if lock_id not in self.locks:
            self.register_lock(lock_id)

    def get_deadlock_history(self) -> List[List[str]]:
        return list(self._deadlock_history)

    def get_wait_for_graph(self) -> WaitForGraph:
        return self.wfg

    def dump_state(self) -> str:
        lines = ["Lock Manager State:"]
        for lid, lock in self.locks.items():
            lines.append(f"  Lock {lid}: owner={lock.owner}, waiters={lock.waiters}")
        for tid, thread in self.threads.items():
            lines.append(f"  Thread {tid}: held={thread.held_locks}, waiting={thread.waiting_for}")
        lines.append(f"  WFG: {self.wfg}")
        return "\n".join(lines)
