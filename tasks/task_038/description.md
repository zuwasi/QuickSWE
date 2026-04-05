# Task 038: Transaction Engine Phantom Reads

## Description

A transaction manager supporting multiple isolation levels (READ_UNCOMMITTED,
READ_COMMITTED, REPEATABLE_READ, SERIALIZABLE) allows phantom reads under
SERIALIZABLE isolation. The engine uses MVCC (multi-version concurrency control)
but fails to implement predicate/range locks for SERIALIZABLE, so concurrent
transactions can insert new rows that become visible to a SERIALIZABLE transaction
re-executing the same range query.

## Bug

SERIALIZABLE isolation should prevent phantom reads by locking query predicates
(ranges). The current implementation only does snapshot isolation (same as
REPEATABLE_READ), allowing inserts by other committed transactions to appear
in subsequent reads within the same SERIALIZABLE transaction.

## Expected Behavior

Under SERIALIZABLE isolation, a transaction should see a consistent snapshot
that is not affected by concurrent inserts or deletes. Range queries should
return the same results throughout the transaction.
