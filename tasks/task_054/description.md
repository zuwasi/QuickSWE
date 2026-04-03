# Bug Report: Producer-Consumer Queue Loses Items Under Interleaving

## Summary
Our producer-consumer queue drops items when multiple consumers try to pop
concurrently. The queue is designed to be used with a lock/signal mechanism,
but even when we simulate the interleaving of operations, items get lost or
consumers get invalid data.

## Steps to Reproduce
1. Set up a queue with capacity
2. Have multiple producers push items via callbacks
3. Have multiple consumers pop items via callbacks
4. Interleave the operations (simulating concurrent access)
5. Count the total items consumed — it doesn't match items produced

## Expected Behavior
- Every item pushed should be popped exactly once
- Pop on empty queue after signal should re-check and wait, not return garbage
- No items should be lost even under arbitrary interleaving

## Observed Behavior  
- Under specific interleaving patterns, consumers pop from an empty queue
  because they don't re-check the empty condition after being signaled
- The `queue_pop` function uses an `if` to check emptiness instead of `while`,
  so after a spurious wakeup (or signal consumed by another consumer), it
  proceeds to pop from an empty queue and returns garbage or underflows

## Technical Details
The queue uses a callback-based architecture where operations can be
interleaved by a scheduler. The pop operation checks if the queue is empty
once, sets a "waiting" flag, and when "signaled" proceeds without rechecking.
This is the classic spurious-wakeup bug pattern.
