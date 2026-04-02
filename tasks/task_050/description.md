# Refactoring: Convert Callback Hell to Clean Async Event Architecture

## Summary

The current data processing pipeline chains downloader → processor → uploader using deeply nested callbacks ("callback hell"). This needs to be refactored to use `async/await` with `asyncio` for a clean, flat, readable pipeline with proper error handling and cancellation support.

## Current State

- `src/downloader.py`: `Downloader` class that downloads URLs with nested callbacks (`on_start`, `on_progress`, `on_complete`, `on_save`).
- `src/processor.py`: `Processor` class that processes downloaded data with callbacks (`on_process_start`, `on_process_complete`, `on_error`).
- `src/uploader.py`: `Uploader` class that uploads results with callbacks (`on_upload_start`, `on_upload_complete`, `on_error`).
- `src/pipeline.py`: `Pipeline` class that chains all three with deeply nested callbacks (~100 lines of nested indentation) — classic callback hell.
- `src/logger.py`: Callback-based logging.

## Problems

1. Pipeline code is deeply nested and hard to read.
2. Error handling is scattered across multiple error callbacks.
3. No way to cancel an in-progress pipeline.
4. Testing requires complex callback wiring.
5. Adding a new stage requires more nesting.

## Requirements

### Async Refactoring
1. Convert `Downloader.download()` to `async def download(url) -> DownloadResult`.
2. Convert `Processor.process()` to `async def process(data) -> ProcessResult`.
3. Convert `Uploader.upload()` to `async def upload(data, destination) -> UploadResult`.
4. Convert `Pipeline.run()` to `async def run(url, destination) -> PipelineResult`.

### Pipeline (`src/pipeline.py`)
- Flat, readable flow: download → process → upload.
- Proper `try/except` error handling instead of error callbacks.
- Return a `PipelineResult` with status, data, and any errors.
- Support cancellation via `asyncio.Task.cancel()`.

### Logger (`src/logger.py`)
- Convert to async-compatible logging (can still be sync, but usable from async context).
- Log events: pipeline_start, download_start/complete, process_start/complete, upload_start/complete, pipeline_complete/error.

### Backward Compatibility
- Individual components (Downloader, Processor, Uploader) should still work independently.
- Their basic functionality (download data, process data, upload data) must produce correct results.

## Acceptance Criteria
- Pipeline is flat (`async def run` with sequential await calls).
- `asyncio.run(pipeline.run(...))` works.
- Cancellation raises `asyncio.CancelledError`.
- Errors in any stage propagate correctly.
- Individual components work for basic operations.
