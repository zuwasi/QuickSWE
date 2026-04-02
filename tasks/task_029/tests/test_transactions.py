"""Tests for transaction manager with savepoints."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.connection import Connection
from src.storage import Storage
from src.journal import Journal
from src.transaction import Transaction
from src.recovery import RecoveryManager


@pytest.mark.fail_to_pass
class TestSavepointRollbackDataLoss:
    """Tests that verify savepoint rollback doesn't lose parent transaction data.

    These tests FAIL because journal.truncate_to_savepoint removes ALL
    entries from the savepoint marker onward using positional truncation,
    instead of only removing entries tagged with that specific savepoint name.
    """

    def test_journal_truncation_only_removes_savepoint_entries(self):
        """truncate_to_savepoint should only remove entries belonging to that savepoint."""
        journal = Journal()

        # Simulate a transaction with interleaved entries
        journal.log_begin('txn1')
        journal.log_set('A', 1, transaction_id='txn1', savepoint_name=None)
        journal.log_savepoint('txn1', 'sp1')
        journal.log_set('B', 2, transaction_id='txn1', savepoint_name='sp1')
        journal.log_set('C', 3, transaction_id='txn1', savepoint_name=None)  # parent write after sp
        journal.log_set('D', 4, transaction_id='txn1', savepoint_name='sp1')

        # Before truncation: 6 entries (BEGIN, SET A, SAVEPOINT, SET B, SET C, SET D)
        assert journal.size == 6

        journal.truncate_to_savepoint('sp1')

        # After truncation: should keep BEGIN, SET A, and SET C (parent entries)
        # Should remove: SAVEPOINT marker, SET B (sp1), SET D (sp1)
        remaining_data = [e for e in journal.entries if e.is_data_entry()]
        remaining_keys = [e.key for e in remaining_data]

        assert 'A' in remaining_keys, "Parent entry A should be preserved"
        assert 'C' in remaining_keys, (
            f"Parent entry C was lost! truncate_to_savepoint removed entries "
            f"that don't belong to the savepoint. Remaining keys: {remaining_keys}"
        )
        assert 'B' not in remaining_keys, "Savepoint entry B should be removed"
        assert 'D' not in remaining_keys, "Savepoint entry D should be removed"

    def test_recovery_after_savepoint_rollback_and_commit(self):
        """After savepoint rollback + commit, recovery should see all surviving data."""
        storage = Storage()
        journal = Journal()
        txn = Transaction(storage, journal)
        txn.begin()

        # Write A in parent
        txn.set('A', 'alpha')

        # Create savepoint
        txn.savepoint('sp1')

        # Write B in savepoint
        txn.set('B', 'beta')

        # Now simulate a "parent scope" write that bypasses savepoint tagging.
        # This happens in real systems when a background task or trigger writes
        # to the same transaction without knowing about the savepoint.
        old_c = storage.get('C')
        storage.set('C', 'gamma')
        journal.log_set('C', 'gamma', old_value=old_c,
                        transaction_id=txn.id, savepoint_name=None)

        # Rollback savepoint — should undo B only, keep A and C
        txn.rollback_to_savepoint('sp1')

        # Storage should have A and C
        assert txn.get('A') == 'alpha'
        assert txn.get('B') is None, "B should be rolled back"
        assert txn.get('C') == 'gamma', "C should survive savepoint rollback"

        # Commit the transaction
        txn.commit()

        # Recovery: replay journal into fresh storage
        fresh = Storage()
        recovery = RecoveryManager(journal, fresh)
        recovery.recover()

        assert fresh.get('A') == 'alpha', "A missing after recovery!"
        assert fresh.get('C') == 'gamma', (
            "C missing after recovery! The journal lost C's entry "
            "during savepoint rollback truncation."
        )
        assert fresh.get('B') is None, "B should not appear after recovery"

    def test_parent_write_during_savepoint_survives_rollback(self):
        """A parent-scope write made while a savepoint is active should survive rollback."""
        storage = Storage()
        journal = Journal()
        txn = Transaction(storage, journal)
        txn.begin()

        # Write in parent before savepoint
        txn.set('pre', 'before')

        # Create savepoint
        txn.savepoint('sp1')

        # Write inside savepoint scope (tagged with sp1)
        txn.set('inner', 'discard_me')

        # Simulate a concurrent parent-scope write (background trigger, audit log, etc.)
        # This write is NOT part of the savepoint
        old = storage.get('audit')
        storage.set('audit', 'logged_event')
        journal.log_set('audit', 'logged_event', old_value=old,
                        transaction_id=txn.id, savepoint_name=None)

        # Also another savepoint-scoped write
        txn.set('inner2', 'also_discard')

        # Rollback savepoint — should undo inner and inner2, keep pre and audit
        txn.rollback_to_savepoint('sp1')

        assert txn.get('inner') is None, "inner should be rolled back"
        assert txn.get('inner2') is None, "inner2 should be rolled back"
        assert txn.get('pre') == 'before', "pre should survive"
        assert txn.get('audit') == 'logged_event', "audit should survive"

        # Commit and recover
        txn.commit()
        fresh = Storage()
        RecoveryManager(journal, fresh).recover()

        assert fresh.get('pre') == 'before', "pre lost after recovery!"
        assert fresh.get('audit') == 'logged_event', (
            "audit entry was lost! Parent-scope write during savepoint was "
            "removed by truncation during savepoint rollback."
        )
        assert fresh.get('inner') is None
        assert fresh.get('inner2') is None


class TestBasicTransactions:
    """Tests for basic transaction operations. Should always pass."""

    def test_begin_commit(self):
        conn = Connection()
        txn = conn.begin()
        txn.set('key1', 'val1')
        txn.commit()
        assert conn.get('key1') == 'val1'

    def test_begin_rollback(self):
        conn = Connection()
        conn.enable_auto_commit()
        conn.set('pre', 'existing')

        txn = conn.begin()
        txn.set('key1', 'val1')
        txn.rollback()

        assert conn.get('pre') == 'existing'
        assert conn.get('key1') is None

    def test_simple_savepoint_rollback(self):
        """Savepoint rollback with no parent writes after savepoint."""
        conn = Connection()
        txn = conn.begin()

        txn.set('A', 1)
        txn.savepoint('sp1')
        txn.set('B', 2)
        txn.rollback_to_savepoint('sp1')

        assert txn.get('A') == 1
        assert txn.get('B') is None

        txn.commit()
        assert conn.get('A') == 1
        assert conn.get('B') is None


class TestRecoveryWorks:
    """Tests for recovery manager. Should always pass."""

    def test_recovery_replays_committed_transactions(self):
        storage = Storage()
        journal = Journal()
        txn = Transaction(storage, journal)

        txn.begin()
        txn.set('recovered_key', 'recovered_value')
        txn.commit()

        # Clear storage and recover
        new_storage = Storage()
        recovery = RecoveryManager(journal, new_storage)
        recovery.recover()

        assert new_storage.get('recovered_key') == 'recovered_value'

    def test_recovery_skips_rolled_back_transactions(self):
        storage = Storage()
        journal = Journal()

        txn1 = Transaction(storage, journal)
        txn1.begin()
        txn1.set('keep', 'yes')
        txn1.commit()

        txn2 = Transaction(storage, journal)
        txn2.begin()
        txn2.set('discard', 'no')
        txn2.rollback()

        new_storage = Storage()
        recovery = RecoveryManager(journal, new_storage)
        recovery.recover()

        assert new_storage.get('keep') == 'yes'
        assert new_storage.get('discard') is None

    def test_verify_consistency(self):
        storage = Storage()
        journal = Journal()
        txn = Transaction(storage, journal)

        txn.begin()
        txn.set('a', 1)
        txn.commit()

        recovery = RecoveryManager(journal, Storage())
        recovery.recover()
        result = recovery.verify_consistency()
        assert result['consistent']
