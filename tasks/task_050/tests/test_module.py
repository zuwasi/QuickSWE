import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.wal import WriteAheadLog, WALRecovery, WALKeyValueStore, LogRecordType


class TestBasicWAL:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_single_transaction_recovery(self):
        store = WALKeyValueStore()
        t1 = store.begin()
        store.put(t1, "x", 10)
        store.put(t1, "y", 20)
        store.commit(t1)

        recovered = store.crash_and_recover()
        assert recovered["x"] == 10
        assert recovered["y"] == 20

    @pytest.mark.pass_to_pass
    def test_aborted_transaction_not_recovered(self):
        store = WALKeyValueStore()
        t1 = store.begin()
        store.put(t1, "x", 100)
        store.abort(t1)

        recovered = store.crash_and_recover()
        assert "x" not in recovered

    @pytest.mark.pass_to_pass
    def test_sequential_non_overlapping(self):
        """Non-overlapping sequential transactions should recover correctly."""
        store = WALKeyValueStore()
        t1 = store.begin()
        store.put(t1, "a", 1)
        store.commit(t1)

        t2 = store.begin()
        store.put(t2, "a", 2)
        store.commit(t2)

        recovered = store.crash_and_recover()
        assert recovered["a"] == 2


class TestCommitOrdering:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_late_committer_wins(self):
        """
        T1 starts first but commits last. T2 starts second but commits first.
        Recovery should replay in commit order: T2 then T1.
        So T1's write (committed later) should be the final value.
        """
        wal = WriteAheadLog()

        t1 = wal.begin_transaction()
        t2 = wal.begin_transaction()

        wal.write(t1, "key", "t1_value")
        wal.write(t2, "key", "t2_value")

        # T2 commits FIRST
        wal.commit(t2)
        # T1 commits SECOND
        wal.commit(t1)

        recovery = WALRecovery(wal.get_log())
        state = recovery.recover()

        assert state["key"] == "t1_value", (
            f"T1 committed after T2, so T1's value should win. "
            f"Got '{state['key']}', expected 't1_value'"
        )

    @pytest.mark.fail_to_pass
    def test_interleaved_commit_order(self):
        """Multiple transactions with interleaved start/commit order."""
        wal = WriteAheadLog()

        t1 = wal.begin_transaction()  # starts first
        t2 = wal.begin_transaction()  # starts second
        t3 = wal.begin_transaction()  # starts third

        wal.write(t1, "counter", 100)
        wal.write(t2, "counter", 200)
        wal.write(t3, "counter", 300)

        # Commit in reverse order: t3, t2, t1
        wal.commit(t3)
        wal.commit(t2)
        wal.commit(t1)

        recovery = WALRecovery(wal.get_log())
        state = recovery.recover()

        # T1 committed last, so its value should be final
        assert state["counter"] == 100, (
            f"T1 committed last, its value 100 should win. Got {state['counter']}"
        )

    @pytest.mark.fail_to_pass
    def test_mixed_keys_commit_order(self):
        """Different keys written by transactions committing in non-start order."""
        wal = WriteAheadLog()

        t1 = wal.begin_transaction()
        t2 = wal.begin_transaction()

        wal.write(t1, "x", "old_x")
        wal.write(t2, "x", "new_x")
        wal.write(t2, "y", "y_by_t2")

        wal.commit(t2)  # T2 commits first

        wal.write(t1, "x", "final_x")  # T1 writes again after T2 committed
        wal.commit(t1)  # T1 commits second

        recovery = WALRecovery(wal.get_log())
        state = recovery.recover()

        assert state["x"] == "final_x", (
            f"T1 committed after T2, 'final_x' should win. Got '{state['x']}'"
        )
        assert state["y"] == "y_by_t2"

    @pytest.mark.fail_to_pass
    def test_store_crash_recovery_ordering(self):
        """WALKeyValueStore.crash_and_recover should respect commit order."""
        store = WALKeyValueStore()

        t1 = store.begin()
        t2 = store.begin()

        store.put(t1, "data", "first_write")
        store.put(t2, "data", "second_write")

        store.commit(t2)  # T2 commits first
        store.commit(t1)  # T1 commits second — should win

        pre_crash = store.get_state()
        assert pre_crash["data"] == "first_write", "Pre-crash state wrong"

        recovered = store.crash_and_recover()
        assert recovered["data"] == "first_write", (
            f"Recovery should match pre-crash state. "
            f"Pre-crash='first_write', recovered='{recovered['data']}'"
        )
