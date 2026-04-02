# Bug Report: Messages Occasionally Arrive Out of Order

## Summary
Messages occasionally arrive out of order to subscribers. This happens more frequently under load. The publisher sends messages with sequence numbers 1, 2, 3, ... but subscribers sometimes receive them as 1, 3, 2 or similar.

## Steps to Reproduce
1. Set up a topic with one or more subscribers
2. Publish 100+ messages in rapid succession
3. Check the subscriber's received message order
4. Sequence numbers are not monotonically increasing

## Expected Behavior
Messages should arrive at each subscriber in the order they were published.

## Additional Notes
- Works fine in low-throughput scenarios
- The broker dispatches to subscribers in parallel threads for performance
- Could be a thread scheduling issue?
- We considered adding locks but weren't sure where
- The message sequence numbers are assigned correctly by the publisher
