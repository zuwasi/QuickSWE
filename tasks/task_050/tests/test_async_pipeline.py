import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.downloader import Downloader, DownloadResult, DownloadError
from src.processor import Processor, ProcessResult, ProcessError
from src.uploader import Uploader, UploadResult, UploadError
from src.pipeline import Pipeline, PipelineResult
from src.logger import Logger, LogEntry


# ── pass-to-pass: basic sync component functionality ──────────────────


class TestDownloaderBasic:
    def test_download_sync(self):
        d = Downloader(delay=0)
        result = d.download_sync("http://example.com/data.csv")
        assert result.success
        assert "id,name,value" in result.data
        assert result.size > 0

    def test_download_sync_not_found(self):
        d = Downloader(delay=0)
        with pytest.raises(DownloadError, match="not found"):
            d.download_sync("http://example.com/nonexistent")

    def test_download_with_callbacks(self):
        d = Downloader(delay=0)
        results = []
        d.download("http://example.com/data.csv",
                    on_complete=lambda r: results.append(r))
        assert len(results) == 1
        assert results[0].success


class TestProcessorBasic:
    def test_process_sync(self):
        p = Processor(delay=0)
        result = p.process_sync("line1\nline2\nline3")
        assert result.success
        assert result.output_data["line_count"] == 3

    def test_process_sync_empty_raises(self):
        p = Processor(delay=0)
        with pytest.raises(ProcessError, match="empty"):
            p.process_sync("")


class TestUploaderBasic:
    def test_upload_sync(self):
        Uploader.clear_store()
        u = Uploader(delay=0)
        result = u.upload_sync({"key": "value"}, "test://dest1")
        assert result.success
        assert Uploader.get_uploaded("test://dest1") == {"key": "value"}

    def test_upload_sync_empty_raises(self):
        u = Uploader(delay=0)
        with pytest.raises(UploadError, match="empty"):
            u.upload_sync({}, "test://dest")


class TestLoggerBasic:
    def test_log_and_get(self):
        logger = Logger()
        logger.log("test_event", "test message")
        entries = logger.get_entries()
        assert len(entries) == 1
        assert entries[0].event == "test_event"

    def test_log_filtered(self):
        logger = Logger()
        logger.log("a", "msg1")
        logger.log("b", "msg2")
        logger.log("a", "msg3")
        assert len(logger.get_entries("a")) == 2

    def test_clear(self):
        logger = Logger()
        logger.log("x", "msg")
        logger.clear()
        assert logger.entry_count == 0


class TestSyncPipeline:
    """Current callback-based pipeline still works (pass-to-pass)."""

    def test_sync_pipeline_success(self):
        Uploader.clear_store()
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
        )
        result = pipeline.run("http://example.com/data.csv", "test://output")
        assert result.success
        assert result.download_result is not None
        assert result.process_result is not None
        assert result.upload_result is not None

    def test_sync_pipeline_download_error(self):
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
        )
        result = pipeline.run("http://example.com/nonexistent", "test://output")
        assert not result.success
        assert result.error is not None


# ── fail-to-pass: async pipeline implementation ──────────────────────


class TestAsyncDownloader:
    @pytest.mark.fail_to_pass
    def test_async_download(self):
        """Downloader should have an async download method."""
        d = Downloader(delay=0)

        async def run():
            result = await d.async_download("http://example.com/data.csv")
            return result

        result = asyncio.run(run())
        assert isinstance(result, DownloadResult)
        assert result.success
        assert "id,name,value" in result.data

    @pytest.mark.fail_to_pass
    def test_async_download_error(self):
        """Async download of missing URL should raise DownloadError."""
        d = Downloader(delay=0)

        async def run():
            return await d.async_download("http://example.com/nonexistent")

        with pytest.raises(DownloadError):
            asyncio.run(run())


class TestAsyncProcessor:
    @pytest.mark.fail_to_pass
    def test_async_process(self):
        """Processor should have an async process method."""
        p = Processor(delay=0)

        async def run():
            return await p.async_process("line1\nline2")

        result = asyncio.run(run())
        assert isinstance(result, ProcessResult)
        assert result.output_data["line_count"] == 2

    @pytest.mark.fail_to_pass
    def test_async_process_empty_raises(self):
        """Async process of empty data should raise ProcessError."""
        p = Processor(delay=0)

        async def run():
            return await p.async_process("")

        with pytest.raises(ProcessError):
            asyncio.run(run())


class TestAsyncUploader:
    @pytest.mark.fail_to_pass
    def test_async_upload(self):
        """Uploader should have an async upload method."""
        Uploader.clear_store()
        u = Uploader(delay=0)

        async def run():
            return await u.async_upload({"x": 1}, "async://dest1")

        result = asyncio.run(run())
        assert isinstance(result, UploadResult)
        assert result.success


class TestAsyncPipeline:
    @pytest.mark.fail_to_pass
    def test_async_pipeline_run(self):
        """Pipeline.async_run should work with asyncio.run()."""
        Uploader.clear_store()
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
        )

        async def run():
            return await pipeline.async_run(
                "http://example.com/data.csv", "async://pipeline_out"
            )

        result = asyncio.run(run())
        assert isinstance(result, PipelineResult)
        assert result.success
        assert result.download_result is not None
        assert result.process_result is not None
        assert result.upload_result is not None

    @pytest.mark.fail_to_pass
    def test_async_pipeline_download_error(self):
        """Pipeline should propagate download errors."""
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
        )

        async def run():
            return await pipeline.async_run(
                "http://example.com/nonexistent", "async://out"
            )

        result = asyncio.run(run())
        assert not result.success
        assert result.error is not None

    @pytest.mark.fail_to_pass
    def test_async_pipeline_upload_error(self):
        """Pipeline should propagate upload errors."""
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
        )

        async def run():
            return await pipeline.async_run(
                "http://example.com/data.csv", "error://fail_dest"
            )

        result = asyncio.run(run())
        assert not result.success
        assert result.error is not None

    @pytest.mark.fail_to_pass
    def test_async_pipeline_cancellation(self):
        """Pipeline should support cancellation via asyncio."""
        pipeline = Pipeline(
            downloader=Downloader(delay=0.5),
            processor=Processor(delay=0.5),
            uploader=Uploader(delay=0.5),
        )

        async def run():
            task = asyncio.create_task(
                pipeline.async_run("http://example.com/data.csv", "async://out")
            )
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                return "cancelled"
            return "not_cancelled"

        result = asyncio.run(run())
        assert result == "cancelled"

    @pytest.mark.fail_to_pass
    def test_async_pipeline_logs_events(self):
        """Async pipeline should log events."""
        Uploader.clear_store()
        logger = Logger()
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
            logger=logger,
        )

        async def run():
            return await pipeline.async_run(
                "http://example.com/data.csv", "async://log_test"
            )

        asyncio.run(run())
        events = [e.event for e in logger.get_entries()]
        assert "pipeline_start" in events
        assert "download_complete" in events
        assert "process_complete" in events
        assert "upload_complete" in events
        assert "pipeline_complete" in events

    @pytest.mark.fail_to_pass
    def test_async_pipeline_result_structure(self):
        """PipelineResult should have all fields populated on success."""
        Uploader.clear_store()
        pipeline = Pipeline(
            downloader=Downloader(delay=0),
            processor=Processor(delay=0),
            uploader=Uploader(delay=0),
        )

        async def run():
            return await pipeline.async_run(
                "http://example.com/users.json", "async://struct_test"
            )

        result = asyncio.run(run())
        assert result.success is True
        assert result.download_result.url == "http://example.com/users.json"
        assert result.process_result.output_data["line_count"] > 0
        assert result.upload_result.destination == "async://struct_test"
        assert result.error is None
