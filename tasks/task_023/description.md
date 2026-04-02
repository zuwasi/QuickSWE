# Task 023: Extract Plugin Architecture from Monolithic Processor

## Current State

`src/processor.py` contains a `DataProcessor` class that does everything in one big class. It has a `process(data)` method that runs a fixed pipeline:

1. **Validate** — checks data structure and types
2. **Transform** — normalizes, converts, reshapes data
3. **Enrich** — adds computed fields, lookups
4. **Filter** — removes records that don't meet criteria
5. **Aggregate** — computes summaries and totals

Each step has hardcoded if/elif logic for different data types (lists of dicts, raw dicts, strings, etc). Adding a new processing step means editing the class itself. It's turning into a maintenance nightmare.

## Requested Refactoring

Pull out a proper plugin system:

- A `PluginBase` abstract class (or protocol) that defines what a processing plugin looks like — at minimum it needs a `name` property and a `process(data, context)` method
- A `PluginRegistry` that can register plugins and look them up
- `DataProcessor` should be refactored to use the registry — discover plugins, run them in order, pass data through

The key insight is that someone should be able to write a new plugin (say, a "deduplicate" step) without ever touching `DataProcessor`. Just register it and it runs.

The existing five steps (validate, transform, enrich, filter, aggregate) should become plugins, and the overall output for the same input data must not change.

## Constraints

- The existing `process()` method must return the same results for the same inputs
- Plugins should have an `order` or `priority` to control execution sequence
- Each plugin should be independently testable
- Context dict should be passed through the chain so plugins can share state

## Acceptance Criteria

- [ ] `PluginBase` is importable from `src.processor` with abstract `name` and `process(data, context)`
- [ ] `PluginRegistry` is importable from `src.processor` with `register(plugin)` and `get_plugins()`
- [ ] Custom plugins can be registered and execute in order
- [ ] DataProcessor uses registry internally
- [ ] Same inputs produce same outputs as before
