# Bug Report: Calendar Shows Conflicts Between Non-Overlapping Meetings

## Summary
The calendar system is reporting conflicts between meetings that shouldn't overlap. This primarily affects users in different timezones. For example, a meeting at 2pm EST and another at 2pm PST (which is actually 5pm EST) are shown as conflicting.

## Steps to Reproduce
1. Create an event at 2:00 PM US/Eastern
2. Create another event at 2:00 PM US/Pacific (3 hours behind)
3. Check for conflicts — the system reports them as overlapping
4. They should NOT conflict since 2PM PST = 5PM EST

## Expected Behavior
Events should be compared based on their actual UTC times, not their local times.

## Additional Notes
- Works correctly when all events are in the same timezone
- The event model stores timezone info, so the data is there
- We use `datetime` with `timezone` info — maybe the comparison isn't normalizing?
- The free slot finder also returns wrong results for cross-timezone queries
- Could be related to the recent scheduler refactor?
