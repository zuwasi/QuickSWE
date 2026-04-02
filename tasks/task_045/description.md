# Refactoring: Convert Procedural ETL to Declarative Pipeline

## Summary

The current ETL (Extract, Transform, Load) implementation is a monolithic `extract_transform_load()` function in `src/etl.py` (~200 lines). It has hardcoded steps, nested loops, inline data cleaning, and is impossible to test individual stages. This needs to be refactored into a clean, declarative pipeline.

## Current State

- `src/etl.py`: One massive function `extract_transform_load(source, db, report_path)` that does everything inline — file reading, data parsing, cleaning, validation, transformation, DB insertion, and report generation.
- `src/database.py`: Mock database with `insert`, `query`, `count` methods.
- `src/file_io.py`: File reading utilities (CSV-like parsing).
- `src/report.py`: Report generation (builds summary text).

## Problems

1. Cannot test individual steps in isolation.
2. Cannot reorder or skip steps.
3. Cannot add new steps without modifying the monolith.
4. Error in one step crashes the entire pipeline with no partial results.
5. No visibility into which step produced what output.

## Requirements

### Pipeline Architecture
1. Create a `Step` base class with `execute(data, context) -> data` method.
2. Create concrete step classes:
   - `ExtractStep` — reads from source using file_io
   - `CleanStep` — removes nulls, strips whitespace, normalizes types
   - `ValidateStep` — checks required fields, value ranges, data types
   - `TransformStep` — applies business transformations (compute derived fields)
   - `LoadStep` — inserts into database
   - `ReportStep` — generates summary report
3. Create `Pipeline` class that:
   - Takes a list of `Step` objects
   - Executes them in order, passing data through
   - Tracks step results in a `PipelineContext`
   - Handles errors per-step (records failure, continues or aborts based on config)
4. Create `PipelineContext` that stores:
   - Step results and timing
   - Error records
   - Configuration

### Backward Compatibility
- The end-to-end result (data extracted, cleaned, validated, transformed, loaded, reported) must match the current monolithic function's output for the same input.

## Acceptance Criteria
- Each step class is independently importable and testable.
- `Pipeline` is configurable via a list of steps.
- Pipeline produces the same end result as the monolith.
- Individual steps can be tested with mock data.
