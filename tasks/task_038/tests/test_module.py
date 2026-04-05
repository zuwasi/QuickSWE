import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.transaction import TransactionManager, IsolationLevel, Table


class TestBasicTransactions:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_read_committed_sees_committed(self):
        tm = TransactionManager()
        t1 = tm.begin(IsolationLevel.READ_COMMITTED)
        tm.write(t1, "x", 10)
        tm.commit(t1)

        t2 = tm.begin(IsolationLevel.READ_COMMITTED)
        assert tm.read(t2, "x") == 10
        tm.commit(t2)

    @pytest.mark.pass_to_pass
    def test_repeatable_read_snapshot(self):
        tm = TransactionManager()
        t1 = tm.begin(IsolationLevel.REPEATABLE_READ)
        tm.write(t1, "x", 1)
        tm.commit(t1)

        t2 = tm.begin(IsolationLevel.REPEATABLE_READ)
        assert tm.read(t2, "x") == 1

        t3 = tm.begin(IsolationLevel.REPEATABLE_READ)
        tm.write(t3, "x", 2)
        tm.commit(t3)

        assert tm.read(t2, "x") == 1
        tm.commit(t2)

    @pytest.mark.pass_to_pass
    def test_rollback(self):
        tm = TransactionManager()
        t1 = tm.begin()
        tm.write(t1, "x", 100)
        tm.rollback(t1)

        t2 = tm.begin()
        assert tm.read(t2, "x") is None
        tm.commit(t2)


class TestSerializablePhantoms:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_phantom_read_via_scan(self):
        """SERIALIZABLE should prevent phantom reads from new inserts."""
        tm = TransactionManager()
        table = Table("users", tm)

        t_setup = tm.begin()
        table.insert(t_setup, {"name": "Alice", "age": 30})
        table.insert(t_setup, {"name": "Bob", "age": 25})
        tm.commit(t_setup)

        t_serial = tm.begin(IsolationLevel.SERIALIZABLE)
        rows_first = table.scan_all(t_serial)
        assert len(rows_first) == 2

        t_other = tm.begin(IsolationLevel.READ_COMMITTED)
        table.insert(t_other, {"name": "Charlie", "age": 35})
        tm.commit(t_other)

        rows_second = table.scan_all(t_serial)
        assert len(rows_second) == 2, (
            f"SERIALIZABLE txn saw phantom row: got {len(rows_second)} rows, expected 2"
        )
        tm.commit(t_serial)

    @pytest.mark.fail_to_pass
    def test_phantom_read_via_predicate_scan(self):
        """SERIALIZABLE scan with predicate should not see new matching rows."""
        tm = TransactionManager()

        t_setup = tm.begin()
        tm.write(t_setup, "order:1", {"amount": 100, "status": "pending"})
        tm.write(t_setup, "order:2", {"amount": 200, "status": "completed"})
        tm.commit(t_setup)

        t_serial = tm.begin(IsolationLevel.SERIALIZABLE)
        pending = tm.scan(t_serial, prefix="order:",
                          predicate=lambda k, v: v["status"] == "pending")
        assert len(pending) == 1

        t_insert = tm.begin()
        tm.write(t_insert, "order:3", {"amount": 150, "status": "pending"})
        tm.commit(t_insert)

        pending_again = tm.scan(t_serial, prefix="order:",
                                predicate=lambda k, v: v["status"] == "pending")
        assert len(pending_again) == 1, (
            f"SERIALIZABLE predicate scan saw phantom: got {len(pending_again)}, expected 1"
        )
        tm.commit(t_serial)

    @pytest.mark.fail_to_pass
    def test_phantom_delete_not_visible(self):
        """SERIALIZABLE should not see deletes from concurrent transactions."""
        tm = TransactionManager()

        t_setup = tm.begin()
        tm.write(t_setup, "item:a", 1)
        tm.write(t_setup, "item:b", 2)
        tm.write(t_setup, "item:c", 3)
        tm.commit(t_setup)

        t_serial = tm.begin(IsolationLevel.SERIALIZABLE)
        items_first = tm.scan(t_serial, prefix="item:")
        assert len(items_first) == 3

        t_del = tm.begin()
        tm.delete(t_del, "item:b")
        tm.commit(t_del)

        items_second = tm.scan(t_serial, prefix="item:")
        assert len(items_second) == 3, (
            f"SERIALIZABLE saw concurrent delete: got {len(items_second)}, expected 3"
        )
        tm.commit(t_serial)

    @pytest.mark.fail_to_pass
    def test_serializable_commit_conflict_on_phantom(self):
        """SERIALIZABLE txn that scanned a range should conflict if range was modified."""
        tm = TransactionManager()

        t_setup = tm.begin()
        tm.write(t_setup, "data:1", "a")
        tm.commit(t_setup)

        t1 = tm.begin(IsolationLevel.SERIALIZABLE)
        results = tm.scan(t1, prefix="data:")
        assert len(results) == 1

        t2 = tm.begin()
        tm.write(t2, "data:2", "b")
        tm.commit(t2)

        results2 = tm.scan(t1, prefix="data:")
        assert len(results2) == 1, "Should not see phantom"
        tm.commit(t1)
