"""
Log-Structured Merge-Tree (LSM-Tree) implementation.

Provides a key-value store with write-optimized performance using an
in-memory memtable and multiple sorted on-disk levels with compaction.
"""

from typing import Dict, List, Optional, Tuple, Any, Iterator
from dataclasses import dataclass, field
from collections import OrderedDict
import bisect


_TOMBSTONE = object()


@dataclass
class SSTEntry:
    """An entry in a sorted string table."""
    key: str
    value: Any
    sequence: int
    is_tombstone: bool = False


class SSTable:
    """Sorted String Table — an immutable sorted run of key-value pairs."""

    def __init__(self, entries: List[SSTEntry], level: int = 0):
        self.entries = sorted(entries, key=lambda e: e.key)
        self.level = level
        self._index: Dict[str, int] = {}
        for i, entry in enumerate(self.entries):
            if entry.key not in self._index:
                self._index[entry.key] = i

    def get(self, key: str) -> Optional[SSTEntry]:
        if key in self._index:
            return self.entries[self._index[key]]
        return None

    def __iter__(self) -> Iterator[SSTEntry]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    @property
    def min_key(self) -> Optional[str]:
        return self.entries[0].key if self.entries else None

    @property
    def max_key(self) -> Optional[str]:
        return self.entries[-1].key if self.entries else None

    def overlaps(self, other: "SSTable") -> bool:
        if not self.entries or not other.entries:
            return False
        return not (self.max_key < other.min_key or self.min_key > other.max_key)

    def key_range(self) -> Tuple[Optional[str], Optional[str]]:
        return (self.min_key, self.max_key)


class MemTable:
    """In-memory sorted table (write buffer)."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._data: Dict[str, Tuple[Any, int, bool]] = {}
        self._seq = 0

    def put(self, key: str, value: Any, seq: int):
        self._data[key] = (value, seq, False)

    def delete(self, key: str, seq: int):
        self._data[key] = (_TOMBSTONE, seq, True)

    def get(self, key: str) -> Optional[Tuple[Any, bool]]:
        if key in self._data:
            value, seq, is_tomb = self._data[key]
            return (value, is_tomb)
        return None

    def is_full(self) -> bool:
        return len(self._data) >= self.max_size

    def flush(self, level: int = 0) -> SSTable:
        entries = []
        for key, (value, seq, is_tomb) in sorted(self._data.items()):
            entries.append(SSTEntry(
                key=key, value=value, sequence=seq, is_tombstone=is_tomb
            ))
        sst = SSTable(entries, level=level)
        self._data.clear()
        return sst

    def __len__(self) -> int:
        return len(self._data)


def merge_sstables(tables: List[SSTable], target_level: int,
                   is_lowest_level: bool = False) -> SSTable:
    """
    Merge multiple SSTables into one, keeping the newest version of each key.
    Tombstones are discarded during merge to save space.
    """
    all_entries: Dict[str, SSTEntry] = {}

    for table in tables:
        for entry in table:
            existing = all_entries.get(entry.key)
            if existing is None or entry.sequence > existing.sequence:
                all_entries[entry.key] = entry

    merged = []
    for key in sorted(all_entries.keys()):
        entry = all_entries[key]
        if entry.is_tombstone:
            continue
        merged.append(SSTEntry(
            key=entry.key,
            value=entry.value,
            sequence=entry.sequence,
            is_tombstone=False,
        ))

    return SSTable(merged, level=target_level)


class LSMTree:
    """Log-Structured Merge-Tree key-value store."""

    def __init__(self, memtable_size: int = 50, max_levels: int = 4,
                 level_ratio: int = 4):
        self.memtable = MemTable(max_size=memtable_size)
        self.immutable_memtable: Optional[MemTable] = None
        self.levels: List[List[SSTable]] = [[] for _ in range(max_levels)]
        self.max_levels = max_levels
        self.level_ratio = level_ratio
        self._sequence = 0
        self._level_max_tables = [level_ratio ** (i + 1) for i in range(max_levels)]
        self._compaction_count = 0

    def _next_seq(self) -> int:
        self._sequence += 1
        return self._sequence

    def put(self, key: str, value: Any):
        """Insert or update a key-value pair."""
        seq = self._next_seq()
        self.memtable.put(key, value, seq)
        if self.memtable.is_full():
            self._flush_memtable()

    def delete(self, key: str):
        """Delete a key by writing a tombstone."""
        seq = self._next_seq()
        self.memtable.delete(key, seq)
        if self.memtable.is_full():
            self._flush_memtable()

    def get(self, key: str) -> Optional[Any]:
        """Look up a key. Returns None if not found or deleted."""
        # Check memtable first
        result = self.memtable.get(key)
        if result is not None:
            value, is_tomb = result
            return None if is_tomb else value

        # Check immutable memtable
        if self.immutable_memtable:
            result = self.immutable_memtable.get(key)
            if result is not None:
                value, is_tomb = result
                return None if is_tomb else value

        # Check each level from newest to oldest
        for level in self.levels:
            for sst in reversed(level):
                entry = sst.get(key)
                if entry is not None:
                    if entry.is_tombstone:
                        return None
                    return entry.value

        return None

    def _flush_memtable(self):
        """Flush the memtable to Level 0."""
        if len(self.memtable) == 0:
            return

        sst = self.memtable.flush(level=0)
        self.levels[0].append(sst)

        if len(self.levels[0]) > self._level_max_tables[0]:
            self._compact(0)

    def _compact(self, level: int):
        """Compact level N into level N+1."""
        if level >= self.max_levels - 1:
            return

        tables_to_merge = self.levels[level]
        if not tables_to_merge:
            return

        next_level = level + 1
        overlapping = []
        remaining = []

        for sst in self.levels[next_level]:
            overlap = False
            for src in tables_to_merge:
                if src.overlaps(sst):
                    overlap = True
                    break
            if overlap:
                overlapping.append(sst)
            else:
                remaining.append(sst)

        all_tables = tables_to_merge + overlapping
        is_lowest = next_level == self.max_levels - 1
        merged = merge_sstables(all_tables, target_level=next_level,
                                is_lowest_level=is_lowest)

        self.levels[level] = []
        self.levels[next_level] = remaining
        if len(merged) > 0:
            self.levels[next_level].append(merged)

        self._compaction_count += 1

        if len(self.levels[next_level]) > self._level_max_tables[next_level]:
            self._compact(next_level)

    def force_flush(self):
        """Force flush memtable (for testing)."""
        self._flush_memtable()

    def force_compact(self, level: int = 0):
        """Force compaction of a specific level (for testing)."""
        self._compact(level)

    def scan(self, start_key: Optional[str] = None,
             end_key: Optional[str] = None) -> List[Tuple[str, Any]]:
        """Scan a range of keys. Returns sorted (key, value) pairs."""
        all_entries: Dict[str, SSTEntry] = {}

        # Collect from all levels (bottom up)
        for level in reversed(self.levels):
            for sst in level:
                for entry in sst:
                    if start_key and entry.key < start_key:
                        continue
                    if end_key and entry.key >= end_key:
                        continue
                    existing = all_entries.get(entry.key)
                    if existing is None or entry.sequence > existing.sequence:
                        all_entries[entry.key] = entry

        # Check memtable
        for key, (value, seq, is_tomb) in self.memtable._data.items():
            if start_key and key < start_key:
                continue
            if end_key and key >= end_key:
                continue
            existing = all_entries.get(key)
            entry = SSTEntry(key=key, value=value, sequence=seq, is_tombstone=is_tomb)
            if existing is None or entry.sequence > existing.sequence:
                all_entries[key] = entry

        results = []
        for key in sorted(all_entries.keys()):
            entry = all_entries[key]
            if not entry.is_tombstone:
                results.append((key, entry.value))

        return results

    def stats(self) -> Dict[str, Any]:
        return {
            "memtable_size": len(self.memtable),
            "levels": [len(level) for level in self.levels],
            "total_sstables": sum(len(level) for level in self.levels),
            "compactions": self._compaction_count,
            "sequence": self._sequence,
        }
