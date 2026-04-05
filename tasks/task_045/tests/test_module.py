import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.lsm_tree import LSMTree, SSTable, SSTEntry, merge_sstables, MemTable


class TestBasicLSM:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_put_get(self):
        lsm = LSMTree(memtable_size=100)
        lsm.put("key1", "value1")
        lsm.put("key2", "value2")
        assert lsm.get("key1") == "value1"
        assert lsm.get("key2") == "value2"

    @pytest.mark.pass_to_pass
    def test_delete_from_memtable(self):
        lsm = LSMTree(memtable_size=100)
        lsm.put("k", "v")
        lsm.delete("k")
        assert lsm.get("k") is None

    @pytest.mark.pass_to_pass
    def test_overwrite(self):
        lsm = LSMTree(memtable_size=100)
        lsm.put("k", "old")
        lsm.put("k", "new")
        assert lsm.get("k") == "new"


class TestTombstoneCompaction:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_delete_survives_compaction(self):
        """A deleted key should remain deleted after compaction pushes tombstone past the value."""
        lsm = LSMTree(memtable_size=10, max_levels=4, level_ratio=2)

        # Put key into L0, then compact to L1, then compact to L2
        lsm.put("important_key", "original_value")
        lsm.force_flush()
        lsm.force_compact(0)  # L0 -> L1
        lsm.force_compact(1)  # L1 -> L2 (value now in L2)

        # Delete the key (tombstone goes to memtable -> L0)
        lsm.delete("important_key")
        lsm.force_flush()

        # Compact L0 -> L1 (tombstone merges into L1, value is in L2)
        lsm.force_compact(0)

        # Now compact L1 -> L2 (tombstone must propagate to cover value in L2)
        lsm.force_compact(1)

        # Key should still be deleted
        assert lsm.get("important_key") is None, (
            "Deleted key was resurrected after compaction!"
        )

    @pytest.mark.fail_to_pass
    def test_tombstone_propagated_through_levels(self):
        """Tombstones must propagate to cover values in lower levels."""
        lsm = LSMTree(memtable_size=5, max_levels=4, level_ratio=2)

        # Write some data to fill levels
        for i in range(10):
            lsm.put(f"key_{i:03d}", f"val_{i}")
        lsm.force_flush()
        lsm.force_compact(0)

        # Write more to push data deeper
        for i in range(10, 20):
            lsm.put(f"key_{i:03d}", f"val_{i}")
        lsm.force_flush()
        lsm.force_compact(0)
        lsm.force_compact(1)

        # Delete a key that's now in a deep level
        lsm.delete("key_005")
        lsm.force_flush()

        # Compact multiple times
        lsm.force_compact(0)
        lsm.force_compact(1)

        assert lsm.get("key_005") is None, (
            "Tombstone was lost during multi-level compaction"
        )

    @pytest.mark.fail_to_pass
    def test_scan_after_delete_and_compact(self):
        """Scan should not return deleted keys after multi-level compaction."""
        lsm = LSMTree(memtable_size=10, max_levels=4, level_ratio=2)

        lsm.put("a", 1)
        lsm.put("b", 2)
        lsm.put("c", 3)
        lsm.force_flush()
        lsm.force_compact(0)  # L0 -> L1
        lsm.force_compact(1)  # L1 -> L2 (values in L2)

        lsm.delete("b")
        lsm.force_flush()
        lsm.force_compact(0)  # tombstone to L1
        lsm.force_compact(1)  # tombstone must propagate to L2

        results = lsm.scan()
        keys = [k for k, v in results]
        assert "b" not in keys, f"Deleted key 'b' appeared in scan: {results}"

    @pytest.mark.fail_to_pass
    def test_merge_sstables_keeps_tombstones(self):
        """merge_sstables should keep tombstones when not at lowest level."""
        entries1 = [SSTEntry("x", "old_val", sequence=1)]
        entries2 = [SSTEntry("x", None, sequence=2, is_tombstone=True)]
        sst1 = SSTable(entries1, level=0)
        sst2 = SSTable(entries2, level=0)

        merged = merge_sstables([sst1, sst2], target_level=1, is_lowest_level=False)

        entry = merged.get("x")
        assert entry is not None, "Tombstone entry should be preserved"
        assert entry.is_tombstone, "Entry should remain a tombstone"
