"""
Transaction manager with MVCC and multiple isolation levels.

Supports READ_UNCOMMITTED, READ_COMMITTED, REPEATABLE_READ, and SERIALIZABLE.
Uses multi-version concurrency control with version chains per key.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import threading
import copy


class IsolationLevel(Enum):
    READ_UNCOMMITTED = 0
    READ_COMMITTED = 1
    REPEATABLE_READ = 2
    SERIALIZABLE = 3


class TransactionState(Enum):
    ACTIVE = auto()
    COMMITTED = auto()
    ABORTED = auto()


@dataclass
class Version:
    """A single version of a value."""
    value: Any
    txn_id: int
    timestamp: int
    deleted: bool = False


@dataclass
class Transaction:
    txn_id: int
    isolation: IsolationLevel
    state: TransactionState = TransactionState.ACTIVE
    start_timestamp: int = 0
    commit_timestamp: int = 0
    read_set: Set[str] = field(default_factory=set)
    write_set: Dict[str, Any] = field(default_factory=dict)
    snapshot_timestamp: int = 0


class TransactionManager:
    """MVCC-based transaction manager."""

    def __init__(self):
        self._lock = threading.Lock()
        self._timestamp_counter = 0
        self._txn_counter = 0
        self._versions: Dict[str, List[Version]] = {}
        self._active_txns: Dict[int, Transaction] = {}
        self._committed_txns: Dict[int, Transaction] = {}

    def _next_timestamp(self) -> int:
        self._timestamp_counter += 1
        return self._timestamp_counter

    def _next_txn_id(self) -> int:
        self._txn_counter += 1
        return self._txn_counter

    def begin(self, isolation: IsolationLevel = IsolationLevel.READ_COMMITTED) -> int:
        """Begin a new transaction. Returns transaction ID."""
        with self._lock:
            txn_id = self._next_txn_id()
            ts = self._next_timestamp()
            txn = Transaction(
                txn_id=txn_id,
                isolation=isolation,
                start_timestamp=ts,
                snapshot_timestamp=ts,
            )
            self._active_txns[txn_id] = txn
            return txn_id

    def _get_txn(self, txn_id: int) -> Transaction:
        txn = self._active_txns.get(txn_id)
        if txn is None:
            raise ValueError(f"Transaction {txn_id} is not active")
        if txn.state != TransactionState.ACTIVE:
            raise ValueError(f"Transaction {txn_id} is {txn.state.name}")
        return txn

    def _visible_version(self, key: str, txn: Transaction) -> Optional[Version]:
        """Find the version of key visible to the given transaction."""
        versions = self._versions.get(key, [])
        if not versions:
            return None

        if txn.isolation == IsolationLevel.READ_UNCOMMITTED:
            return versions[-1]

        if txn.isolation == IsolationLevel.READ_COMMITTED:
            for v in reversed(versions):
                if v.txn_id == txn.txn_id:
                    return v
                committed_txn = self._committed_txns.get(v.txn_id)
                if committed_txn and committed_txn.state == TransactionState.COMMITTED:
                    return v
            return None

        if txn.isolation == IsolationLevel.SERIALIZABLE:
            for v in reversed(versions):
                if v.txn_id == txn.txn_id:
                    return v
                committed_txn = self._committed_txns.get(v.txn_id)
                if committed_txn and committed_txn.state == TransactionState.COMMITTED:
                    return v
            return None

        # REPEATABLE_READ uses snapshot isolation
        snapshot_ts = txn.snapshot_timestamp
        for v in reversed(versions):
            if v.txn_id == txn.txn_id:
                return v
            committed_txn = self._committed_txns.get(v.txn_id)
            if committed_txn and committed_txn.state == TransactionState.COMMITTED:
                if committed_txn.commit_timestamp <= snapshot_ts:
                    return v
        return None

    def read(self, txn_id: int, key: str) -> Optional[Any]:
        """Read a key within a transaction."""
        with self._lock:
            txn = self._get_txn(txn_id)
            txn.read_set.add(key)

            if key in txn.write_set:
                val = txn.write_set[key]
                if val is None:
                    return None
                return val

            version = self._visible_version(key, txn)
            if version is None or version.deleted:
                return None
            return version.value

    def write(self, txn_id: int, key: str, value: Any):
        """Write a key within a transaction."""
        with self._lock:
            txn = self._get_txn(txn_id)

            if txn.isolation in (IsolationLevel.REPEATABLE_READ, IsolationLevel.SERIALIZABLE):
                versions = self._versions.get(key, [])
                for v in versions:
                    if v.txn_id != txn.txn_id:
                        other_txn = self._active_txns.get(v.txn_id)
                        if other_txn and other_txn.state == TransactionState.ACTIVE:
                            if v.timestamp > txn.start_timestamp:
                                raise RuntimeError(
                                    f"Write conflict on key '{key}' for txn {txn_id}"
                                )

            txn.write_set[key] = value

    def delete(self, txn_id: int, key: str):
        """Delete a key within a transaction."""
        with self._lock:
            txn = self._get_txn(txn_id)
            txn.write_set[key] = None

    def scan(self, txn_id: int, prefix: str = "",
             predicate: Optional[Callable[[str, Any], bool]] = None) -> Dict[str, Any]:
        """
        Scan keys matching an optional prefix and predicate.
        Returns dict of matching key-value pairs.
        """
        with self._lock:
            txn = self._get_txn(txn_id)
            results = {}

            all_keys = set(self._versions.keys()) | set(txn.write_set.keys())

            for key in sorted(all_keys):
                if prefix and not key.startswith(prefix):
                    continue

                if key in txn.write_set:
                    val = txn.write_set[key]
                    if val is not None:
                        if predicate is None or predicate(key, val):
                            results[key] = val
                    continue

                version = self._visible_version(key, txn)
                if version and not version.deleted:
                    if predicate is None or predicate(key, version.value):
                        results[key] = version.value

            for key in results:
                txn.read_set.add(key)

            return results

    def commit(self, txn_id: int) -> bool:
        """Commit a transaction. Returns True on success."""
        with self._lock:
            txn = self._get_txn(txn_id)

            commit_ts = self._next_timestamp()

            if txn.isolation == IsolationLevel.SERIALIZABLE:
                for other_txn in self._committed_txns.values():
                    if other_txn.commit_timestamp > txn.start_timestamp:
                        if txn.read_set & set(other_txn.write_set.keys()):
                            txn.state = TransactionState.ABORTED
                            del self._active_txns[txn_id]
                            return False

            for key, value in txn.write_set.items():
                if key not in self._versions:
                    self._versions[key] = []
                if value is None:
                    self._versions[key].append(Version(
                        value=None,
                        txn_id=txn.txn_id,
                        timestamp=commit_ts,
                        deleted=True,
                    ))
                else:
                    self._versions[key].append(Version(
                        value=value,
                        txn_id=txn.txn_id,
                        timestamp=commit_ts,
                    ))

            txn.state = TransactionState.COMMITTED
            txn.commit_timestamp = commit_ts
            del self._active_txns[txn_id]
            self._committed_txns[txn_id] = txn
            return True

    def rollback(self, txn_id: int):
        """Rollback/abort a transaction."""
        with self._lock:
            txn = self._get_txn(txn_id)
            txn.state = TransactionState.ABORTED
            del self._active_txns[txn_id]

    def get_all_committed(self) -> Dict[str, Any]:
        """Get the current committed state of all keys (for testing)."""
        with self._lock:
            result = {}
            for key, versions in self._versions.items():
                for v in reversed(versions):
                    committed_txn = self._committed_txns.get(v.txn_id)
                    if committed_txn and committed_txn.state == TransactionState.COMMITTED:
                        if not v.deleted:
                            result[key] = v.value
                        break
            return result


class Table:
    """Simple table abstraction on top of TransactionManager."""

    def __init__(self, name: str, tm: TransactionManager):
        self.name = name
        self.tm = tm
        self._row_counter = 0

    def _key(self, row_id: int) -> str:
        return f"{self.name}:{row_id}"

    def insert(self, txn_id: int, data: Dict[str, Any]) -> int:
        with self.tm._lock:
            self._row_counter += 1
            row_id = self._row_counter
        key = self._key(row_id)
        data_copy = dict(data)
        data_copy["_id"] = row_id
        self.tm.write(txn_id, key, data_copy)
        return row_id

    def get(self, txn_id: int, row_id: int) -> Optional[Dict[str, Any]]:
        return self.tm.read(txn_id, self._key(row_id))

    def update(self, txn_id: int, row_id: int, data: Dict[str, Any]):
        data_copy = dict(data)
        data_copy["_id"] = row_id
        self.tm.write(txn_id, self._key(row_id), data_copy)

    def delete(self, txn_id: int, row_id: int):
        self.tm.delete(txn_id, self._key(row_id))

    def scan_all(self, txn_id: int,
                 predicate: Optional[Callable[[str, Any], bool]] = None) -> List[Dict[str, Any]]:
        results = self.tm.scan(txn_id, prefix=f"{self.name}:", predicate=predicate)
        return list(results.values())
