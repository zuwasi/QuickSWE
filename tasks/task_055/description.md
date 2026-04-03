# Bug Report: BST Corrupted After Deleting Nodes

## Summary
Our binary search tree implementation produces incorrect results after certain
delete sequences. After deleting specific nodes, the in-order traversal is no
longer sorted, and some elements that should be in the tree become unfindable.

## Steps to Reproduce
1. Insert elements: 50, 30, 70, 20, 40, 60, 80, 35, 45, 75, 85
2. Delete node 70 (has two children: 60 and 80)
3. In-order traversal should be: 20 30 35 40 45 50 60 75 80 85
4. Try to find all remaining elements

## Observed Behavior
- After deleting 70, the in-order successor (75) replaces it correctly
- BUT 75's right child (if any) or the subtree gets lost
- Some elements become unfindable even though they should still be in the tree
- In-order traversal may show elements out of order

## Expected Behavior
Deleting a node with two children should:
1. Find in-order successor (leftmost node in right subtree)
2. Copy successor's value to the node being deleted
3. Delete the successor node, properly relinking its right child to its parent

## Impact
This breaks our sorted data structure. After a few deletes, the tree is corrupted
and lookups return wrong results.
