# Bug Report: Linked List Memory Growing Unbounded

## Summary
We're using the linked list library in a long-running service. Over time, memory usage
grows continuously even though we're deleting nodes and destroying lists regularly.
Valgrind shows "definitely lost" bytes after a create/insert/delete/destroy cycle.

## Steps to Reproduce
1. Create a list
2. Insert several items with string data
3. Delete some items
4. Destroy the list
5. Check for memory leaks — they're there

## Expected Behavior
After destroying a list, ALL memory associated with it should be freed, including:
- Each node's duplicated string data
- Each node struct  
- The list struct itself

## Observed Behavior
Memory keeps growing. Our monitoring shows allocations that never get freed.
Something in delete and/or destroy isn't cleaning up properly.

## Impact
This is a production issue — the service OOMs after running for ~12 hours.
