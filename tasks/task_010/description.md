# Task 010: Cron Expression Parser — Day-of-Week Bug

## Problem

The `CronExpression` class parses standard 5-field cron expressions and computes the next run time. The day-of-week field uses `0=Monday` internally, but **standard cron uses `0=Sunday`**. This causes the parser to return incorrect next-run times for any expression that specifies a day of the week.

## Expected Behavior

- In standard cron: 0=Sunday, 1=Monday, 2=Tuesday, ..., 6=Saturday
- `"0 9 * * 0"` means "every Sunday at 9:00"
- `"0 9 * * 5"` means "every Friday at 9:00"
- The minute, hour, day-of-month, and month fields should continue to work correctly

## Files

- `src/cron_parser.py` — CronExpression implementation
- `tests/test_cron_parser.py` — Test suite
