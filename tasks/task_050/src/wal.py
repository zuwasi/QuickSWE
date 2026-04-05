"""
Write-Ahead Log (WAL) for a key-value store.

Provides transaction durability through logging. All writes go to the log
first. On crash recovery, committed transactions are replayed from the log.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import OrderedDict
import time
import copy


class LogRecordType(Enum):
    BEGIN = auto()
    WRITE = auto()
    DELETE = auto()
    COMMIT = auto()
    ABORT = auto()
    CHECKPOINT = auto()


@dataclass
class LogRecord:
    """A single record in the write-ahead log."""
    lsn: int                    # Log sequence number
    txn_id: int                 # Transaction ID
    record_type: LogRecordType
    key: Optional[str] = None
    value: Optional[Any] = None
    old_value: Optional[Any] = None
    timestamp: float = 0.0

    def __repr__(self):
        if self.record_type in (LogRecordType.WRITE, LogRecordType.DELETE):
            return (f"LogRecord(lsn={self.lsn}, txn={self.txn_id}, "
                    f"{self.record_type.name}, key={self.key!r}, val={self.value!r})")
        return f"LogRecord(lsn={self.lsn}, txn={self.txn_id}, {self.record_type.name})"


class WriteAheadLog:
    """Write-ahead log with transaction support."""

    def __init__(self):
        self._log: List[LogRecord] = []
        self._lsn_counter = 0
        self._txn_counter = 0
        self._active_txns: Dict[int, List[LogRecord]] = {}
        self._flushed_lsn = 0

    def _next_lsn(self) -> int:
        self._lsn_counter += 1
        return self._lsn_counter

    def _next_txn_id(self) -> int:
        self._txn_counter += 1
        return self._txn_counter

    def _append(self, record: LogRecord):
        self._log.append(record)

    def begin_transaction(self) -> int:
        """Start a new transaction. Returns transaction ID."""
        txn_id = self._next_txn_id()
        record = LogRecord(
            lsn=self._next_lsn(),
            txn_id=txn_id,
            record_type=LogRecordType.BEGIN,
            timestamp=time.time(),
        )
        self._append(record)
        self._active_txns[txn_id] = []
        return txn_id

    def write(self, txn_id: int, key: str, value: Any, old_value: Any = None):
        """Log a write operation."""
        if txn_id not in self._active_txns:
            raise ValueError(f"Transaction {txn_id} is not active")
        record = LogRecord(
            lsn=self._next_lsn(),
            txn_id=txn_id,
            record_type=LogRecordType.WRITE,
            key=key,
            value=value,
            old_value=old_value,
            timestamp=time.time(),
        )
        self._append(record)
        self._active_txns[txn_id].append(record)

    def delete(self, txn_id: int, key: str, old_value: Any = None):
        """Log a delete operation."""
        if txn_id not in self._active_txns:
            raise ValueError(f"Transaction {txn_id} is not active")
        record = LogRecord(
            lsn=self._next_lsn(),
            txn_id=txn_id,
            record_type=LogRecordType.DELETE,
            key=key,
            old_value=old_value,
            timestamp=time.time(),
        )
        self._append(record)
        self._active_txns[txn_id].append(record)

    def commit(self, txn_id: int):
        """Commit a transaction."""
        if txn_id not in self._active_txns:
            raise ValueError(f"Transaction {txn_id} is not active")
        record = LogRecord(
            lsn=self._next_lsn(),
            txn_id=txn_id,
            record_type=LogRecordType.COMMIT,
            timestamp=time.time(),
        )
        self._append(record)
        del self._active_txns[txn_id]

    def abort(self, txn_id: int):
        """Abort a transaction."""
        if txn_id not in self._active_txns:
            raise ValueError(f"Transaction {txn_id} is not active")
        record = LogRecord(
            lsn=self._next_lsn(),
            txn_id=txn_id,
            record_type=LogRecordType.ABORT,
            timestamp=time.time(),
        )
        self._append(record)
        del self._active_txns[txn_id]

    def checkpoint(self):
        """Write a checkpoint record."""
        record = LogRecord(
            lsn=self._next_lsn(),
            txn_id=0,
            record_type=LogRecordType.CHECKPOINT,
            timestamp=time.time(),
        )
        self._append(record)
        self._flushed_lsn = record.lsn

    def get_log(self) -> List[LogRecord]:
        """Return the complete log."""
        return list(self._log)

    def get_log_size(self) -> int:
        return len(self._log)


class WALRecovery:
    """Recovers database state from a write-ahead log."""

    def __init__(self, log: List[LogRecord]):
        self.log = log
        self.recovered_state: Dict[str, Any] = {}
        self.committed_txns: Set[int] = set()
        self.aborted_txns: Set[int] = set()

    def analyze(self):
        """Analysis pass: determine which transactions committed and which aborted."""
        for record in self.log:
            if record.record_type == LogRecordType.COMMIT:
                self.committed_txns.add(record.txn_id)
            elif record.record_type == LogRecordType.ABORT:
                self.aborted_txns.add(record.txn_id)

    def redo(self) -> Dict[str, Any]:
        """
        Redo pass: replay committed transactions to reconstruct state.
        """
        self.analyze()

        # Collect writes per transaction
        txn_writes: Dict[int, List[LogRecord]] = {}
        for record in self.log:
            if record.txn_id in self.committed_txns:
                if record.record_type in (LogRecordType.WRITE, LogRecordType.DELETE):
                    if record.txn_id not in txn_writes:
                        txn_writes[record.txn_id] = []
                    txn_writes[record.txn_id].append(record)

        # Replay transactions in transaction ID order (start order)
        for txn_id in sorted(txn_writes.keys()):
            for record in txn_writes[txn_id]:
                if record.record_type == LogRecordType.WRITE:
                    self.recovered_state[record.key] = record.value
                elif record.record_type == LogRecordType.DELETE:
                    self.recovered_state.pop(record.key, None)

        return self.recovered_state

    def recover(self) -> Dict[str, Any]:
        """Full recovery: analyze + redo."""
        return self.redo()


class WALKeyValueStore:
    """Key-value store backed by a write-ahead log."""

    def __init__(self):
        self.wal = WriteAheadLog()
        self._data: Dict[str, Any] = {}
        self._txn_buffers: Dict[int, Dict[str, Tuple[str, Any]]] = {}

    def begin(self) -> int:
        """Begin a transaction."""
        txn_id = self.wal.begin_transaction()
        self._txn_buffers[txn_id] = {}
        return txn_id

    def put(self, txn_id: int, key: str, value: Any):
        """Write a key-value pair within a transaction."""
        old_value = self._data.get(key)
        self.wal.write(txn_id, key, value, old_value)
        self._txn_buffers[txn_id][key] = ("write", value)

    def get(self, key: str, txn_id: Optional[int] = None) -> Optional[Any]:
        """Read a value. If txn_id given, includes uncommitted writes from that txn."""
        if txn_id and txn_id in self._txn_buffers:
            buf = self._txn_buffers[txn_id]
            if key in buf:
                op, val = buf[key]
                if op == "delete":
                    return None
                return val
        return self._data.get(key)

    def delete(self, txn_id: int, key: str):
        """Delete a key within a transaction."""
        old_value = self._data.get(key)
        self.wal.delete(txn_id, key, old_value)
        self._txn_buffers[txn_id][key] = ("delete", None)

    def commit(self, txn_id: int):
        """Commit a transaction."""
        buf = self._txn_buffers.pop(txn_id, {})
        for key, (op, value) in buf.items():
            if op == "write":
                self._data[key] = value
            elif op == "delete":
                self._data.pop(key, None)
        self.wal.commit(txn_id)

    def abort(self, txn_id: int):
        """Abort a transaction."""
        self._txn_buffers.pop(txn_id, None)
        self.wal.abort(txn_id)

    def crash_and_recover(self) -> Dict[str, Any]:
        """Simulate crash and recovery from WAL."""
        log = self.wal.get_log()
        recovery = WALRecovery(log)
        recovered = recovery.recover()
        self._data = dict(recovered)
        return recovered

    def get_state(self) -> Dict[str, Any]:
        """Get current database state."""
        return dict(self._data)
