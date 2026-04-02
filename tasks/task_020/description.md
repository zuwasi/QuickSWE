# Bug Report: Memory usage grows over time when creating/destroying metric collectors

## Summary

Our monitoring system uses an observer pattern — `DataSource` objects are observable, and `MetricsCollector` instances attach to them to collect metrics. Collectors are created and destroyed as dashboards are opened and closed.

## Problem

Memory usage steadily increases over the lifetime of the application. After profiling, it appears that `MetricsCollector` instances are never garbage collected even after all references to them are removed. The observer list in `DataSource` keeps growing indefinitely.

In production, after ~24 hours, memory usage doubles. Restarting the service temporarily fixes it, but the leak resumes.

## Steps to Reproduce

1. Create a `DataSource`
2. Create a `MetricsCollector`, attach it to the data source
3. Delete all references to the collector
4. Observe that the data source's observer count does not decrease
5. Repeat steps 2-4 many times and watch memory grow

## Expected Behavior

When a `MetricsCollector` is deleted (no more references), the `DataSource` should automatically stop holding references to it, and the observer count should decrease. Dead observers should be cleaned up, not accumulate forever.

## Environment

- Python 3.10+
- Long-running service with dynamic observer registration
