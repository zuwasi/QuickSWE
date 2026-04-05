# Task 050: WAL Recovery Transaction Ordering Bug

## Description

A write-ahead log (WAL) implementation provides durability for a key-value store.
Transactions write operations to the log, and on crash recovery, committed
transactions are replayed from the log to reconstruct the database state.

## Bug

The recovery procedure replays committed transactions in the order they were
STARTED (by transaction ID) instead of the order they were COMMITTED. This violates
serializability: if T1 starts before T2 but commits after T2, replaying T1's writes
after T2's writes produces incorrect state (T1's stale writes overwrite T2's newer values).

## Expected Behavior

Recovery should replay committed transactions in COMMIT ORDER (the order their
commit records appear in the log), not in start/transaction-ID order.
