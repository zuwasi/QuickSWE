# Task 042: Raft Consensus Premature Commit

## Description

A simplified Raft consensus implementation has a bug where the leader commits
log entries after receiving the first AppendEntries acknowledgment instead of
waiting for a majority (quorum) of the cluster to acknowledge.

## Bug

The `_try_advance_commit` method checks if `match_index >= N` for any single
follower instead of checking if a majority of nodes have `match_index >= N`.
This causes entries to be committed with just one follower's ACK in a 5-node
cluster (which requires 3 ACKs including the leader).

## Expected Behavior

An entry at index N should only be committed when a majority of all servers
(including the leader) have the entry in their log (match_index >= N).
