# Bug Report: Data Loss After Savepoint Rollback

## Summary

We're experiencing data loss in our transaction manager. When using nested transactions (savepoints), rolling back an inner savepoint sometimes causes writes from the outer transaction to disappear too.

## Steps to Reproduce

1. Begin an outer transaction
2. Write some data (key "A")
3. Create a savepoint
4. Write data within the savepoint (key "B")
5. Also write more data in the outer transaction's scope (key "C") — this write happens after the savepoint was created but is NOT part of the inner transaction
6. Roll back the savepoint — should undo key "B" only
7. Commit the outer transaction
8. Key "C" is MISSING from storage

## Expected Behavior

Rolling back a savepoint should ONLY undo writes that were explicitly made within that savepoint's scope. Writes made in the parent transaction (even if they happened chronologically after the savepoint was created) should be preserved.

## Actual Behavior

Rolling back a savepoint seems to also remove writes that were made in the parent transaction after the savepoint was created. It's as if the rollback truncates ALL journal entries after the savepoint marker, not just the ones belonging to the savepoint.

## Additional Notes

- Basic transactions (without savepoints) work correctly
- Simple savepoint rollback (where no parent writes happen after the savepoint) also works
- The recovery manager was recently refactored — not sure if that's related
- The journal module handles write-ahead logging and has a `truncate_to_savepoint` method that might be relevant
- We've confirmed the data IS written to the journal before rollback happens
